from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.message_feedback import MessageFeedback


client = TestClient(app)


def test_create_feedback():
    db = SessionLocal()

    try:
        response = client.post(
            "/api/v1/feedback",
            json={
                "message_id": 1,
                "user_id": 9,
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

        feedback = (
            db.query(MessageFeedback)
            .filter(MessageFeedback.id == data["id"])
            .first()
        )

        assert feedback is not None
        assert feedback.message_id == 1
        assert feedback.user_id == 9
        assert feedback.rating == "positive"
        assert feedback.comment == "Helpful response."

    finally:
        if "data" in locals() and "id" in data:
            db.query(MessageFeedback).filter(
                MessageFeedback.id == data["id"]
            ).delete()
            db.commit()

        db.close()
