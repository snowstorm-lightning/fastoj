import io
import re
import sys
from contextlib import redirect_stdout

import pytest

from backend.services.function_mode import wrap_function_submission
from backend.services.problem_modes import FUNCTION_SIGNATURES


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
    assert "_fastoj_format_result(result, 'list[int]')" in wrapped
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
    assert "_fastoj_load_args" in wrapped
    assert "('nums', 'list[int]')" in wrapped
    assert "('target', 'int')" in wrapped


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
    assert "('s', 'str')" in wrapped


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
    assert "fastojLoadArgs" in wrapped
    assert '["nums", "list[int]"]' in wrapped
    assert "fn(...args)" in wrapped


@pytest.mark.parametrize(
    ("language", "code", "expected"),
    [
        ("cpp", "int single_number(vector<int> nums) { return nums[0]; }", "single_number(nums)"),
        ("java", "class Solution { public int singleNumber(int[] nums) { return nums[0]; } }", "solver.singleNumber(nums)"),
        ("javascript", "function singleNumber(nums) { return nums[0]; }", "singleNumber"),
        ("typescript", "function singleNumber(nums: number[]): number { return nums[0]; }", "singleNumber"),
        ("golang", "package main\n\nfunc singleNumber(nums []int) int { return nums[0] }", "singleNumber(nums)"),
        ("c", "int single_number(int* nums, int nums_len) { return nums[0]; }", "single_number(nums.data, nums.len)"),
    ],
)
def test_wrap_dynamic_function_mode_for_all_languages(language, code, expected):
    wrapped = wrap_function_submission(
        code,
        language,
        "single-number",
        "def single_number(nums: list[int]) -> int",
    )

    assert expected in wrapped


def test_wrap_dynamic_java_accepts_snake_case_method_name_from_signature():
    wrapped = wrap_function_submission(
        """
class Solution {
    public String print_test() {
        return "test";
    }
}
""",
        "java",
        "print-test",
        "def print_test() -> str:",
    )

    assert "solver.print_test()" in wrapped
    assert "solver.printTest()" not in wrapped


def test_wrap_dynamic_go_accepts_snake_case_function_name_from_signature():
    wrapped = wrap_function_submission(
        """
package main

func print_test() string {
    return "test"
}
""",
        "golang",
        "print-test",
        "def print_test() -> str:",
    )

    assert "result := print_test()" in wrapped
    assert "result := printTest()" not in wrapped
    assert "_ = lines" in wrapped


def test_wrap_dynamic_c_string_return_uses_const_result():
    wrapped = wrap_function_submission(
        """
const char* print_test() {
    return "test";
}
""",
        "c",
        "print-test",
        "def print_test() -> str:",
    )

    assert "const char* result = print_test();" in wrapped
    assert "\n    char* result = print_test();" not in wrapped


def test_wrap_dynamic_c_matrix_function_mode():
    wrapped = wrap_function_submission(
        """
int** merge_intervals(int** intervals, int intervals_rows, int* intervals_cols, int* return_size, int** return_column_sizes) {
    *return_size = intervals_rows;
    *return_column_sizes = intervals_cols;
    return intervals;
}
""",
        "c",
        "merge-intervals",
        "def merge_intervals(intervals: list[list[int]]) -> list[list[int]]",
    )

    assert "IntMatrix intervals = parse_int_matrix(raw);" in wrapped
    assert "int *result_cols = NULL;" in wrapped
    assert "merge_intervals(intervals.data, intervals.rows, intervals.cols, &result_len, &result_cols)" in wrapped
    assert "print_int_matrix(result, result_len, result_cols);" in wrapped


def test_wrap_dynamic_c_string_matrix_function_mode():
    wrapped = wrap_function_submission(
        """
char*** group_anagrams(char** strs, int strs_len, int* return_size, int** return_column_sizes) {
    *return_size = 0;
    *return_column_sizes = NULL;
    return NULL;
}
""",
        "c",
        "group-anagrams",
        "def group_anagrams(strs: list[str]) -> list[list[str]]",
    )

    assert "StringVec strs = parse_string_vec(raw);" in wrapped
    assert "char*** result = group_anagrams(strs.data, strs.len, &result_len, &result_cols);" in wrapped
    assert "print_string_matrix(result, result_len, result_cols);" in wrapped


