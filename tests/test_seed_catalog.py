import io
import re
import sys
from contextlib import redirect_stdout

from backend.scripts.hot100_data import HOT100_CANONICAL_SLUGS, HOT100_LEGACY_SLUG_ALIASES
from backend.scripts.seed_data import PROBLEMS_DATA, _expanded_testcases
from backend.scripts.seed_explanations import (
    SEED_EXPLANATIONS,
    sample_explanation_for_slug,
    solution_explanation_for_slug,
)
from backend.scripts.seed_official_solutions import (
    OFFICIAL_PYTHON_SOLUTIONS,
    official_solution_for_slug,
)
from backend.scripts.seed_testcase_augmentation import (
    hidden_minimum_for_slug,
    public_minimum_for_slug,
)
from backend.services.function_mode import wrap_function_submission
from backend.services.problem_modes import FUNCTION_SIGNATURES
from backend.worker.tasks.judge_task import _outputs_match


def test_seed_catalog_contains_hot100_ai_practice_and_extra_interview_problems():
    slugs = [item["problem"]["slug"] for item in PROBLEMS_DATA]

    assert len(HOT100_CANONICAL_SLUGS) == 100
    assert len(set(HOT100_CANONICAL_SLUGS)) == 100
    assert set(HOT100_CANONICAL_SLUGS).issubset(slugs)
    assert len(slugs) == 108
    assert len(set(slugs)) == len(slugs)
    assert "alien-dictionary" in slugs
    assert "two-car-parking-lot" in slugs
    assert "print-test" not in slugs
    assert "print-qiu-qiu" not in slugs


def test_seed_catalog_uses_canonical_hot100_slug_for_longest_substring():
    slugs = {item["problem"]["slug"] for item in PROBLEMS_DATA}

    assert "longest-substring-without-repeating-characters" in slugs
    assert "longest-substring-without-repeating" not in slugs
    assert HOT100_LEGACY_SLUG_ALIASES["longest-substring-without-repeating-characters"] == [
        "longest-substring-without-repeating"
    ]


def test_seed_catalog_descriptions_focus_on_problem_meaning_not_platform_contracts():
    banned_fragments = [
        "Function contract",
        "Parameter contract",
        "Return contract",
        "Judging and representation notes",
        "Edge cases to consider",
        "JSON-line",
        "hidden tests",
        "function signature",
        "stdin",
        "stdout",
    ]

    for item in PROBLEMS_DATA:
        problem = item["problem"]
        description = problem["description"]

        assert problem["mode"] == "function"
        assert problem["function_signature"] not in description
        assert len(description.split("\n\n")) >= 2
        for fragment in banned_fragments:
            assert fragment.lower() not in description.lower()


def test_seed_catalog_describes_problem_semantics_for_representative_tasks():
    by_slug = {item["problem"]["slug"]: item["problem"]["description"] for item in PROBLEMS_DATA}

    min_path_sum = by_slug["minimum-path-sum"]
    assert "top-left" in min_path_sum
    assert "bottom-right" in min_path_sum
    assert "cost" in min_path_sum
    assert "smallest" in min_path_sum

    lru_cache = by_slug["lru-cache"]
    assert "least recently used" in lru_cache
    assert "most recently used" in lru_cache

    parking_lot = by_slug["two-car-parking-lot"]
    assert "A must finish on a" in parking_lot
    assert "B must finish on b" in parking_lot
    assert "current cell" in parking_lot


def test_seed_catalog_has_python_official_solution_for_every_problem():
    slugs = {item["problem"]["slug"] for item in PROBLEMS_DATA}

    assert slugs == set(OFFICIAL_PYTHON_SOLUTIONS)


def test_seed_official_solutions_do_not_contain_placeholders():
    banned_fragments = [
        "TODO",
        "implement your solution",
        "add official solution",
    ]

    for slug, solution in OFFICIAL_PYTHON_SOLUTIONS.items():
        assert solution.code.strip()
        assert not re.search(r"\bpass\b", solution.code), slug
        for fragment in banned_fragments:
            assert fragment.lower() not in solution.code.lower(), slug


