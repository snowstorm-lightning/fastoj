from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.ai.schemas import AILocale, AIModelProfile
from backend.core.code_normalization import normalize_source_code
from backend.core.languages import Language
from backend.core.locales import DEFAULT_LOCALE

ProblemMode = Literal["function", "acm", "both"]
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
    target_languages: list[str] | None = Field(default=None, max_length=7)
    locale: AILocale = DEFAULT_LOCALE
    model_profile: AIModelProfile = "default"
    constraints: str | None = Field(default=None, max_length=2000)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        return [tag.strip() for tag in value if tag.strip()]

    @field_validator("target_language")
    @classmethod
    def clean_target_language(cls, value: str) -> str:
        language = value.strip().lower() or "python"
        if not Language.is_supported(language):
            raise ValueError(f"Unsupported language: {language}")
        return language

    @field_validator("target_languages")
    @classmethod
    def clean_target_languages(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for item in value:
            language = item.strip().lower()
            if not language:
                continue
            if not Language.is_supported(language):
                raise ValueError(f"Unsupported language: {language}")
            if language not in cleaned:
                cleaned.append(language)
        return cleaned or None

    @model_validator(mode="after")
    def fill_target_languages(self) -> "ProblemAuthoringRequest":
        languages = list(self.target_languages or [])
        if self.target_language not in languages:
            languages.insert(0, self.target_language)
        if len(languages) > 7:
            raise ValueError("At most 7 target languages are supported")
        self.target_language = languages[0]
        self.target_languages = languages
        return self

    def requested_languages(self) -> list[str]:
        return list(self.target_languages or [self.target_language])


class AuthoredTestCase(BaseModel):
    input: str
    output: str
    explanation: str | None = None


class AuthoredOfficialSolution(BaseModel):
    language: str = Field(max_length=20)
    code: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

    @field_validator("language")
    @classmethod
    def clean_language(cls, value: str) -> str:
        language = value.strip().lower()
        if not Language.is_supported(language):
            raise ValueError(f"Unsupported language: {language}")
        return language

    @field_validator("code")
    @classmethod
    def clean_code(cls, value: str) -> str:
        return normalize_source_code(value)


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
    official_solution_code: str = ""
    official_solution_explanation: str = ""
    official_solutions: list[AuthoredOfficialSolution] = Field(default_factory=list, max_length=7)
    time_complexity: str
    space_complexity: str
    public_sample_testcases: list[AuthoredTestCase] = Field(default_factory=list)
    hidden_testcases: list[AuthoredTestCase] = Field(default_factory=list)
    validation_notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def hydrate_legacy_solution_fields(cls, data):
        if not isinstance(data, dict):
            return data
        values = dict(data)
        solutions = values.get("official_solutions")
        if isinstance(solutions, list) and solutions:
            first = solutions[0]
            if isinstance(first, dict):
                values.setdefault("official_solution_language", first.get("language") or "python")
                values.setdefault("official_solution_code", first.get("code") or "")
                values.setdefault("official_solution_explanation", first.get("explanation") or "")
        elif values.get("official_solution_code") is not None:
            values["official_solutions"] = [
                {
                    "language": values.get("official_solution_language") or "python",
                    "code": values.get("official_solution_code") or "",
                    "explanation": values.get("official_solution_explanation") or "",
                }
            ]
        return values

    @field_validator("official_solution_language")
    @classmethod
    def clean_primary_solution_language(cls, value: str) -> str:
        language = value.strip().lower() or "python"
        if not Language.is_supported(language):
            raise ValueError(f"Unsupported language: {language}")
        return language

    @model_validator(mode="after")
    def normalize_official_solutions(self) -> "AuthoredProblemDraft":
        solutions: list[AuthoredOfficialSolution] = []
        seen: set[str] = set()
        for solution in self.official_solutions:
            if solution.language in seen:
                continue
            solutions.append(solution)
            seen.add(solution.language)
        if not solutions and self.official_solution_code.strip():
            solutions.append(
                AuthoredOfficialSolution(
                    language=self.official_solution_language,
                    code=self.official_solution_code,
                    explanation=self.official_solution_explanation,
                )
            )
        if not solutions:
            raise ValueError("At least one official solution is required")
        primary = next(
            (solution for solution in solutions if solution.language == self.official_solution_language),
            solutions[0],
        )
        self.official_solution_language = primary.language
        self.official_solution_code = primary.code
        self.official_solution_explanation = primary.explanation
        self.official_solutions = solutions
        return self


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


class ProblemDraftTestCaseUpdate(BaseModel):
    input: str = ""
    output: str = ""
    explanation: str | None = None
    is_hidden: bool = False
    is_sample: bool = False
    order: int | None = Field(default=None, ge=1)


class ProblemDraftUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    difficulty: Literal["easy", "medium", "hard"] | None = None
    tags: list[str] | None = None
    mode: ProblemMode | None = None
    target_languages: list[str] | None = Field(default=None, max_length=7)
    input_format: str | None = None
    output_format: str | None = None
    function_signature: str | None = None
    time_limit: int | None = Field(default=None, ge=100, le=10000)
    memory_limit: int | None = Field(default=None, ge=16, le=2048)
    hint: str | None = None
    official_solution_language: str | None = Field(default=None, max_length=20)
    official_solution_code: str | None = None
    official_solution_explanation: str | None = None
    official_solutions: list[AuthoredOfficialSolution] | None = Field(default=None, max_length=7)
    time_complexity: str | None = Field(default=None, max_length=50)
    space_complexity: str | None = Field(default=None, max_length=50)
    testcases: list[ProblemDraftTestCaseUpdate] | None = None

    @field_validator("tags")
    @classmethod
    def clean_optional_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [tag.strip() for tag in value if tag.strip()]

    @field_validator("target_languages")
    @classmethod
    def clean_optional_target_languages(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for item in value:
            language = item.strip().lower()
            if not language:
                continue
            if not Language.is_supported(language):
                raise ValueError(f"Unsupported language: {language}")
            if language not in cleaned:
                cleaned.append(language)
        return cleaned or None


class ProblemDraftSolutionGenerateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    language: str = Field(max_length=20)
    locale: AILocale = DEFAULT_LOCALE
    model_profile: AIModelProfile = "default"
    draft: ProblemDraftUpdate | None = None

    @field_validator("language")
    @classmethod
    def clean_language(cls, value: str) -> str:
        language = value.strip().lower()
        if not Language.is_supported(language):
            raise ValueError(f"Unsupported language: {language}")
        return language


class ProblemDraftResponse(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    difficulty: str
    tags: list[str]
    mode: str
    target_languages: list[str] = Field(default_factory=list)
    input_format: str | None = None
    output_format: str | None = None
    function_signature: str | None = None
    time_limit: int
    memory_limit: int
    hint: str | None = None
    official_solution_language: str
    official_solution_code: str
    official_solution_explanation: str
    official_solutions: list[AuthoredOfficialSolution] = Field(default_factory=list)
    time_complexity: str | None = None
    space_complexity: str | None = None
    testcases: list[dict]
    validation_report: dict
    status: str
    created_by: str
    approved_problem_id: str | None = None
    created_at: str
    updated_at: str
    steps: list[AgentStepResponse] = Field(default_factory=list)
    runs: list[AgentRunResponse] = Field(default_factory=list)


class ProblemDraftListItem(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str
    tags: list[str]
    mode: str
    target_languages: list[str] = Field(default_factory=list)
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
