import uuid
from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.api.admin import (
    CONTENT_PERMISSION_MANAGE_USERS,
    CONTENT_PERMISSION_MODERATE_DISCUSSIONS,
    CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS,
    ROLE_ADMIN,
    ROLE_CONTENT_ADMIN,
    ROLE_USER,
    AdminPasswordReset,
    AdminUserUpdate,
    content_admin_permissions,
    has_content_permission,
    require_admin,
    require_content_permission,
    reset_user_password,
    update_user,
)
from backend.core.security import verify_password
from backend.core.time import utc_now
from backend.models import User


class FakeQuery:
    def __init__(self, items: list[Any]):
        self.items = list(items)

    def filter(self, *criteria):
        for criterion in criteria:
            left = getattr(criterion, "left", None)
            right = getattr(criterion, "right", None)
            field_name = getattr(left, "name", None)
            value = getattr(right, "value", None)
            if field_name is None:
                continue
            if str(right) == "true":
                value = True
            elif str(right) == "false":
                value = False
            self.items = [item for item in self.items if str(getattr(item, field_name)) == str(value)]
        return self

    def first(self):
        return self.items[0] if self.items else None

    def count(self):
        return len(self.items)


class FakeSession:
    def __init__(self, users: list[User]):
        self.data = {User: users}
        self.committed = False

    def query(self, model):
        return FakeQuery(self.data.setdefault(model, []))

    def commit(self):
        self.committed = True

    def refresh(self, _user):
        pass


def _user(role: str = ROLE_USER, permissions: list[str] | None = None) -> User:
    return User(
        id=uuid.uuid4(),
        username=f"{role}-{uuid.uuid4().hex[:6]}",
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash="x",
        role=role,
        content_admin_permissions=permissions or [],
        is_active=True,
        created_at=utc_now(),
    )


def test_require_admin_remains_highest_admin_only():
    with pytest.raises(HTTPException) as exc_info:
        require_admin(_user(ROLE_CONTENT_ADMIN, [CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS]))

    assert exc_info.value.status_code == 403
    assert require_admin(_user(ROLE_ADMIN)).role == ROLE_ADMIN


def test_content_permission_helper_checks_role_and_configured_permission():
    admin = _user(ROLE_ADMIN)
    content_admin = _user(ROLE_CONTENT_ADMIN, [CONTENT_PERMISSION_MODERATE_DISCUSSIONS])
    user = _user(ROLE_USER, [CONTENT_PERMISSION_MODERATE_DISCUSSIONS])

    assert has_content_permission(admin, CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS) is True
    assert has_content_permission(content_admin, CONTENT_PERMISSION_MODERATE_DISCUSSIONS) is True
    assert has_content_permission(content_admin, CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS) is False
    assert has_content_permission(user, CONTENT_PERMISSION_MODERATE_DISCUSSIONS) is False

    dependency = require_content_permission(CONTENT_PERMISSION_MODERATE_DISCUSSIONS)
    assert dependency(content_admin) is content_admin
    with pytest.raises(HTTPException):
        dependency(user)


def test_highest_admin_can_configure_content_admin_permissions():
    target = _user(ROLE_USER)
    db = FakeSession([target])

    response = update_user(
        str(target.id),
        AdminUserUpdate(
            role=ROLE_CONTENT_ADMIN,
            content_admin_permissions=[
                CONTENT_PERMISSION_MODERATE_DISCUSSIONS,
                CONTENT_PERMISSION_MODERATE_DISCUSSIONS,
            ],
        ),
        db,
        _user(ROLE_ADMIN),
    )

    assert response == {"success": True}
    assert db.committed is True
    assert target.role == ROLE_CONTENT_ADMIN
    assert content_admin_permissions(target) == [CONTENT_PERMISSION_MODERATE_DISCUSSIONS]


def test_content_admin_permissions_require_content_admin_role():
    target = _user(ROLE_USER)
    db = FakeSession([target])

    with pytest.raises(HTTPException) as exc_info:
        update_user(
            str(target.id),
            AdminUserUpdate(role=ROLE_USER, content_admin_permissions=[CONTENT_PERMISSION_MODERATE_DISCUSSIONS]),
            db,
            _user(ROLE_ADMIN),
        )

    assert exc_info.value.status_code == 400
    assert target.role == ROLE_USER
    assert target.content_admin_permissions == []
    assert db.committed is False


