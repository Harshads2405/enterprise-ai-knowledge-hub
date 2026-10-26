
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError
from app.core.config import Settings, settings
from app.core.config import settings
from app.services.auth_service import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    password_context,
    verify_password,
)


def test_access_token_round_trip():
    token = create_access_token(123)
    assert decode_access_token(token) == 123


def test_invalid_token_is_rejected():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid-token")


def test_token_with_invalid_subject_is_rejected():
    token = jwt.encode(
        {
            "sub": "not-a-user-id",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_password_hash_verification():
    password = "Temporary-Test-Password-123!"
    hashed = password_context.hash(password)

    assert verify_password(password, hashed)
    assert not verify_password("Wrong-Password-123!", hashed)


def test_malformed_password_hash_is_rejected():
    assert not verify_password("any-password", "test")

def test_settings_reject_short_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(
            database_url="sqlite:///./test.db",
            redis_url="redis://localhost:6379/0",
            groq_api_key="test-key",
            jwt_secret_key="short",
        )

def test_token_issued_in_the_future_is_rejected():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=10)

    token = jwt.encode(
        {
            "sub": "123",
            "iat": future_time,
            "exp": future_time + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)
