
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RunTestCaseInput(BaseModel):
    input: str = Field(..., max_length=32768)
    expected_output: str | None = Field(default="", max_length=32768)


class SubmissionCreate(BaseModel):
    problem_id: str
    code: str = Field(..., max_length=65536)
    language: str
    judge_mode: Literal["acm", "function"] = "acm"
    run_testcases: list[RunTestCaseInput] | None = Field(default=None, max_length=8)


class SubmissionRun(BaseModel):
    problem_id: str
    code: str = Field(..., max_length=65536)
    language: str


class TestCaseResultResponse(BaseModel):
    id: str
    testcase_id: str | None = None
    status: str
    input: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None
    execute_time: int | None = None
    memory_used: int | None = None
    is_hidden: bool

    model_config = ConfigDict(from_attributes=True)


class SubmissionResponse(BaseModel):
    id: str
    problem_id: str
    user_id: str
    code: str
    language: str
    status: str
    result: str | None = None
    error_message: str | None = None
    execute_time: int | None = None
    memory_used: int | None = None
    score: int
    created_at: str
    finished_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionDetail(SubmissionResponse):
    testcase_results: list[TestCaseResultResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SubmissionListItem(BaseModel):
    id: str
    problem: dict
    language: str
    status: str
    result: str | None = None
    error_message: str | None = None
    score: int
    execute_time: int | None = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)
