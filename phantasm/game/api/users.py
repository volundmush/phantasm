from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import typing
import mudpy
import jwt
import uuid
import phantasm
import pydantic

from pyantic import BaseModel, exceptions


from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from .utils import crypt_context, oauth2_scheme, get_real_ip, get_current_user, UserModel, CharacterModel


router = APIRouter()


@router.get("/", response_model=typing.List[UserModel])
async def get_users(user: Annotated[UserModel, Depends(get_current_user)]):
    if user.admin_level < 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    with phantasm.PGPOOL.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")
    
    return [UserModel(**u) for u in users]

@router.get("/{user_id}", response_model=UserModel)
async def get_user(user_id: uuid.UUID, user: Annotated[UserModel, Depends(get_current_user)]):
    if user.admin_level < 1 and user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    with phantasm.PGPOOL.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    return UserModel(**user)

@router.get("/{user_id}/characters")
async def get_user_characters(user_id: uuid.UUID, user: Annotated[UserModel, Depends(get_current_user)]):
    if user.id != user_id and user.admin_level < 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    if not (u := await auth.User.filter(id=user_id).first()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return await characters.Character_Pydantic_List.from_queryset(characters.Character.filter(user=u))