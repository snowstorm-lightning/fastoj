from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from backend.core.locales import DEFAULT_LOCALE, validate_locale

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
AIModelProfile = Literal["default", "deepseek", "deepseek-pro", "qwen-local"]
AILocale = Annotated[str, BeforeValidator(validate_locale)]


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
    locale: AILocale = DEFAULT_LOCALE


class AIActionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_profile: AIModelProfile = "default"
    locale: AILocale = DEFAULT_LOCALE


class AIChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    message: str = Field(min_length=1, max_length=2000)
    model_profile: AIModelProfile = "default"
    locale: AILocale = DEFAULT_LOCALE


class AIChatResponse(BaseModel):
    message: str
    suggested_actions: list[str] = Field(default_factory=list)
    full_solution_revealed: bool = False


class AIProfileResponse(BaseModel):
    value: AIModelProfile
    label_zh: str
    label_en: str
    detail_zh: str
    detail_en: str
    configured: bool
    available: bool
    reason: str | None = None
    checked_at: str | None = None


class AIHintResponse(BaseModel):
    level: Literal[1, 2, 3]
    hint: str
    focus: list[str] = Field(default_factory=list)
    full_solution_revealed: bool = False
