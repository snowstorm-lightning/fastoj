import pytest

from backend.services.function_mode import wrap_function_submission


def test_wrap_two_sum_python_function_mode():
    code = """
def two_sum(nums, target):
    seen = {}
    for index, value in enumerate(nums):
        if target - value in seen:
            return [seen[target - value], index]
        seen[value] = index
"""
    wrapped = wrap_function_submission(code, "python", "two-sum")

    namespace: dict[str, object] = {"__name__": "not_main"}
    exec(wrapped, namespace)

    assert callable(namespace["two_sum"])
    assert "json.dumps(result" in wrapped
    assert "Function mode" not in wrapped


def test_wrap_two_sum_uses_json_line_input_only():
    wrapped = wrap_function_submission(
        """
def two_sum(nums, target):
    seen = {}
    for index, value in enumerate(nums):
        if target - value in seen:
            return [seen[target - value], index]
        seen[value] = index
""",
        "python",
        "two-sum",
    )
    assert "_call_args" not in wrapped
    assert "_looks_like_call" not in wrapped
    assert "nums = json.loads(lines[0])" in wrapped
    assert "target = json.loads(lines[1])" in wrapped


def test_function_mode_rejects_unavailable_language():
    with pytest.raises(ValueError, match="Function mode currently supports Python"):
        wrap_function_submission("int main() {}", "cpp", "two-sum")


def test_function_mode_rejects_unavailable_problem():
    with pytest.raises(ValueError, match="Function mode is not available"):
        wrap_function_submission("def solve(): pass", "python", "unknown")
