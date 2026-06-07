from __future__ import annotations

from pydantic import BaseModel, Field


class ProblemDiscussionCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
    parent_id: str | None = None


class ProblemDiscussionResponse(BaseModel):
    id: str
    problem_id: str
    parent_id: str | None = None
    user_id: str
    author: str
    body: str
    deleted: bool = False
    is_deleted: bool = False
    is_template: bool = False
    deleted_at: str | None = None
    deleted_by: str | None = None
    like_count: int = 0
    liked_by_me: bool = False
    can_delete: bool = False
    reply_count: int = 0
    created_at: str
    updated_at: str | None = None
    replies: list[ProblemDiscussionResponse] = Field(default_factory=list)
