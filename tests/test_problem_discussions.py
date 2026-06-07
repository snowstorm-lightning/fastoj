import uuid
from typing import Any

import pytest
from fastapi import HTTPException

from backend.api.admin import CONTENT_PERMISSION_MODERATE_DISCUSSIONS
from backend.api.problems import (
    create_problem_discussion,
    delete_problem_discussion,
    get_problem_discussions,
    like_problem_discussion,
    unlike_problem_discussion,
)
from backend.core.time import utc_now
from backend.models import Difficulty, Problem, ProblemDiscussion, ProblemDiscussionLike, User
from backend.schemas.discussion import ProblemDiscussionCreate


class FakeQuery:
    def __init__(self, items: list[Any]):
        self.items = list(items)

    def filter(self, *criteria):
        for criterion in criteria:
            left = getattr(criterion, "left", None)
            right = getattr(criterion, "right", None)
            field_name = getattr(left, "name", None)
            value = getattr(right, "value", None)
            operator_name = getattr(getattr(criterion, "operator", None), "__name__", "")
            if field_name is None:
                continue
            if operator_name == "in_op":
                values = {str(item) for item in value}
                self.items = [item for item in self.items if str(getattr(item, field_name)) in values]
            else:
                self.items = [item for item in self.items if str(getattr(item, field_name)) == str(value)]
        return self

    def order_by(self, *_args):
        reverse = bool(_args and "DESC" in str(_args[0]).upper())
        self.items = sorted(self.items, key=lambda item: item.created_at or utc_now(), reverse=reverse)
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items


class FakeSession:
    def __init__(self, problem: Problem):
        self.data: dict[type, list[Any]] = {
            Problem: [problem],
            ProblemDiscussion: [],
            ProblemDiscussionLike: [],
        }

    def query(self, model):
        return FakeQuery(self.data.setdefault(model, []))

    def add(self, item):
        if getattr(item, "created_at", None) is None:
            item.created_at = utc_now()
        if hasattr(item, "updated_at") and getattr(item, "updated_at", None) is None:
            item.updated_at = utc_now()
        self.data.setdefault(type(item), []).append(item)

    def commit(self):
        pass

    def rollback(self):
        pass

    def refresh(self, item):
        if getattr(item, "created_at", None) is None:
            item.created_at = utc_now()

    def delete(self, item):
        items = self.data.setdefault(type(item), [])
        if item in items:
            items.remove(item)


def _user(username: str, role: str = "user", permissions: list[str] | None = None) -> User:
    return User(
        id=uuid.uuid4(),
        username=username,
        email=f"{username}@example.com",
        password_hash="x",
        role=role,
        content_admin_permissions=permissions or [],
        is_active=True,
    )


def _problem() -> Problem:
    return Problem(
        id=uuid.uuid4(),
        title="Discuss Me",
        slug="discuss-me",
        description="Temporary problem.",
        difficulty=Difficulty.EASY,
        mode="acm",
        is_public=True,
    )


def test_problem_discussion_is_persisted_and_listed():
    user = _user("alice")
    problem = _problem()
    db = FakeSession(problem)

    created = create_problem_discussion(
        str(problem.id),
        ProblemDiscussionCreate(body="  shared idea  "),
        db,
        user,
    )
    listed = get_problem_discussions(str(problem.id), limit=50, db=db, current_user=user)

    assert created["data"]["body"] == "shared idea"
    assert created["data"]["author"] == "alice"
    assert len(db.data[ProblemDiscussion]) == 1
    assert listed["data"][0]["body"] == "shared idea"
    assert listed["data"][0]["replies"] == []
    assert listed["data"][0]["like_count"] == 0
    assert listed["data"][0]["liked_by_me"] is False
    assert listed["data"][0]["can_delete"] is True
    assert listed["data"][0]["deleted"] is False


