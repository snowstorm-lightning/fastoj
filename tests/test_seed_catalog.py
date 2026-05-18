from backend.scripts.hot100_data import HOT100_CANONICAL_SLUGS, HOT100_LEGACY_SLUG_ALIASES
from backend.scripts.seed_data import PROBLEMS_DATA


def test_seed_catalog_contains_hot100_and_ai_practice_problems():
    slugs = [item["problem"]["slug"] for item in PROBLEMS_DATA]

    assert len(HOT100_CANONICAL_SLUGS) == 100
    assert len(set(HOT100_CANONICAL_SLUGS)) == 100
    assert set(HOT100_CANONICAL_SLUGS).issubset(slugs)
    assert len(slugs) == 106
    assert len(set(slugs)) == len(slugs)


def test_seed_catalog_uses_canonical_hot100_slug_for_longest_substring():
    slugs = {item["problem"]["slug"] for item in PROBLEMS_DATA}

    assert "longest-substring-without-repeating-characters" in slugs
    assert "longest-substring-without-repeating" not in slugs
    assert HOT100_LEGACY_SLUG_ALIASES["longest-substring-without-repeating-characters"] == [
        "longest-substring-without-repeating"
    ]
