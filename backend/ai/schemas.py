from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Verdict = Literal[
    "accepted",
    "wrong_answer",
    "time_limit",
    "memory_limit",
    "compile_error",
    "runtime_error",
    "system_error",
    "unknown",
]
AIModelProfile = Literal["default", "deepseek", "qwen-local"]
AILocale = Literal["zh", "en"]


class SuspiciousCodeRegion(BaseModel):
    line_start: int | None = None
    line_end: int | None = None
    reason: str


class PublicCaseAnalysis(BaseModel):
    case_index: int
    observation: str
    expected_summary: str
    actual_summary: str


class AIExplainResponse(BaseModel):
    summary: str
    verdict: Verdict
    likely_causes: list[str] = Field(default_factory=list)
    suspicious_code_regions: list[SuspiciousCodeRegion] = Field(default_factory=list)
    public_case_analysis: list[PublicCaseAnalysis] = Field(default_factory=list)
    minimal_fix_hint: str
    edge_cases_to_check: list[str] = Field(default_factory=list)
    complexity_comment: str
    next_action: str
    full_solution_revealed: bool = False


class AIReviewResponse(BaseModel):
    summary: str
    risks: list[str] = Field(default_factory=list)
    io_format_notes: list[str] = Field(default_factory=list)
    edge_cases_to_check: list[str] = Field(default_factory=list)
    complexity_comment: str
    suggested_next_action: str


class AIHintRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    level: Literal[1, 2, 3]
    language: str | None = None
    current_code: str | None = None
    model_profile: AIModelProfile = "default"
    locale: AILocale = "en"


class AIActionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_profile: AIModelProfile = "default"
    locale: AILocale = "en"


class AIChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    message: str = Field(min_length=1, max_length=2000)
    model_profile: AIModelProfile = "default"
    locale: AILocale = "en"


class AIChatResponse(BaseModel):
    message: str
    suggested_actions: list[str] = Field(default_factory=list)
    full_solution_revealed: bool = False


class AIHintResponse(BaseModel):
    level: Literal[1, 2, 3]
    hint: str
    focus: list[str] = Field(default_factory=list)
    full_solution_revealed: bool = False
