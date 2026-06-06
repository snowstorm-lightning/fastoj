from backend.scripts.hot100_data import HOT100_CANONICAL_SLUGS, HOT100_LEGACY_SLUG_ALIASES
from backend.scripts.seed_data import PROBLEMS_DATA


def test_seed_catalog_contains_hot100_and_ai_practice_problems():
    slugs = [item["problem"]["slug"] for item in PROBLEMS_DATA]

    assert len(HOT100_CANONICAL_SLUGS) == 100
    assert len(set(HOT100_CANONICAL_SLUGS)) == 100
    assert set(HOT100_CANONICAL_SLUGS).issubset(slugs)
    assert len(slugs) == 106
    assert len(set(slugs)) == len(slugs)
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
