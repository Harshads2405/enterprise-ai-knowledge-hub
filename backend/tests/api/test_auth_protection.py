
from fastapi.testclient import TestClient

from app.main import app


PROTECTED_REQUESTS = [
    ("post", "/api/v1/rag/query", {"question": "Test query"}),
    ("get", "/api/v1/documents", None),
    ("get", "/api/v1/documents/1", None),
    ("get", "/api/v1/conversations", None),
    ("post", "/api/v1/conversations", {"title": "Test conversation"}),
    ("post", "/api/v1/llm/chat", {"message": "Test message"}),
]


def test_protected_endpoints_reject_missing_bearer_token():
    with TestClient(app) as client:
        for method, path, payload in PROTECTED_REQUESTS:
            response = getattr(client, method)(
                path,
                json=payload,
            ) if payload is not None else getattr(client, method)(path)

            assert response.status_code == 401, (
                f"{method.upper()} {path} returned "
                f"{response.status_code}, expected 401"
            )


def test_protected_endpoints_reject_invalid_bearer_token():
    headers = {"Authorization": "Bearer invalid-token"}

    with TestClient(app) as client:
        for method, path, payload in PROTECTED_REQUESTS:
            response = getattr(client, method)(
                path,
                json=payload,
                headers=headers,
            ) if payload is not None else getattr(client, method)(
                path,
                headers=headers,
            )

            assert response.status_code == 401, (
                f"{method.upper()} {path} returned "
                f"{response.status_code}, expected 401"
            )
