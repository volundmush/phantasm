import mudpy
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request

crypt_context = CryptContext(schemes=["argon2"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_real_ip(request: Request):
    """
    If the request is behind a trusted proxy, then we'll trust X-Forwarded-For and use the first IP in the list.
    trusted proxies are in mudpy.SETTINGS["GAME"]["networking"]["trusted_proxy_ips"]
    """
    ip = request.client.host
    if ip in mudpy.SETTINGS["GAME"]["networking"]["trusted_proxy_ips"]:
        ip = request.headers.get("X-Forwarded-For", ip).split(",")[0].strip()
    return ip