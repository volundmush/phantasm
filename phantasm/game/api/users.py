from datetime import datetime, timedelta, timezone
from typing import Annotated

import mudpy
import jwt
import uuid

from tortoise.transactions import in_transaction

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from .utils import crypt_context, oauth2_scheme, get_real_ip, get_current_user
from ..models import auth, characters

router = APIRouter()

@router.get("/")
async def get_users(user: Annotated[auth.User, Depends(get_current_user)]):
    if user.admin_level < 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    return await auth.User_Pydantic_List.from_queryset(auth.User.all())

@router.get("/{user_id}")
async def get_user(user_id: uuid.UUID, user: Annotated[auth.User, Depends(get_current_user)]):
    if user.admin_level < 1 and user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    if not (u := await auth.User.filter(id=user_id).first()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return await auth.User_Pydantic.from_tortoise_orm(u)

@router.get("/{user_id}/characters")
async def get_user_characters(user_id: uuid.UUID, user: Annotated[auth.User, Depends(get_current_user)]):
    if user.id != user_id and user.admin_level < 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    if not (u := await auth.User.filter(id=user_id).first()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return await characters.Character_Pydantic_List.from_queryset(characters.Character.filter(user=u))