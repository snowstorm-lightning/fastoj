from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.ai.schemas import AILocale, AIModelProfile

ProblemMode = Literal["function", "acm"]
ProblemDraftStatus = Literal[
    "draft",
    "validating",
    "validated",
    "validation_failed",
    "approved",
    "rejected",
]


class ProblemAuthoringRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    topic: str = Field(min_length=3, max_length=200)
    difficulty: Literal["easy", "medium", "hard"]
    tags: list[str] = Field(default_factory=list, max_length=10)
    mode: ProblemMode
    target_language: str = "python"
    locale: AILocale = "en"
    model_profile: AIModelProfile = "default"
    constraints: str | None = Field(default=None, max_length=2000)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        return [tag.strip() for tag in value if tag.strip()]


class AuthoredTestCase(BaseModel):
    input: str
    output: str
    explanation: str | None = None


class AuthoredProblemDraft(BaseModel):
    title: str
    slug_candidate: str
    description: str
    input_format: str | None = None
    output_format: str | None = None
    function_signature: str | None = None
    difficulty: Literal["easy", "medium", "hard"]
    tags: list[str] = Field(default_factory=list)
    mode: ProblemMode
    time_limit: int = Field(default=1000, ge=100, le=10000)
    memory_limit: int = Field(default=256, ge=16, le=2048)
    hint: str | None = None
    official_solution_language: str = "python"
    official_solution_code: str
    official_solution_explanation: str
    time_complexity: str
    space_complexity: str
    public_sample_testcases: list[AuthoredTestCase] = Field(default_factory=list)
    hidden_testcases: list[AuthoredTestCase] = Field(default_factory=list)
    validation_notes: str | None = None


class AgentStepResponse(BaseModel):
    id: str
    run_id: str
    step_index: int
    step_type: str
    tool_name: str | None = None
    input: dict
    output: dict
    status: str
    error_message: str | None = None
    created_at: str


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    run_type: str
    status: str
    input: dict
    output: dict
    error_message: str | None = None
    model_profile: str
    locale: str
    created_by: str
    draft_id: str | None = None
    created_at: str
    finished_at: str | None = None
    steps: list[AgentStepResponse] = Field(default_factory=list)


class ProblemDraftResponse(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    difficulty: str
    tags: list[str]
    mode: str
    input_format: str | None = None
    output_format: str | None = None
    function_signature: str | None = None
    time_limit: int
    memory_limit: int
    hint: str | None = None
    official_solution_language: str
    official_solution_code: str
    official_solution_explanation: str
    time_complexity: str | None = None
    space_complexity: str | None = None
    testcases: list[dict]
    validation_report: dict
    status: str
    created_by: str
    approved_problem_id: str | None = None
    created_at: str
    updated_at: str


class ProblemDraftListItem(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str
    tags: list[str]
    mode: str
    status: str
    validation_summary: dict
    approved_problem_id: str | None = None
    created_at: str
    updated_at: str


class ProblemAuthoringCreateResponse(BaseModel):
    draft_id: str
    run_id: str
    status: str
    validation_summary: dict
    steps: list[AgentStepResponse]
