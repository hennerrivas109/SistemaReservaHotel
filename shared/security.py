from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        usuario_id = payload.get("usuario_id")
        if usuario_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


def create_access_token(payload: Dict[str, Any]) -> str:
    to_encode = payload.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(payload: Dict[str, Any]) -> str:
    to_encode = payload.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
