import mudpy
import jwt
import uuid
import pydantic
import phantasm
from datetime import datetime
from dataclasses import dataclass
from typing import Annotated, Optional
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

class UserModel(pydantic.BaseModel):
    id: uuid.UUID
    email: pydantic.EmailStr
    email_confirmed_at: Optional[datetime]
    display_name: Optional[str]
    admin_level: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

class CharacterModel(pydantic.BaseModel):
    id: int
    user_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserModel:
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
    
    with phantasm.PGPOOL.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    
    if user is None:
        raise credentials_exception
    
    return UserModel(**user)


@dataclass(slots=True)
class ActingAs:
    user: UserModel
    character: CharacterModel
    admin_level: int


async def get_acting_character(user: UserModel, character_id: int, admin_level: int) -> ActingAs:
    with phantasm.PGPOOL.acquire() as conn:
        character_data = await conn.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
    if character_data is None:
        raise HTTPException(status_code=404, detail="Character not found")
    character = CharacterModel(**character_data)
    if character.user_id != user.id:
        raise HTTPException(status_code=403, detail="Character does not belong to you.")
    acting_admin = min(admin_level, user.admin_level)
    return ActingAs(user=user, character=character, admin_level=acting_admin)
