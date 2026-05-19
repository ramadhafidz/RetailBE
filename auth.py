import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Konfigurasi: ambil dari env, dengan fallback untuk development lokal
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))

security = HTTPBearer()


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject, "role": role}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    user = {
        "username": payload.get("sub"),
        "role": payload.get("role", "user"),
    }
    return user


def require_role(*allowed_roles: str):
    def _dependency(user: dict = Depends(get_current_user)) -> dict:
        if allowed_roles and user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden for this role")
        return user

    return _dependency
