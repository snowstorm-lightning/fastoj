"""Repair the online least-squares logistics problem with Markdown and dual IO views."""

from __future__ import annotations

import uuid

from backend.core.database import SessionLocal
from backend.models import Difficulty, Problem, ProblemDraft, Solution, TestCase
from backend.schemas.problem_authoring import ProblemImportRequest
from backend.services.problem_authoring_agent import (
    ProblemAuthoringAgentService,
    dump_json,
    load_json,
)

RAW_MATERIAL = """
在线最小二乘回归

ADD x y
QUERY x0

样例 1
输入
8
ADD 10 35
ADD 20 55
QUERY 15
ADD 30 78
QUERY 25
ADD 25 69
QUERY 40
QUERY 5
输出
45.000000
66.750000
100.285714
23.685714
样例解释
前两条样本加入后，回归直线为 y = 2x + 15，所以 QUERY 15 输出 45.000000。加入更多样本后，回归参数会变化。

样例 2
输入
7
ADD 12 30
ADD 12 36
QUERY 12
ADD 12 45
QUERY 100
QUERY -20
QUERY 0
输出
33.000000
37.000000
37.000000
37.000000
样例解释
所有样本的 x 都等于 12，最小二乘解不唯一。按退化规则使用常数模型，预测值恒为当前所有 y 的平均值。
""".strip()

TARGET_TITLE = "智能物流定价引擎（在线学习）"
TARGET_SLUG_PREFIX = "smart-logistics-pricing-engine-online-least-squares-regression"


def main() -> None:
    db = SessionLocal()
    try:
        service = ProblemAuthoringAgentService(db)
        payload = ProblemImportRequest(
            raw_material=RAW_MATERIAL,
            topic=TARGET_TITLE,
            difficulty="hard",
            tags=["机器学习", "在线学习", "最小二乘回归", "数据流", "数学", "模拟"],
            mode="both",
            target_language="python",
            target_languages=["python", "cpp", "java"],
            locale="zh",
            model_profile="deepseek-pro",
        )
        authored = service._online_least_squares_import_candidate(payload)
        if authored is None:
            raise RuntimeError("Failed to build online least-squares repair draft")
        authored = service._prepare_authored_draft(authored, payload)
        testcases = service._testcases(authored)
        validation_report = service.validator.validate(authored, testcases, payload.requested_languages())
        if not validation_report.get("passed"):
            raise RuntimeError(f"Repair draft did not validate: {validation_report}")

        problems = (
            db.query(Problem)
            .filter((Problem.slug.ilike(f"{TARGET_SLUG_PREFIX}%")) | (Problem.title == TARGET_TITLE))
            .all()
        )
        drafts = (
            db.query(ProblemDraft)
            .filter((ProblemDraft.slug.ilike(f"{TARGET_SLUG_PREFIX}%")) | (ProblemDraft.title == TARGET_TITLE))
            .all()
        )
        for problem in problems:
            _repair_problem(db, problem, service, authored, testcases)
        for draft in drafts:
            _repair_draft(draft, service, authored, testcases, validation_report)
        db.commit()
        print(f"repaired {len(problems)} problem(s), {len(drafts)} draft(s)")
    finally:
        db.close()


def _repair_problem(db, problem: Problem, service: ProblemAuthoringAgentService, authored, testcases: list[dict]) -> None:
    problem.title = authored.title
    problem.description = authored.description
    problem.difficulty = Difficulty(authored.difficulty)
    problem.tags = authored.tags
    problem.hint = authored.hint
    problem.mode = authored.mode
    problem.input_format = authored.input_format
    problem.output_format = authored.output_format
    problem.function_signature = authored.function_signature
    problem.time_limit = authored.time_limit
    problem.memory_limit = authored.memory_limit

    db.query(TestCase).filter(TestCase.problem_id == problem.id).delete(synchronize_session=False)
    for index, testcase in enumerate(testcases, start=1):
        db.add(
            TestCase(
                id=uuid.uuid4(),
                problem_id=problem.id,
                input=str(testcase.get("input") or ""),
                output=str(testcase.get("output") or ""),
                io_metadata_json=dump_json(testcase.get("io_metadata")) if testcase.get("io_metadata") else None,
                is_hidden=bool(testcase.get("is_hidden")),
                is_sample=bool(testcase.get("is_sample")),
                score=10,
                order=index,
            )
        )

    existing = {str(solution.language): solution for solution in db.query(Solution).filter(Solution.problem_id == problem.id).all()}
    for solution in service._solutions(authored):
        record = existing.get(solution["language"])
        if record is None:
            record = Solution(
                id=uuid.uuid4(),
                problem_id=problem.id,
                language=solution["language"],
                is_official=True,
                created_by=problem.created_by,
            )
            db.add(record)
        record.code = solution["code"]
        record.explanation = solution["explanation"]
        record.time_complexity = authored.time_complexity
        record.space_complexity = authored.space_complexity


def _repair_draft(draft: ProblemDraft, service: ProblemAuthoringAgentService, authored, testcases: list[dict], validation_report: dict) -> None:
    metadata = load_json(draft.source_metadata_json, {})
    draft.title = authored.title
    draft.description = authored.description
    draft.difficulty = authored.difficulty
    draft.tags = dump_json(authored.tags)
    draft.mode = authored.mode
    draft.input_format = authored.input_format
    draft.output_format = authored.output_format
    draft.function_signature = authored.function_signature
    draft.time_limit = authored.time_limit
    draft.memory_limit = authored.memory_limit
    draft.hint = authored.hint
    draft.official_solution_language = authored.official_solution_language
    draft.official_solution_code = authored.official_solution_code
    draft.official_solution_explanation = authored.official_solution_explanation
    draft.official_solutions_json = dump_json(service._solutions(authored))
    draft.target_languages_json = dump_json(["python", "cpp", "java"])
    draft.time_complexity = authored.time_complexity
    draft.space_complexity = authored.space_complexity
    draft.testcases_json = dump_json(testcases)
    draft.validation_report_json = dump_json(validation_report)
    draft.source_metadata_json = dump_json({**metadata, "dual_mode_io_metadata": True})
    if draft.status != "approved":
        draft.status = "validated"


if __name__ == "__main__":
    main()
