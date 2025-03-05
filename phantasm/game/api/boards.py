from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel

import re
import typing
import mudpy
import jwt
import uuid

from tortoise.expressions import RawSQL
from tortoise.transactions import in_transaction

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from .utils import crypt_context, oauth2_scheme, get_real_ip, get_current_user, get_acting_character, ActingAs
from ..models import auth, characters, boards, factions

router = APIRouter()

RE_BOARD_ID = re.compile(r"^(?P<abbr>[a-zA-Z]+)?(?P<order>\d+)$")

class BoardCreate(BaseModel):
    name: str
    board_id: str

    class Config:
        from_attributes = True

@router.post("/", response_model=boards.Board_Pydantic)
async def create_board(board: BoardCreate, user: Annotated[auth.User, Depends(get_current_user)], character_id: int, admin_level: int = 0):
    acting = await get_acting_character(user, character_id, admin_level)
    if not (matched := RE_BOARD_ID.match(board.board_id)):
        raise HTTPException(status_code=400, detail="Invalid board ID format.")
    order = int(matched.group("order"))
    faction = None
    if (abbr := matched.group("abbr")):
        if not (faction := await factions.Faction.filter(abbreviation__iexact=abbr).first()):
            raise HTTPException(status_code=404, detail=f"Faction {board.board_id} not found.")
    if faction:
        if not await faction.access(acting, "bbadmin"):
            raise HTTPException(status_code=403, detail="You do not have permission to create boards in that faction.")
    else:
        if acting.admin_level < 4:
            raise HTTPException(status_code=403, detail="You do not have permission to create public boards.")
    fac_id = faction.id if faction else None
    if (exists := await boards.Board.filter(faction_id=fac_id, order=order).first()) is not None:
        raise HTTPException(status_code=409, detail=f"Board with order {order} already exists in faction {fac_id}.")
    if (exists := await boards.Board.filter(name__iexact=board.name).first()) is not None:
        raise HTTPException(status_code=409, detail=f"Board with name {board.name} already exists.")
    board = await boards.Board.create(faction_id=fac_id, order=order, name=board.name)
    return await boards.Board_Pydantic.from_tortoise_orm(board)

def annotated_boards():
    return boards.Board.annotate(board_id=RawSQL("COALESCE(faction.abbreviation, '') || order::text"))

def annotated_posts():
    return boards.Post.annotate(post_id=RawSQL("order::text || sub_order::text"))

@router.get("/", response_model=boards.Board_Pydantic_List)
async def list_boards(user: Annotated[auth.User, Depends(get_current_user)], character_id: int, admin_level: int = 0):
    acting = await get_acting_character(user, character_id, admin_level)
    good_ids = []
    for board in await boards.Board.all():
        if await board.access(acting, "read"):
            good_ids.append(board.id)
    return await boards.Board_Pydantic_List.from_queryset(annotated_boards().filter(id__in=good_ids))


@router.get("/{board_id}", response_model=boards.Board_Pydantic)
async def get_board(board_id: str, user: Annotated[auth.User, Depends(get_current_user)], character_id: int, admin_level: int = 0):
    acting = await get_acting_character(user, character_id, admin_level)
    board = await annotated_boards().filter(board_id__iexact=board_id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found.")
    if not await board.access(acting, "read"):
        raise HTTPException(status_code=403, detail="You do not have permission to read this board.")
    return await boards.Board_Pydantic.from_tortoise_orm(board)

class PostData(BaseModel):
    post_id: str
    title: str
    body: str
    created_at: datetime
    modified_at: datetime
    poster_name: str
    character_id: typing.Optional[int] = None
    character_name: typing.Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_board_post(cls, board: boards.Board, post: boards.Post, admin: bool):
        poster_name = None
        character_name = None
        character_id= None
        if board.anonymous_name:
            poster_name = board.anonymous_name
            if admin:
                character_name = post.poster.name
                character_id = post.poster.id
        else:
            poster_name = post.poster.name
            character_name = post.poster.name
            character_id= post.poster.id
        return cls(
            post_id=post.post_id,
            title=post.title,
            body=post.body,
            created_at=post.created_at,
            modified_at=post.modified_at,
            poster_name=poster_name,
            character_id=character_id,
            character_name=character_name,
        )

@router.get("/{board_id}/posts", response_model=list[PostData])
async def list_posts(board_id: str, user: Annotated[auth.User, Depends(get_current_user)], character_id: int, admin_level: int = 0):
    acting = await get_acting_character(user, character_id, admin_level)
    board = await annotated_boards().filter(board_id__iexact=board_id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found.")
    if not await board.access(acting, "read"):
        raise HTTPException(status_code=403, detail="You do not have permission to read this board.")
    admin = await board.access(acting, "admin")
    out_posts = list()

    async for post in boards.Post.filter(board=board).prefetch_related("poster"):
        out_posts.append(PostData.from_board_post(board, post, admin))

    return out_posts


@router.get("/{board_id}/posts/{post_id}", response_model=PostData)
async def get_post(board_id: str, post_id: str, user: Annotated[auth.User, Depends(get_current_user)], character_id: int, admin_level: int = 0):
    acting = await get_acting_character(user, character_id, admin_level)
    board = await annotated_boards().filter(board_id__iexact=board_id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found.")
    if not await board.access(acting, "read"):
        raise HTTPException(status_code=403, detail="You do not have permission to read this board.")
    admin = await board.access(acting, "admin")
    post = await annotated_posts().filter(board=board, post_id=post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    return PostData.from_board_post(board, post, admin)

class PostCreate(BaseModel):
    title: str
    body: str

    class Config:
        from_attributes = True

@router.post("/{board_id}/posts", response_model=PostData)
async def create_post(board_id: str, post: PostCreate, user: Annotated[auth.User, Depends(get_current_user)], character_id: int, admin_level: int = 0):
    acting = await get_acting_character(user, character_id, admin_level)
    board = await annotated_boards().filter(board_id__iexact=board_id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found.")
    if not await board.access(acting, "post"):
        raise HTTPException(status_code=403, detail="You do not have permission to write to this board.")
    post = await boards.Post.create(board=board, **post.dict(exclude_unset=True))
    admin = await board.access(acting, "admin")
    post_data = PostData.from_board_post(board, post, admin)
    return post_data

class ReplyCreate(BaseModel):
    body: str

    class Config:
        from_attributes = True

@router.post("/{board_id}/posts/{post_id}", response_model=PostData)
async def create_reply_post(board_id: str, post_id: str, reply: ReplyCreate, user: Annotated[auth.User, Depends(get_current_user)], character_id: int, admin_level: int = 0):
    acting = await get_acting_character(user, character_id, admin_level)
    board = await annotated_boards().filter(board_id__iexact=board_id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found.")
    if not await board.access(acting, "post"):
        raise HTTPException(status_code=403, detail="You do not have permission to write to this board.")
    post = await annotated_posts().filter(board=board, post_id=post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    sub_order = max([p.sub_order for p in await boards.Post.filter(board=board, order=post.order)]) + 1
    reply = await boards.Post.create(board=board, order=post.order, title=f"RE: {post.title}", sub_order=sub_order, **reply.model_dump(exclude_unset=True))
    admin = await board.access(acting, "admin")
    post_data = PostData.from_board_post(board, reply, admin)
    return post_data