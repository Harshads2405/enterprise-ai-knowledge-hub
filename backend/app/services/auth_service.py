
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from passlib.exc import UnknownHashError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    try:
        return password_context.verify(plain_password, password_hash)
    except (ValueError, UnknownHashError):
        return False


def create_access_token(user_id: int) -> str:
    if not settings.jwt_secret_key or len(settings.jwt_secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters.")

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )



def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )

    issued_at = payload.get("iat")
    if not isinstance(issued_at, (int, float)):
        raise jwt.InvalidTokenError("Invalid token issued-at claim.")

    if issued_at > datetime.now(timezone.utc).timestamp():
        raise jwt.InvalidTokenError("Token was issued in the future.")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise jwt.InvalidTokenError("Invalid token subject.")

    user_id = int(subject)
    if user_id <= 0:
        raise jwt.InvalidTokenError("Invalid token subject.")

    return user_id
