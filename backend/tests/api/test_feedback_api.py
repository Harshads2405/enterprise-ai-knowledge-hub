
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.conversation import Conversation
from app.models.message import Message


def test_create_feedback():
    current_user = SimpleNamespace(
        id=9,
        organization_id=3,
        is_active=True,
    )

    message = SimpleNamespace(id=1)

    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.first.return_value = message

    saved_feedback = SimpleNamespace(
        id=101,
        message_id=1,
        user_id=9,
        rating="positive",
        comment="Helpful response.",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )

    def fake_create_feedback(**kwargs):
        assert kwargs["user_id"] == current_user.id
        assert kwargs["message_id"] == message.id
        return saved_feedback

    from app.services.feedback_service import feedback_service

    original_create_feedback = feedback_service.create_feedback
    feedback_service.create_feedback = fake_create_feedback

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/feedback",
                json={
                    "message_id": 1,
                    "rating": "positive",
                    "comment": "Helpful response.",
                },
            )

        assert response.status_code == 200

        data = response.json()
        assert data["message_id"] == 1
        assert data["user_id"] == 9
        assert data["rating"] == "positive"
        assert data["comment"] == "Helpful response."

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        feedback_service.create_feedback = original_create_feedback


def test_create_feedback_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/feedback",
            json={
                "message_id": 1,
                "rating": "positive",
                "comment": "Helpful response.",
            },
        )

    assert response.status_code == 401
