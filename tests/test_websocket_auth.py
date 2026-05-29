import uuid

import pytest

from backend.api.websocket.judge import judge_status_websocket
from backend.models import User


class FakeWebSocket:
    def __init__(self):
        self.close_code = None

    async def close(self, code=None):
        self.close_code = code


class FakeQuery:
    def __init__(self, item):
        self.item = item

    def filter(self, *criteria):
        return self

    def first(self):
        return self.item


class FakeDb:
    def __init__(self, user):
        self.user = user

    def query(self, model):
        return FakeQuery(self.user if model is User else None)


@pytest.mark.asyncio
async def test_judge_websocket_rejects_disabled_user_token(monkeypatch):
    user = User(
        id=uuid.uuid4(),
        username="disabled",
        email="disabled@example.com",
        password_hash="hash",
        role="user",
        is_active=False,
    )
    monkeypatch.setattr(
        "backend.core.security.decode_token",
        lambda token: {"type": "access", "sub": str(user.id)},
    )
    websocket = FakeWebSocket()

    await judge_status_websocket(websocket, str(uuid.uuid4()), "token", FakeDb(user))

    assert websocket.close_code == 4003