def test_function_signatures_do_not_use_bare_list_returns():
    offenders = {
        slug: signature
        for slug, signature in FUNCTION_SIGNATURES.items()
        if re.search(r"->\s*list\s*:?\s*$", signature)
    }

    assert offenders == {}


def test_dynamic_python_function_mode_formats_float_lists():
    wrapped = wrap_function_submission(
        """
def masked_softmax(scores, mask):
    return [1.0, 0.0]
""",
        "python",
        "attention-mask-apply",
    )

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("[0.0,0.0]\n[1,0]")
        output = io.StringIO()
        with redirect_stdout(output):
            exec(wrapped, {"__name__": "__main__"})
    finally:
        sys.stdin = old_stdin

    assert output.getvalue().strip() == "[1.0000,0.0000]"


def test_wrap_dynamic_c_nullable_list_return_function_mode():
    wrapped = wrap_function_submission(
        """
int* run_min_stack(char** operations, int operations_len, int** args, int args_rows, int* args_cols, int* return_size, int** return_nulls) {
    *return_size = 0;
    *return_nulls = NULL;
    return NULL;
}
""",
        "c",
        "min-stack",
    )

    assert "int* run_min_stack(char** operations, int operations_len, int** args, int args_rows, int* args_cols, int* return_size, int** return_nulls)" in wrapped
    assert "int *result_nulls = NULL;" in wrapped
    assert "print_nullable_int_array(result, result_nulls, result_len);" in wrapped


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
    assert "_fastoj_format_result(result, 'bool')" in wrapped


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


def test_alien_dictionary_accepts_leetcode_style_solution_class():
    wrapped = wrap_function_submission(
        """
class Solution:
    def alienOrder(self, words):
        from collections import defaultdict, deque
        graph = defaultdict(set)
        indegree = {ch: 0 for word in words for ch in word}
        for first, second in zip(words, words[1:]):
            if len(first) > len(second) and first.startswith(second):
                return ""
            for left, right in zip(first, second):
                if left != right:
                    if right not in graph[left]:
                        graph[left].add(right)
                        indegree[right] += 1
                    break
        queue = deque(ch for ch in indegree if indegree[ch] == 0)
        order = []
        while queue:
            ch = queue.popleft()
            order.append(ch)
            for nxt in sorted(graph[ch]):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        return "" if len(order) != len(indegree) else "".join(order)
""",
        "python",
        "alien-dictionary",
    )

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO('["wrt","wrf","er","ett","rftt"]')
        output = io.StringIO()
        with redirect_stdout(output):
            exec(wrapped, {"__name__": "__main__"})
    finally:
        sys.stdin = old_stdin

    assert output.getvalue().strip() == "wertf"


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


def test_dynamic_python_function_mode_keeps_unquoted_string_arguments():
    wrapped = wrap_function_submission(
        """
def letter_combinations(digits):
    return [digits]
""",
        "python",
        "letter-combinations-of-a-phone-number",
    )

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("23")
        output = io.StringIO()
        with redirect_stdout(output):
            exec(wrapped, {"__name__": "__main__"})
    finally:
        sys.stdin = old_stdin

    assert output.getvalue().strip() == '["23"]'


def test_dynamic_python_function_mode_prints_null_for_none():
    wrapped = wrap_function_submission(
        """
def getIntersectionNode(headA, headB):
    return None
""",
        "python",
        "intersection-of-two-linked-lists",
    )

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("[2,6,4]\n[1,5]")
        output = io.StringIO()
        with redirect_stdout(output):
            exec(wrapped, {"__name__": "__main__"})
    finally:
        sys.stdin = old_stdin

    assert output.getvalue().strip() == "null"


