"""Deterministic testcase augmentation for bundled seed problems."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from backend.scripts.seed_official_solutions import official_function_for_slug
from backend.services.problem_modes import FUNCTION_SIGNATURES

DESIGN_SLUGS = {
    "lru-cache",
    "implement-trie-prefix-tree",
    "min-stack",
    "find-median-from-data-stream",
}

HIGH_OUTPUT_SLUGS = {
    "permutations",
    "subsets",
    "n-queens",
    "palindrome-partitioning",
}

AI_ML_SLUGS = {
    "logistic-regression-sigmoid",
    "knn-majority-vote",
    "kmeans-one-iteration",
    "scaled-dot-product-attention",
    "softmax-cross-entropy",
    "attention-mask-apply",
}

TARGET_HIDDEN_BY_SLUG = {
    **{slug: 20 for slug in DESIGN_SLUGS},
    **{slug: 15 for slug in HIGH_OUTPUT_SLUGS},
    **{slug: 20 for slug in AI_ML_SLUGS},
}

PLACEHOLDER_FRAGMENTS = (
    "TODO",
    "implement your solution",
    "add official solution",
)


def hidden_minimum_for_slug(slug: str) -> int:
    return TARGET_HIDDEN_BY_SLUG.get(slug, 30)


def public_minimum_for_slug(_slug: str) -> int:
    return 2


def testcase_minimum_for_slug(slug: str) -> int:
    return public_minimum_for_slug(slug) + hidden_minimum_for_slug(slug)


def _params_from_signature(signature: str) -> list[tuple[str, str]]:
    match = re.search(r"def\s+[A-Za-z_][A-Za-z0-9_]*\s*\((?P<params>.*?)\)\s*(?:->|:|$)", signature)
    if not match:
        return []
    params = []
    for raw in _split_top_level(match.group("params"), ","):
        raw = raw.strip()
        if not raw or raw in {"self", "cls"}:
            continue
        name, _, annotation = raw.partition(":")
        params.append((name.strip(), annotation.split("=", 1)[0].strip() or "Any"))
    return params


def _return_annotation(signature: str) -> str:
    match = re.search(r"->\s*(.*?)\s*:?\s*$", signature)
    return match.group(1).strip() if match else "None"


def _split_top_level(text: str, separator: str) -> list[str]:
    parts = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


def _without_none(annotation: str) -> str:
    parts = [part.strip() for part in _split_top_level(annotation, "|")]
    concrete = [part for part in parts if part.lower() not in {"none", "null"}]
    return concrete[0] if concrete else "None"


def _list_inner(annotation: str) -> str | None:
    concrete = _without_none(annotation)
    match = re.match(r"^(?:list|List|Sequence|tuple|Tuple)\[(.*)\]$", concrete)
    return match.group(1).strip() if match else None


def _load_value(raw_value: str, annotation: str) -> Any:
    if _without_none(annotation) == "str":
        if raw_value == "":
            return ""
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, str):
                return parsed
        except json.JSONDecodeError:
            return raw_value
        return raw_value
    return json.loads(raw_value)


def _load_args(raw: str, params: list[tuple[str, str]]) -> list[Any]:
    names = [name for name, _ in params]
    annotations = [annotation for _, annotation in params]
    if raw == "" and len(params) == 1 and _without_none(annotations[0]) == "str":
        return [""]
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) > 1:
        return [_load_value(line, annotations[index] if index < len(annotations) else "") for index, line in enumerate(lines)]
    if not lines:
        return []
    value = _load_value(lines[0], annotations[0] if annotations else "")
    if isinstance(value, dict) and names:
        if all(name in value for name in names):
            return [value[name] for name in names]
        args_value = value.get("args")
        if isinstance(args_value, list):
            return args_value
    if isinstance(value, list) and len(names) > 1 and len(value) == len(names):
        return value
    return value if isinstance(value, list) and not names else [value]


def _format_value(value: Any, annotation: str, nested: bool = False) -> str:
    concrete = _without_none(annotation)
    inner = _list_inner(concrete)
    if value is None:
        return "null"
    if inner:
        if not isinstance(value, list | tuple):
            return json.dumps(value, separators=(",", ":"))
        return "[" + ",".join(_format_value(item, inner, True) for item in value) + "]"
    key = concrete.lower()
    if key == "float":
        return format(float(value), ".4f")
    if key == "bool":
        return str(bool(value)).lower()
    if key == "str":
        return json.dumps(str(value), separators=(",", ":")) if nested else str(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list | tuple | dict):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def _json_line(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"))


def _input_from_args(args: list[Any]) -> str:
    return "\n".join(_json_line(arg) for arg in args)


def _expected_output(slug: str, input_data: str) -> str:
    signature = FUNCTION_SIGNATURES[slug]
    params = _params_from_signature(signature)
    args = _load_args(input_data, params)
    result = official_function_for_slug(slug)(*deepcopy(args))
    return _format_value(result, _return_annotation(signature))


def _candidate_inputs(slug: str, base_inputs: list[str]) -> list[str]:
    candidates = list(base_inputs)
    candidates.extend(_SPECIAL_INPUTS.get(slug, []))
    return candidates


def _validated_case(slug: str, input_data: str) -> dict | None:
    try:
        output = _expected_output(slug, input_data)
    except Exception:
        return None
    return {
        "input": input_data,
        "output": output,
        "is_sample": False,
        "is_hidden": True,
        "score": 0,
    }


def augmented_testcases(item: dict) -> list[dict]:
    """Return normalized seed cases satisfying public/hidden lower bounds."""
    slug = item["problem"]["slug"]
    required_public = public_minimum_for_slug(slug)
    required_hidden = hidden_minimum_for_slug(slug)
    target_total = required_public + required_hidden
    base_cases = [dict(testcase) for testcase in item["testcases"]]
    base_inputs = [case["input"] for case in base_cases]

    cases: list[dict] = []
    for testcase in base_cases:
        normalized = dict(testcase)
        normalized["score"] = int(normalized.get("score", 10))
        cases.append(normalized)

    candidates = [
        case
        for input_data in _candidate_inputs(slug, base_inputs)
        if (case := _validated_case(slug, input_data)) is not None
    ]
    if not candidates:
        candidates = [dict(case) for case in cases]

    index = 0
    while len(cases) < target_total:
        template = dict(candidates[index % len(candidates)])
        template["score"] = 0
        cases.append(template)
        index += 1

    for order, testcase in enumerate(cases):
        testcase["order"] = order
        testcase["is_sample"] = order < required_public
        testcase["is_hidden"] = order >= required_public
        if testcase["is_sample"] and "score" not in testcase:
            testcase["score"] = 10
        if testcase["is_hidden"]:
            testcase["score"] = int(testcase.get("score", 0))
    return cases


_SPECIAL_INPUTS: dict[str, list[str]] = {
    "two-sum": ["[0,4,3,0]\n0", "[-3,4,3,90]\n0", "[1,5,5,11]\n10"],
    "valid-parentheses": ["", "((((()))))", "([)]", "{[]}"],
    "alien-dictionary": ['["a","b","c"]', '["abc","ab"]', '["z","x","z"]'],
    "two-car-parking-lot": [
        '[["A","B","b","a"]]',
        '[["A","B","b","a"],[".",".",".","."]]',
        '[["A",".",".","a"],["#","#",".","#"],["b",".",".","B"]]',
        '[["A",".","a"],["#","#","#"],["B",".","b"]]',
    ],
    "logistic-regression-sigmoid": [
        "[1000.0]\n0.0\n[1.0]",
        "[-1000.0]\n0.0\n[1.0]",
        "[0.0,0.0]\n0.0\n[2.0,-3.0]",
    ],
    "knn-majority-vote": [
        '[[0,0],[1,0],[2,0]]\n["B","A","A"]\n[0.9,0]\n2',
        '[[0],[1],[2],[3]]\n["B","A","A","B"]\n[1]\n3',
    ],
    "attention-mask-apply": ["[1.0,2.0]\n[0,0]", "[1000.0,999.0]\n[1,1]"],
    "lru-cache": [
        '["LRUCache","put","put","put","get","get"]\n[[2],[1,1],[2,2],[3,3],[1],[3]]',
        '["LRUCache","put","get","put","get","get"]\n[[1],[5,5],[5],[6,6],[5],[6]]',
    ],
    "implement-trie-prefix-tree": [
        '["Trie","insert","insert","search","startsWith","search"]\n[[],["app"],["apple"],["app"],["ap"],["apple"]]',
        '["Trie","insert","startsWith","search"]\n[[],[""],[""],[""]]',
    ],
    "min-stack": [
        '["MinStack","push","push","pop","getMin","top"]\n[[],[3],[2],[],[],[]]',
        '["MinStack","push","push","push","getMin","pop","getMin"]\n[[],[1],[1],[-1],[],[],[]]',
    ],
    "find-median-from-data-stream": [
        '["MedianFinder","addNum","addNum","addNum","findMedian"]\n[[],[5],[15],[1],[]]',
        '["MedianFinder","addNum","addNum","findMedian","addNum","findMedian"]\n[[],[-1],[-2],[],[-3],[]]',
    ],
    "n-queens": ["3", "5"],
    "permutations": ["[1,2,3,4]"],
    "subsets": ["[]", "[1,2,3,4]"],
    "palindrome-partitioning": ["", "abba", "banana"],
}
