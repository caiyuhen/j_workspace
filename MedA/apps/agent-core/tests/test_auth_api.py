from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.services.jwt_tokens import decode_token, get_secret


def test_dev_login_creates_session_and_returns_context() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "demo-hospital",
            "organization_name": "Demo Hospital",
            "user_id": "u-001",
            "display_name": "Dr. Chen",
            "role": "org_admin",
            "client_type": "web",
        },
    )

    body = response.json()

    assert response.status_code == 200
    # The token is a signed JWT now, so it must decode with our own key and
    # carry the session identity rather than being an opaque random string.
    claims = decode_token(body["token"])
    assert claims["sub"] == "u-001"
    assert claims["org"] == "demo-hospital"
    assert claims["role"] == "org_admin"
    assert claims["client_type"] == "web"
    assert claims["exp"] > claims["iat"]
    assert body["user"]["user_id"] == "u-001"
    assert body["user"]["display_name"] == "Dr. Chen"
    assert body["organization"]["slug"] == "demo-hospital"
    assert body["role"] == "org_admin"


def test_me_rejects_token_signed_with_another_secret() -> None:
    client = TestClient(app)
    forged = jwt.encode(
        {
            "sub": "u-001",
            "org": "demo-hospital",
            "role": "super_admin",
            "client_type": "web",
            "jti": "forged",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        },
        "not-the-real-secret",
        algorithm="HS256",
    )

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401, response.text


def test_me_rejects_expired_token() -> None:
    client = TestClient(app)
    issued_at = datetime.now(timezone.utc) - timedelta(hours=2)
    expired = jwt.encode(
        {
            "sub": "u-001",
            "org": "demo-hospital",
            "role": "org_admin",
            "client_type": "web",
            "jti": "expired",
            "iat": int(issued_at.timestamp()),
            "exp": int((issued_at + timedelta(seconds=1)).timestamp()),
        },
        get_secret(),
        algorithm="HS256",
    )

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401, response.text
    assert (response.json() or {}).get("detail") == "token expired"
