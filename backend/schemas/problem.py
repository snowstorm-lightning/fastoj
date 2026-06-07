
from pydantic import BaseModel, ConfigDict


class SampleTestCase(BaseModel):
    input: str
    output: str
    explanation: str | None = None
    acm_input: str | None = None
    acm_output: str | None = None
    function_input: str | None = None
    function_output: str | None = None
    display_mode: str | None = None


class ProblemListItem(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str
    tags: list[str]
    total_submissions: int
    accepted_submissions: int
    ac_rate: float
    is_public: bool
    mode: str = "acm"
    function_signature: str | None = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ProblemDetail(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    difficulty: str
    tags: list[str]
    time_limit: int
    memory_limit: int
    hint: str | None
    mode: str = "acm"
    input_format: str | None = None
    output_format: str | None = None
    function_signature: str | None = None
    total_submissions: int
    accepted_submissions: int
    ac_rate: float
    sample_testcases: list[SampleTestCase]
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ProblemFilter(BaseModel):
    page: int = 1
    page_size: int = 20
    difficulty: str | None = None
    tags: str | None = None
    keyword: str | None = None
    sort: str = "created_at"
    order: str = "desc"
