"""JWT-авторизация."""

from datetime import datetime, timedelta
from typing import Optional
import jwt

SECRET = "super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

users_db = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}


def create_access_token(username: str, password: str) -> Optional[str]:
    """Проверяет пароль и возвращает JWT-токен или None."""
    user = users_db.get(username)
    if not user or user["password"] != password:
        return None
    to_encode = {"sub": username, "role": user["role"]}
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)


def register_user(username: str, password: str) -> Optional[str]:
    """Регистрирует нового пользователя и возвращает токен."""
    if username in users_db:
        return None
    users_db[username] = {"password": password, "role": "user"}
    return create_access_token(username, password)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return {}
