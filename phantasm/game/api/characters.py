from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel

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

@router.get("/characters", response_model=characters.Character_Pydantic_List)
async def get_characters(user: Annotated[auth.User, Depends(get_current_user)]):
    if not user.admin_level > 0:
        raise HTTPException(status_code=403, detail="You do not have permission to view all characters.")
    return await characters.Character.filter(user=user)

@router.get("/characters/{character_id}", response_model=characters.Character_Pydantic)
async def get_character(user: Annotated[auth.User, Depends(get_current_user)], character_id: int):
    character = await characters.Character.filter(id=character_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user != user and user.admin_level == 0:
        raise HTTPException(status_code=403, detail="Character does not belong to you.")
    return characters.Character_Pydantic.from_tortoise_orm(character)

class CharacterCreate(BaseModel):
    name: str

    class Config:
        from_attributes = True

@router.post("/characters", response_model=characters.Character_Pydantic)
async def create_character(user: Annotated[auth.User, Depends(get_current_user)], char_data: CharacterCreate):
    if (exists := await characters.Character.filter(name__iexact=char_data.name).exists()):
        raise HTTPException(status_code=400, detail="Character name already exists.")
    character = await characters.Character.create(user=user, name=char_data.name)
    return characters.Character_Pydantic.from_tortoise_orm(character)