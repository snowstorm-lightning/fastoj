import io
import sys
from contextlib import redirect_stdout

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


def test_wrap_longest_substring_canonical_hot100_slug():
    wrapped = wrap_function_submission(
        """
def length_of_longest_substring(s):
    return len(set(s))
""",
        "python",
        "longest-substring-without-repeating-characters",
    )

    assert "length_of_longest_substring" in wrapped
    assert "s = raw" in wrapped


def test_wrap_two_sum_cpp_function_mode():
    wrapped = wrap_function_submission(
        """
vector<int> two_sum(vector<int> nums, int target) {
    return {0, 1};
}
""",
        "cpp",
        "two-sum",
    )
    assert "parseIntVector" in wrapped
    assert "two_sum(nums, target)" in wrapped
    assert "int main()" in wrapped


def test_wrap_two_sum_javascript_function_mode():
    wrapped = wrap_function_submission(
        """
function twoSum(nums, target) {
  return [0, 1];
}
""",
        "javascript",
        "two-sum",
    )
    assert "JSON.parse(lines[0])" in wrapped
    assert "fn(nums, target)" in wrapped


def test_wrap_valid_parentheses_python_function_mode():
    code = """
def is_valid_parentheses(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for ch in s:
        if ch in pairs.values():
            stack.append(ch)
        elif not stack or stack.pop() != pairs[ch]:
            return False
    return not stack
"""
    wrapped = wrap_function_submission(code, "python", "valid-parentheses")

    namespace: dict[str, object] = {"__name__": "not_main"}
    exec(wrapped, namespace)

    assert callable(namespace["is_valid_parentheses"])
    assert "str(result).lower()" in wrapped


def test_function_mode_rejects_unavailable_problem():
    with pytest.raises(ValueError, match="Function mode is not available"):
        wrap_function_submission("def solve(): pass", "python", "unknown")


def test_wrap_dynamic_python_function_mode_from_signature():
    wrapped = wrap_function_submission(
        """
def echo_value(value):
    return value
""",
        "python",
        "agent-echo",
        "def echo_value(value: int) -> int",
    )

    assert "_fastoj_load_args" in wrapped
    assert "Expected function echo_value" in wrapped
    assert "result = func(*args)" in wrapped


def test_dynamic_python_function_mode_accepts_object_arguments():
    wrapped = wrap_function_submission(
        """
def add_pair(left, right):
    return left + right
""",
        "python",
        "agent-add-pair",
        "def add_pair(left: int, right: int) -> int",
    )

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO('{"left":2,"right":5}')
        output = io.StringIO()
        with redirect_stdout(output):
            exec(wrapped, {"__name__": "__main__"})
    finally:
        sys.stdin = old_stdin

    assert output.getvalue().strip() == "7"


def test_dynamic_python_function_mode_accepts_array_arguments():
    wrapped = wrap_function_submission(
        """
def add_pair(left, right):
    return left + right
""",
        "python",
        "agent-add-pair",
        "def add_pair(left: int, right: int) -> int",
    )

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("[2,5]")
        output = io.StringIO()
        with redirect_stdout(output):
            exec(wrapped, {"__name__": "__main__"})
    finally:
        sys.stdin = old_stdin

    assert output.getvalue().strip() == "7"