@pytest.mark.parametrize(
    ("slug", "code", "stdin_value", "expected"),
    [
        (
            "reverse-linked-list",
            "def reverseList(head):\n    prev = None\n    while head:\n        nxt = head.next\n        head.next = prev\n        prev = head\n        head = nxt\n    return prev\n",
            "[1,2,3,4,5]",
            "[5,4,3,2,1]",
        ),
        (
            "linked-list-cycle-ii",
            "def detectCycle(head):\n    slow = fast = head\n    while fast and fast.next:\n        slow = slow.next\n        fast = fast.next.next\n        if slow is fast:\n            cur = head\n            while cur is not slow:\n                cur = cur.next\n                slow = slow.next\n            return cur\n    return None\n",
            "[3,2,0,-4]\n1",
            "1",
        ),
        (
            "copy-list-with-random-pointer",
            "def copyRandomList(head):\n    clones = {}\n    cur = head\n    while cur:\n        clones[cur] = Node(cur.val)\n        cur = cur.next\n    cur = head\n    while cur:\n        clones[cur].next = clones.get(cur.next)\n        clones[cur].random = clones.get(cur.random)\n        cur = cur.next\n    return clones.get(head)\n",
            "[[7,null],[13,0],[11,4],[10,2],[1,0]]",
            "[[7,null],[13,0],[11,4],[10,2],[1,0]]",
        ),
        (
            "invert-binary-tree",
            "def invertTree(root):\n    if root:\n        root.left, root.right = invertTree(root.right), invertTree(root.left)\n    return root\n",
            "[4,2,7,1,3,6,9]",
            "[4,7,2,9,6,3,1]",
        ),
        (
            "lowest-common-ancestor-of-a-binary-tree",
            "def lowestCommonAncestor(root, p, q):\n    if root in (None, p, q):\n        return root\n    left = lowestCommonAncestor(root.left, p, q)\n    right = lowestCommonAncestor(root.right, p, q)\n    return root if left and right else left or right\n",
            "[3,5,1,6,2,0,8,null,null,7,4]\n5\n1",
            "3",
        ),
        (
            "flatten-binary-tree-to-linked-list",
            "def flatten(root):\n    nodes = []\n    def dfs(node):\n        if node:\n            nodes.append(node)\n            dfs(node.left)\n            dfs(node.right)\n    dfs(root)\n    for index, node in enumerate(nodes):\n        node.left = None\n        node.right = nodes[index + 1] if index + 1 < len(nodes) else None\n",
            "[1,2,5,3,4,null,6]",
            "[1,2,3,4,5,6]",
        ),
    ],
)
def test_node_python_function_mode_executes_structured_inputs(slug, code, stdin_value, expected):
    wrapped = wrap_function_submission(code, "python", slug)

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(stdin_value)
        output = io.StringIO()
        with redirect_stdout(output):
            exec(wrapped, {"__name__": "__main__"})
    finally:
        sys.stdin = old_stdin

    assert output.getvalue().strip() == expected


@pytest.mark.parametrize(
    ("language", "code", "expected"),
    [
        ("cpp", "class Solution { public: ListNode* reverseList(ListNode* head) { return head; } };", "Solution solver"),
        ("java", "class Solution { public ListNode reverseList(ListNode head) { return head; } }", "class ListNode"),
        ("javascript", "function reverseList(head) { return head; }", "class ListNode"),
        ("typescript", "function reverseList(head: any): any { return head; }", "// @ts-nocheck"),
        ("golang", "package main\nfunc reverseList(head *ListNode) *ListNode { return head }", "type ListNode struct"),
        ("c", "struct ListNode* reverseList(struct ListNode* head) { return head; }", "struct ListNode"),
    ],
)
def test_node_function_mode_wraps_static_languages(language, code, expected):
    wrapped = wrap_function_submission(code, language, "reverse-linked-list")

    assert expected in wrapped
    assert "reverseList" in wrapped
    assert "listValues" in wrapped or "list_values" in wrapped
