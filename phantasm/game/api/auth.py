from datetime import datetime, timedelta, timezone
from typing import Annotated

import mudpy
import jwt

from tortoise.transactions import in_transaction

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from .utils import crypt_context, oauth2_scheme, get_real_ip, get_current_user
from ..models import auth

router = APIRouter()

@router.post("/register")
async def register(data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    data.username = data.username.lower().strip()
    data.password = data.password.strip()

    if (found := await auth.User.filter(email=data.username).first()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists.")

    try:
        hashed = crypt_context.hash(data.password)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error hashing password.")

    async with in_transaction():
        user = await auth.User.create(email=data.username)
        pass_new = await auth.Passwords.create(user=user, password=hashed)

    return {"success": True}

def _create_token(user: auth.User, expires: datetime, refresh: bool = False):
    data = {
        "sub": str(user.id),
        "exp": expires,
        "iat": datetime.now(tz=timezone.utc),
    }
    if refresh:
        data["refresh"] = True
    jwt_settings = mudpy.SETTINGS["JWT"]
    return jwt.encode(data, jwt_settings["secret"], algorithm=jwt_settings["algorithm"])

def create_token(user: auth.User):
    jwt_settings = mudpy.SETTINGS["JWT"]
    return _create_token(user, datetime.now(tz=timezone.utc) + timedelta(minutes=jwt_settings["token_expire_minutes"]))

def create_refresh(user: auth.User):
    jwt_settings = mudpy.SETTINGS["JWT"]
    return _create_token(user, datetime.now(tz=timezone.utc) + timedelta(minutes=jwt_settings["refresh_expire_minutes"]), True)

@router.post("/login")
async def login(request: Request, data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    data.username = data.username.lower().strip()
    data.password = data.password.strip()

    if not (user := await auth.User.filter(email=data.username).first()):
        raise HTTPException(status_code=400, detail="Invalid credentials.")

    ip = get_real_ip(request)
    user_agent = request.headers.get("User-Agent", None)

    password = await auth.Passwords.filter(user=user).order_by("-created_at").first()

    if not (password and password.password and crypt_context.verify(data.password, password.password)):
        await auth.LoginRecord.create(user=user, ip_address=ip, success=False, user_agent=user_agent)
        raise HTTPException(status_code=400, detail="Invalid credentials.")

    await auth.LoginRecord.create(user=user, ip_address=ip, success=True, user_agent=user_agent)
    token = create_token(user)
    refresh = create_refresh(user)
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(ref: str):
    jwt_settings = mudpy.SETTINGS["JWT"]
    try:
        payload = jwt.decode(ref, jwt_settings["secret"], algorithms=[jwt_settings["algorithm"]])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
        # Get user identifier from token. For example:
    if not payload.get("refresh", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    if (sub := payload.get("sub", None)) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
    if not (user := await auth.User.filter(id=sub).first()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Create a new access token
    new_access_token = create_token(user)
    # Optionally, create a new refresh token
    new_refresh_token = create_refresh(user)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,  # if you want to rotate refresh tokens
        "token_type": "bearer"
    }


@router.get("/me")
async def read_users_me(current_user: Annotated[auth.User, Depends(get_current_user)]):
    return await auth.User_Pydantic.from_tortoise_orm(current_user)