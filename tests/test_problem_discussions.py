import uuid
from typing import Any

from backend.api.problems import create_problem_discussion, get_problem_discussions
from backend.core.time import utc_now
from backend.models import Difficulty, Problem, ProblemDiscussion, User
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
            if field_name is None:
                continue
            self.items = [item for item in self.items if str(getattr(item, field_name)) == str(value)]
        return self

    def order_by(self, *_args):
        self.items = sorted(self.items, key=lambda item: item.created_at or utc_now(), reverse=True)
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
        }

    def query(self, model):
        return FakeQuery(self.data.setdefault(model, []))

    def add(self, item):
        self.data.setdefault(type(item), []).append(item)

    def commit(self):
        pass

    def refresh(self, item):
        if getattr(item, "created_at", None) is None:
            item.created_at = utc_now()


def test_problem_discussion_is_persisted_and_listed():
    user = User(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash="x",
        is_active=True,
    )
    problem = Problem(
        id=uuid.uuid4(),
        title="Discuss Me",
        slug="discuss-me",
        description="Temporary problem.",
        difficulty=Difficulty.EASY,
        mode="acm",
        is_public=True,
    )
    db = FakeSession(problem)

    created = create_problem_discussion(
        str(problem.id),
        ProblemDiscussionCreate(body="  shared idea  "),
        db,
        user,
    )
    listed = get_problem_discussions(str(problem.id), limit=50, db=db)

    assert created["data"]["body"] == "shared idea"
    assert created["data"]["author"] == "alice"
    assert len(db.data[ProblemDiscussion]) == 1
    assert listed["data"][0]["body"] == "shared idea"
