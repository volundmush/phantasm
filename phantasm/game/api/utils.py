import mudpy
import jwt
from typing import Annotated
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request, Depends, HTTPException, status

crypt_context = CryptContext(schemes=["argon2"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

from ..models import auth

def get_real_ip(request: Request):
    """
    If the request is behind a trusted proxy, then we'll trust X-Forwarded-For and use the first IP in the list.
    trusted proxies are in mudpy.SETTINGS["GAME"]["networking"]["trusted_proxy_ips"]
    """
    ip = request.client.host
    if ip in mudpy.SETTINGS["GAME"]["networking"]["trusted_proxy_ips"]:
        ip = request.headers.get("X-Forwarded-For", ip).split(",")[0].strip()
    return ip


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
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