def test_problem_discussions_are_returned_as_nested_tree_with_likes():
    alice = _user("alice")
    bob = _user("bob")
    problem = _problem()
    db = FakeSession(problem)

    root = create_problem_discussion(str(problem.id), ProblemDiscussionCreate(body="root"), db, alice)["data"]
    reply = create_problem_discussion(
        str(problem.id),
        ProblemDiscussionCreate(body="reply", parent_id=root["id"]),
        db,
        bob,
    )["data"]
    like_problem_discussion(str(problem.id), root["id"], db, bob)

    listed = get_problem_discussions(str(problem.id), limit=50, db=db, current_user=bob)

    assert len(listed["data"]) == 1
    root_data = listed["data"][0]
    assert root_data["id"] == root["id"]
    assert root_data["like_count"] == 1
    assert root_data["liked_by_me"] is True
    assert root_data["can_delete"] is False
    assert root_data["replies"][0]["id"] == reply["id"]
    assert root_data["replies"][0]["parent_id"] == root["id"]
    assert root_data["replies"][0]["can_delete"] is True


def test_discussion_likes_and_unlikes_are_idempotent():
    alice = _user("alice")
    bob = _user("bob")
    problem = _problem()
    db = FakeSession(problem)
    discussion = create_problem_discussion(str(problem.id), ProblemDiscussionCreate(body="root"), db, alice)["data"]

    first_like = like_problem_discussion(str(problem.id), discussion["id"], db, bob)
    second_like = like_problem_discussion(str(problem.id), discussion["id"], db, bob)
    first_unlike = unlike_problem_discussion(str(problem.id), discussion["id"], db, bob)
    second_unlike = unlike_problem_discussion(str(problem.id), discussion["id"], db, bob)

    assert first_like["data"] == {"liked": True, "like_count": 1}
    assert second_like["data"] == {"liked": True, "like_count": 1}
    assert first_unlike["data"] == {"liked": False, "like_count": 0}
    assert second_unlike["data"] == {"liked": False, "like_count": 0}
    assert db.data[ProblemDiscussionLike] == []


def test_user_can_soft_delete_own_discussion_without_removing_replies():
    alice = _user("alice")
    bob = _user("bob")
    problem = _problem()
    db = FakeSession(problem)
    root = create_problem_discussion(str(problem.id), ProblemDiscussionCreate(body="root"), db, alice)["data"]
    create_problem_discussion(
        str(problem.id),
        ProblemDiscussionCreate(body="reply", parent_id=root["id"]),
        db,
        bob,
    )

    deleted = delete_problem_discussion(str(problem.id), root["id"], db, alice)
    listed = get_problem_discussions(str(problem.id), limit=50, db=db, current_user=alice)

    assert deleted["data"]["deleted"] is True
    assert listed["data"][0]["deleted"] is True
    assert listed["data"][0]["body"] == ""
    assert listed["data"][0]["deleted_by"] == str(alice.id)
    assert len(listed["data"][0]["replies"]) == 1
    assert len(db.data[ProblemDiscussion]) == 2


def test_content_admin_permission_controls_moderator_delete():
    owner = _user("alice")
    moderator = _user("mod", role="content_admin", permissions=[CONTENT_PERMISSION_MODERATE_DISCUSSIONS])
    unprivileged = _user("viewer", role="content_admin", permissions=[])
    problem = _problem()
    db = FakeSession(problem)
    discussion = create_problem_discussion(str(problem.id), ProblemDiscussionCreate(body="root"), db, owner)["data"]

    with pytest.raises(HTTPException) as exc_info:
        delete_problem_discussion(str(problem.id), discussion["id"], db, unprivileged)
    assert exc_info.value.status_code == 403

    response = delete_problem_discussion(str(problem.id), discussion["id"], db, moderator)

    assert response["success"] is True
    assert response["data"]["deleted"] is True


def test_create_reply_rejects_parent_from_another_problem():
    alice = _user("alice")
    problem = _problem()
    other_problem = _problem()
    db = FakeSession(problem)
    parent = ProblemDiscussion(
        id=uuid.uuid4(),
        problem_id=other_problem.id,
        user_id=alice.id,
        user=alice,
        body="other",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.data[ProblemDiscussion].append(parent)

    with pytest.raises(HTTPException) as exc_info:
        create_problem_discussion(
            str(problem.id),
            ProblemDiscussionCreate(body="reply", parent_id=str(parent.id)),
            db,
            alice,
        )

    assert exc_info.value.status_code == 404
