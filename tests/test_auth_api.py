from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.api.auth import (
    UserCreate,
    UserUpdate,
    get_current_user,
    get_me,
    login,
    register,
    update_me,
)
from backend.api.auth import (
    refresh_token as refresh_access_token,
)
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from backend.core.time import utc_now
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
        user.created_at = user.created_at or utc_now()


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
    assert decode_token(token.access_token)["token_version"] == 0


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


def test_get_current_user_rejects_disabled_user_token():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        is_active=False,
    )
    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    with pytest.raises(HTTPException) as exc:
        get_current_user(token, FakeAuthDb([user]))

    assert exc.value.status_code == 401


def test_get_current_user_accepts_legacy_token_until_password_changes():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
        token_version=0,
    )
    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    assert get_current_user(token, FakeAuthDb([user])).id == user.id

    user.token_version = 1
    with pytest.raises(HTTPException) as exc:
        get_current_user(token, FakeAuthDb([user]))
    assert exc.value.status_code == 401


def test_get_current_user_rejects_stale_token_version():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
        token_version=2,
    )
    token = create_access_token(data={"sub": str(user.id), "username": user.username, "token_version": 1})

    with pytest.raises(HTTPException) as exc:
        get_current_user(token, FakeAuthDb([user]))

    assert exc.value.status_code == 401


def test_refresh_rejects_stale_token_version():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
        token_version=3,
    )
    token = create_refresh_token(data={"sub": str(user.id), "username": user.username, "token_version": 2})

    with pytest.raises(HTTPException) as exc:
        refresh_access_token(token, FakeAuthDb([user]))

    assert exc.value.status_code == 401


def test_update_me_password_bumps_token_version_and_invalidates_old_token():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        locale="zh",
        is_active=True,
        token_version=0,
        created_at=utc_now(),
    )
    old_token = create_access_token(data={"sub": str(user.id), "username": user.username, "token_version": 0})

    update_me(UserUpdate(current_password="password123", new_password="newpassword"), FakeAuthDb([user]), user)

    assert user.token_version == 1
    assert verify_password("newpassword", user.password_hash)
    with pytest.raises(HTTPException) as exc:
        get_current_user(old_token, FakeAuthDb([user]))
    assert exc.value.status_code == 401


def test_update_me_persists_locale_preference():
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        locale="zh",
        is_active=True,
        created_at=utc_now(),
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
        created_at=utc_now(),
    )
    response = get_me(user)
    assert response.locale == "en"


def test_user_update_rejects_invalid_locale():
    with pytest.raises(ValidationError):
        UserUpdate(locale="fr")
