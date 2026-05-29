from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.api.auth import UserCreate, UserUpdate, get_me, login, register, update_me
from backend.core.security import get_password_hash
from backend.models import User


class FakeUserQuery:
    def __init__(self, users):
        self.users = users

    def filter(self, *_args):
        return self

    def first(self):
        return self.users[0] if self.users else None


class FakeAuthDb:
    def __init__(self, users=None):
        self.users = users or []

    def query(self, _model):
        return FakeUserQuery(self.users)

    def add(self, user):
        self.users.append(user)

    def commit(self):
        pass

    def refresh(self, user):
        user.id = user.id or uuid4()
        user.created_at = user.created_at or datetime.utcnow()


def test_register_success():
    db = FakeAuthDb()
    response = register(
        UserCreate(username="alice", email="alice@example.com", password="password123"),
        db,
    )
    assert response.username == "alice"
    assert response.locale == "zh"
    assert len(db.users) == 1


def test_register_accepts_locale_preference():
    db = FakeAuthDb()
    response = register(
        UserCreate(username="alice", email="alice@example.com", password="password123", locale="en"),
        db,
    )
    assert response.locale == "en"
    assert db.users[0].locale == "en"


def test_register_duplicate_username_or_email_fails():
    db = FakeAuthDb([User(username="alice", email="alice@example.com", password_hash="x")])
    with pytest.raises(HTTPException) as exc:
        register(UserCreate(username="alice", email="other@example.com", password="password123"), db)
    assert exc.value.status_code == 400


def test_login_success():
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    token = login(SimpleNamespace(username="alice", password="password123"), FakeAuthDb([user]))
    assert token.token_type == "bearer"
    assert token.access_token


def test_login_wrong_password_fails():
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    with pytest.raises(HTTPException) as exc:
        login(SimpleNamespace(username="alice", password="wrong"), FakeAuthDb([user]))
    assert exc.value.status_code == 401


def test_update_me_persists_locale_preference():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        locale="zh",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    response = update_me(UserUpdate(locale="en"), FakeAuthDb([user]), user)
    assert response.locale == "en"
    assert user.locale == "en"


def test_get_me_returns_locale_preference():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        locale="en",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    response = get_me(user)
    assert response.locale == "en"


def test_user_update_rejects_invalid_locale():
    with pytest.raises(ValidationError):
        UserUpdate(locale="fr")
