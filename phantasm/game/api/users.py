from datetime import datetime, timedelta, timezone
from typing import Annotated

import mudpy
import jwt

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
    users = await auth.User.all()

    return auth.User_Pydantic_List.from_queryset(users)

@router.get("/{user_id}")
async def get_user(user_id: int, user: Annotated[auth.User, Depends(get_current_user)]):
    if user.id == user_id:
        return auth.User_Pydantic.from_tortoise_orm(user)

    if user.admin_level < 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    
    user = await auth.User.filter(id=user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return auth.User_Pydantic.from_tortoise_orm(user)

@router.get("/{user_id}/characters")
async def get_user_characters(user_id: int, user: Annotated[auth.User, Depends(get_current_user)]):
    if user.id == user_id:
        characters = await user.characters
    else:
        if user.admin_level < 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        user = await auth.User.filter(id=user_id).prefetch_related("characters").first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        characters = user.characters

    return characters.Character_Pydantic_List.from_queryset(characters)