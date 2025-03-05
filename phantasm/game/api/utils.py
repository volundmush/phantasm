import mudpy
import jwt
from dataclasses import dataclass
from typing import Annotated
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request, Depends, HTTPException, status

crypt_context = CryptContext(schemes=["argon2"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

from ..models import auth, characters

def get_real_ip(request: Request):
    """
    If the request is behind a trusted proxy, then we'll trust X-Forwarded-For and use the first IP in the list.
    trusted proxies are in mudpy.SETTINGS["GAME"]["networking"]["trusted_proxy_ips"]
    """
    ip = request.client.host
    if ip in mudpy.SETTINGS["GAME"]["networking"]["trusted_proxy_ips"]:
        ip = request.headers.get("X-Forwarded-For", ip).split(",")[0].strip()
    return ip


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> auth.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    jwt_settings = mudpy.SETTINGS["JWT"]
    try:
        payload = jwt.decode(token, jwt_settings["secret"], algorithms=[jwt_settings["algorithm"]])
        if (user_id := payload.get("sub", None)) is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        raise credentials_exception
    user = await auth.User.filter(id=user_id).first()
    if user is None:
        raise credentials_exception
    return user


@dataclass(slots=True)
class ActingAs:
    user: auth.User
    character: characters.Character
    admin_level: int


async def get_acting_character(user: auth.User, character_id: int, admin_level: int) -> ActingAs:
    character = await characters.Character.filter(id=character_id).prefetch_related("user").first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user != user:
        raise HTTPException(status_code=403, detail="Character does not belong to you.")
    acting_admin = min(admin_level, user.admin_level)
    return ActingAs(user=user, character=character, admin_level=acting_admin)
