from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.security import verify_password
from backend.models import User
from backend.scripts.create_admin import create_or_promote_admin, validate_admin_password


class FakeUserQuery:
    def __init__(self, users):
        self.users = users

    def filter(self, *_args):
        return self

    def all(self):
        return self.users


class FakeDb:
    def __init__(self, users=None):
        self.users = users or []
        self.committed = False

    def query(self, _model):
        return FakeUserQuery(self.users)

    def add(self, user):
        self.users.append(user)

    def commit(self):
        self.committed = True

    def refresh(self, user):
        user.id = user.id or uuid4()
        user.created_at = user.created_at or datetime.now(UTC)


def test_create_admin_user_hashes_password_and_sets_role():
    db = FakeDb()

    user, action = create_or_promote_admin(
        db,
        username="admin",
        email="admin@example.com",
        password="correct-horse-password",
    )

    assert action == "created"
    assert user.role == "admin"
    assert user.is_active is True
    assert verify_password("correct-horse-password", user.password_hash)
    assert db.committed is True


def test_promote_existing_user_without_resetting_password():
    user = User(
        id=uuid4(),
        username="ops",
        email="ops@example.com",
        password_hash="existing-hash",
        role="user",
        is_active=False,
    )
    db = FakeDb([user])

    promoted, action = create_or_promote_admin(
        db,
        username="ops",
        email="ops@example.com",
        password=None,
    )

    assert promoted is user
    assert action == "promoted"
    assert user.role == "admin"
    assert user.is_active is True
    assert user.password_hash == "existing-hash"


def test_admin_password_validation_rejects_short_password():
    with pytest.raises(ValueError, match="at least"):
        validate_admin_password("short")
