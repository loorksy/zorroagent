"""Credential encryption at rest. Keys never leave the server."""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _fernet() -> Fernet:
    key = get_settings().encryption_key.encode()
    digest = hashlib.sha256(key).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt secret") from exc


def hash_password(password: str) -> str:
    return pwd.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd.verify(password, hashed)


def create_token(sub: str) -> str:
    settings = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": sub, "exp": exp}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return str(payload.get("sub"))
    except JWTError:
        return None
