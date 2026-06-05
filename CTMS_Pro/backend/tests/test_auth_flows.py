import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import auth


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeDB:
    def __init__(self, execute_results):
        self.execute_results = list(execute_results)
        self.commits = 0

    async def execute(self, _query):
        if self.execute_results:
            return self.execute_results.pop(0)
        return FakeResult(None)

    async def commit(self):
        self.commits += 1

    def add(self, _obj):
        return None


def make_request():
    return SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={"user-agent": "pytest"},
    )


def test_login_success_returns_access_and_refresh_token(monkeypatch):
    user_id = uuid4()
    role_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        username="admin",
        email="admin@ctms-pro.com",
        full_name="管理员",
        role_id=role_id,
        is_superuser=True,
        mfa_enabled=False,
        is_active=True,
        locked_until=None,
        failed_attempts=0,
        hashed_password="hashed",
    )
    role = SimpleNamespace(code="SUPER_ADMIN", name="超级管理员", permissions=["*"])
    db = FakeDB([FakeResult(user), FakeResult(role), FakeResult(None)])

    async def fake_write_audit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(auth, "_write_audit", fake_write_audit)
    monkeypatch.setattr(auth, "verify_password", lambda plain, hashed: plain == "Admin@123")
    monkeypatch.setattr(auth, "create_access_token", lambda **_kwargs: "access-token")
    monkeypatch.setattr(auth, "create_refresh_token", lambda **_kwargs: "refresh-token")

    body = auth.LoginRequest(username="admin", password="Admin@123")
    response = asyncio.run(auth.login(request=make_request(), body=body, db=db))

    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    assert response.user["username"] == "admin"
    assert response.user["role"] == "SUPER_ADMIN"
    assert db.commits >= 1


def test_login_wrong_password_raises_401(monkeypatch):
    user = SimpleNamespace(
        id=uuid4(),
        username="admin",
        email="admin@ctms-pro.com",
        full_name="管理员",
        role_id=None,
        is_superuser=True,
        mfa_enabled=False,
        is_active=True,
        locked_until=None,
        failed_attempts=0,
        hashed_password="hashed",
    )
    db = FakeDB([FakeResult(user), FakeResult(None)])
    called = {"audit": 0}

    async def fake_write_audit(*_args, **_kwargs):
        called["audit"] += 1

    monkeypatch.setattr(auth, "_write_audit", fake_write_audit)
    monkeypatch.setattr(auth, "verify_password", lambda plain, hashed: False)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            auth.login(
                request=make_request(),
                body=auth.LoginRequest(username="admin", password="wrong"),
                db=db,
            )
        )

    assert exc.value.status_code == 401
    assert "密码错误" in exc.value.detail
    assert called["audit"] == 1
