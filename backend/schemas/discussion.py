from pydantic import BaseModel, Field


class ProblemDiscussionCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class ProblemDiscussionResponse(BaseModel):
    id: str
    problem_id: str
    user_id: str
    author: str
    body: str
    created_at: str
    updated_at: str | None = None