def test_seed_explanations_cover_every_problem_without_templates():
    slugs = {item["problem"]["slug"] for item in PROBLEMS_DATA}
    banned_fragments = [
        "standard optimal approach",
        "canonical expected answer",
        "TODO",
        "placeholder",
        "按相同输入/输出格式比较",
    ]

    assert slugs == set(SEED_EXPLANATIONS)

    for item in PROBLEMS_DATA:
        slug = item["problem"]["slug"]
        zh_solution = solution_explanation_for_slug(slug, "zh")
        en_solution = solution_explanation_for_slug(slug, "en")
        assert zh_solution and re.search(r"[\u4e00-\u9fff]", zh_solution), slug
        assert en_solution and zh_solution != en_solution, slug

        cases = _expanded_testcases(item)
        public_cases = [testcase for testcase in cases if not testcase["is_hidden"]]
        assert len(public_cases) >= public_minimum_for_slug(slug), slug
        for index, testcase in enumerate(public_cases):
            zh_sample = sample_explanation_for_slug(slug, index, testcase["input"], testcase["output"], "zh")
            en_sample = sample_explanation_for_slug(slug, index, testcase["input"], testcase["output"], "en")
            assert zh_sample and re.search(r"[\u4e00-\u9fff]", zh_sample), slug
            assert en_sample and zh_sample != en_sample, slug
            for fragment in banned_fragments:
                assert fragment.lower() not in zh_sample.lower(), slug
                assert fragment.lower() not in en_sample.lower(), slug
                assert fragment.lower() not in zh_solution.lower(), slug
                assert fragment.lower() not in en_solution.lower(), slug


def test_seed_testcase_counts_follow_policy():
    for item in PROBLEMS_DATA:
        slug = item["problem"]["slug"]
        cases = _expanded_testcases(item)
        public_count = sum(not testcase["is_hidden"] for testcase in cases)
        hidden_count = sum(testcase["is_hidden"] for testcase in cases)

        assert public_count >= public_minimum_for_slug(slug), slug
        assert hidden_count >= hidden_minimum_for_slug(slug), slug


def test_seed_function_testcases_have_acm_and_function_views():
    for item in PROBLEMS_DATA:
        if item["problem"]["slug"] not in FUNCTION_SIGNATURES:
            continue
        for index, testcase in enumerate(_expanded_testcases(item)):
            metadata = testcase.get("io_metadata")
            assert isinstance(metadata, dict), item["problem"]["slug"]
            assert "function" in metadata, (item["problem"]["slug"], index)
            assert "acm" in metadata, (item["problem"]["slug"], index)
            function_view = metadata["function"]
            acm_view = metadata["acm"]
            assert isinstance(function_view, dict), (item["problem"]["slug"], index)
            assert isinstance(acm_view, dict), (item["problem"]["slug"], index)
            assert function_view.get("input") is not None, (item["problem"]["slug"], index)
            assert function_view.get("output") is not None, (item["problem"]["slug"], index)
            assert acm_view.get("input") is not None, (item["problem"]["slug"], index)
            assert acm_view.get("output") is not None, (item["problem"]["slug"], index)


def test_seed_python_official_solutions_pass_all_seed_cases():
    for item in PROBLEMS_DATA:
        slug = item["problem"]["slug"]
        solution = official_solution_for_slug(slug)
        assert solution is not None
        wrapped = wrap_function_submission(
            solution.code,
            "python",
            slug,
            item["problem"].get("function_signature"),
        )

        for testcase in _expanded_testcases(item):
            old_stdin = sys.stdin
            output = io.StringIO()
            try:
                sys.stdin = io.StringIO(testcase["input"])
                with redirect_stdout(output):
                    exec(wrapped, {"__name__": "__main__"})
            finally:
                sys.stdin = old_stdin

            assert _outputs_match(output.getvalue().strip(), testcase["output"]), (
                slug,
                testcase["input"],
                testcase["output"],
                output.getvalue().strip(),
            )
