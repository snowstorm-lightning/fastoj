
from pydantic import BaseModel, ConfigDict


class TestCaseBase(BaseModel):
    input: str
    output: str
    is_hidden: bool = False
    is_sample: bool = False


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseResponse(TestCaseBase):
    id: str
    problem_id: str

    model_config = ConfigDict(from_attributes=True)


class SampleTestCase(BaseModel):
    input: str
    output: str


class ProblemBase(BaseModel):
    title: str
    slug: str
    description: str
    difficulty: str
    time_limit: int = 1000
    memory_limit: int = 256
    tags: list[str] = []
    hint: str | None = None


class ProblemCreate(ProblemBase):
    pass


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


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