def test_unknown_content_admin_permission_is_rejected():
    with pytest.raises(ValidationError):
        AdminUserUpdate(role=ROLE_CONTENT_ADMIN, content_admin_permissions=["delete_everything"])


def test_content_admin_cannot_disable_highest_admin():
    target = _user(ROLE_ADMIN)
    actor = _user(ROLE_CONTENT_ADMIN, [CONTENT_PERMISSION_MANAGE_USERS])
    db = FakeSession([target, actor])

    with pytest.raises(HTTPException) as exc_info:
        update_user(str(target.id), AdminUserUpdate(is_active=False), db, actor)

    assert exc_info.value.status_code == 403
    assert target.is_active is True
    assert db.committed is False


def test_content_admin_cannot_change_user_role_or_permissions():
    target = _user(ROLE_USER)
    actor = _user(ROLE_CONTENT_ADMIN, [CONTENT_PERMISSION_MANAGE_USERS])
    db = FakeSession([target, actor])

    with pytest.raises(HTTPException) as exc_info:
        update_user(str(target.id), AdminUserUpdate(role=ROLE_CONTENT_ADMIN), db, actor)

    assert exc_info.value.status_code == 403
    assert target.role == ROLE_USER
    assert db.committed is False


def test_content_admin_cannot_manage_elevated_accounts():
    target = _user(ROLE_CONTENT_ADMIN, [CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS])
    actor = _user(ROLE_CONTENT_ADMIN, [CONTENT_PERMISSION_MANAGE_USERS])
    db = FakeSession([target, actor])

    with pytest.raises(HTTPException) as exc_info:
        update_user(str(target.id), AdminUserUpdate(is_active=False), db, actor)

    assert exc_info.value.status_code == 403
    assert target.is_active is True
    assert db.committed is False


def test_admin_cannot_remove_last_active_admin():
    admin = _user(ROLE_ADMIN)
    db = FakeSession([admin])

    with pytest.raises(HTTPException) as exc_info:
        update_user(str(admin.id), AdminUserUpdate(is_active=False), db, admin)

    assert exc_info.value.status_code == 400
    assert admin.is_active is True
    assert db.committed is False


def test_admin_cannot_downgrade_self():
    admin = _user(ROLE_ADMIN)
    other_admin = _user(ROLE_ADMIN)
    db = FakeSession([admin, other_admin])

    with pytest.raises(HTTPException) as exc_info:
        update_user(str(admin.id), AdminUserUpdate(role=ROLE_USER), db, admin)

    assert exc_info.value.status_code == 400
    assert admin.role == ROLE_ADMIN
    assert db.committed is False


def test_admin_can_reset_user_password_and_invalidate_tokens():
    target = _user(ROLE_USER)
    target.password_hash = "old"
    target.token_version = 4
    db = FakeSession([target])

    response = reset_user_password(str(target.id), AdminPasswordReset(new_password="newpassword"), db, _user(ROLE_ADMIN))

    assert response == {"success": True}
    assert verify_password("newpassword", target.password_hash)
    assert target.token_version == 5
    assert db.committed is True


def test_admin_reset_password_rejects_self():
    admin = _user(ROLE_ADMIN)
    db = FakeSession([admin])

    with pytest.raises(HTTPException) as exc_info:
        reset_user_password(str(admin.id), AdminPasswordReset(new_password="newpassword"), db, admin)

    assert exc_info.value.status_code == 400
    assert db.committed is False


def test_content_admin_cannot_reset_user_password():
    target = _user(ROLE_USER)
    db = FakeSession([target])

    with pytest.raises(HTTPException) as exc_info:
        reset_user_password(
            str(target.id),
            AdminPasswordReset(new_password="newpassword"),
            db,
            _user(ROLE_CONTENT_ADMIN, [CONTENT_PERMISSION_MANAGE_USERS]),
        )

    assert exc_info.value.status_code == 403
    assert db.committed is False
