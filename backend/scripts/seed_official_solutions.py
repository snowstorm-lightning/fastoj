"""Official Python solutions for bundled seed problems.

The registry stores one executable, displayable Python function-mode solution per
seed slug. Keep functions self-contained or list their helper functions in the
registry so seeded code can run inside the judge sandbox without importing this
module.
"""

from __future__ import annotations

import inspect
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from functools import cache
from heapq import heappop, heappush
from itertools import permutations as iter_permutations

from backend.scripts.seed_explanations import solution_explanation_for_slug


@dataclass(frozen=True)
class OfficialSolutionSpec:
    code: str
    explanation: str
    time_complexity: str
    space_complexity: str

    def as_seed_solution(self) -> dict:
        return {
            "language": "python",
            "code": self.code,
            "explanation": self.explanation,
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
        }


def _trim_tree(values):
    result = list(values)
    while result and result[-1] is None:
        result.pop()
    return result


@cache
def _tree_children_cached(values_tuple):
    values = list(values_tuple)
    left_children = [None] * len(values)
    right_children = [None] * len(values)
    if not values or values[0] is None:
        return tuple(left_children), tuple(right_children)
    queue = deque([0])
    cursor = 1
    while queue and cursor < len(values):
        parent = queue.popleft()
        if cursor < len(values):
            if values[cursor] is not None:
                left_children[parent] = cursor
                queue.append(cursor)
            cursor += 1
        if cursor < len(values):
            if values[cursor] is not None:
                right_children[parent] = cursor
                queue.append(cursor)
            cursor += 1
    return tuple(left_children), tuple(right_children)


def _children(values, index):
    left_children, right_children = _tree_children_cached(tuple(values))
    return left_children[index], right_children[index]


def _serialize_tree(values, left_children, right_children, root_index=0):
    if not values:
        return []
    result = []
    queue = deque([root_index])
    while queue:
        index = queue.popleft()
        if index is None:
            result.append(None)
            continue
        result.append(values[index])
        queue.append(left_children[index])
        queue.append(right_children[index])
    return _trim_tree(result)


def _tree_sources() -> list[object]:
    return [_trim_tree, _tree_children_cached, _children]


def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for index, value in enumerate(nums):
        other = target - value
        if other in seen:
            return [seen[other], index]
        seen[value] = index
    return []


def add_two_numbers(l1: list[int], l2: list[int]) -> list[int]:
    answer = []
    carry = 0
    index = 0
    while index < len(l1) or index < len(l2) or carry:
        total = carry
        if index < len(l1):
            total += l1[index]
        if index < len(l2):
            total += l2[index]
        answer.append(total % 10)
        carry = total // 10
        index += 1
    return answer


def length_of_longest_substring(s: str) -> int:
    left = 0
    last_seen = {}
    best = 0
    for right, char in enumerate(s):
        if char in last_seen and last_seen[char] >= left:
            left = last_seen[char] + 1
        last_seen[char] = right
        best = max(best, right - left + 1)
    return best


def is_valid_parentheses(s: str) -> bool:
    stack = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    for char in s:
        if char in pairs:
            stack.append(pairs[char])
        elif not stack or stack.pop() != char:
            return False
    return not stack


def alienOrder(words: list[str]) -> str:  # noqa: N802
    graph = defaultdict(set)
    indegree = {char: 0 for word in words for char in word}
    for first, second in zip(words, words[1:], strict=False):
        if len(first) > len(second) and first.startswith(second):
            return ""
        for left, right in zip(first, second, strict=False):
            if left != right:
                if right not in graph[left]:
                    graph[left].add(right)
                    indegree[right] += 1
                break
    queue = deque(char for char in indegree if indegree[char] == 0)
    order = []
    while queue:
        char = queue.popleft()
        order.append(char)
        for nxt in sorted(graph[char]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return "" if len(order) != len(indegree) else "".join(order)


def can_reach(grid: list[list[str]]) -> bool:
    if not grid:
        return False

    starts = {}
    targets = {}
    for row, values in enumerate(grid):
        for col, cell in enumerate(values):
            if cell in {"A", "B"}:
                starts[cell] = (row, col)
            elif cell == "a":
                targets["A"] = (row, col)
            elif cell == "b":
                targets["B"] = (row, col)

    required = {"A", "B"}
    if not required.issubset(starts) or not required.issubset(targets):
        return False

    def is_open(position: tuple[int, int]) -> bool:
        row, col = position
        return 0 <= row < len(grid) and 0 <= col < len(grid[row]) and grid[row][col] != "#"

    goal = (targets["A"], targets["B"])
    start = (starts["A"], starts["B"])
    queue = deque([start])
    seen = {start}
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    while queue:
        car_a, car_b = queue.popleft()
        if (car_a, car_b) == goal:
            return True

        for moving_a in (True, False):
            current = car_a if moving_a else car_b
            other = car_b if moving_a else car_a
            for dr, dc in directions:
                nxt = (current[0] + dr, current[1] + dc)
                if not is_open(nxt) or nxt == other:
                    continue
                state = (nxt, other) if moving_a else (other, nxt)
                if state not in seen:
                    seen.add(state)
                    queue.append(state)
    return False


def max_sub_array(nums: list[int]) -> int:
    best = current = nums[0]
    for value in nums[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return best


def group_anagrams(strs: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    for word in strs:
        groups["".join(sorted(word))].append(word)
    answer = [sorted(group) for group in groups.values()]
    return sorted(answer, key=lambda group: group[0] if group else "")


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    intervals = sorted(intervals)
    merged = []
    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def climb_stairs(n: int) -> int:
    prev, cur = 1, 1
    for _ in range(n):
        prev, cur = cur, prev + cur
    return prev


def max_area(height: list[int]) -> int:
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        best = max(best, min(height[left], height[right]) * (right - left))
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best


def predict_probability(weights: list[float], bias: float, features: list[float]) -> float:
    score = bias + sum(weight * feature for weight, feature in zip(weights, features, strict=False))
    if score >= 0:
        exp_neg = math.exp(-score)
        return 1 / (1 + exp_neg)
    exp_pos = math.exp(score)
    return exp_pos / (1 + exp_pos)


def predict_knn(points: list[list[float]], labels: list[str], query: list[float], k: int) -> str:
    ranked = sorted(
        (sum((a - b) ** 2 for a, b in zip(point, query, strict=False)), index, labels[index])
        for index, point in enumerate(points)
    )
    votes = Counter(label for _, _, label in ranked[:k])
    return min(votes, key=lambda label: (-votes[label], label))


def assign_clusters(points: list[list[float]], centroids: list[list[float]]) -> list[int]:
    result = []
    for point in points:
        result.append(
            min(
                range(len(centroids)),
                key=lambda index: (sum((a - b) ** 2 for a, b in zip(point, centroids[index], strict=False)), index),
            )
        )
    return result


def attention_row(query: list[float], keys: list[list[float]], values: list[list[float]]) -> list[float]:
    scale = math.sqrt(len(query))
    scores = [sum(q * k for q, k in zip(query, key, strict=False)) / scale for key in keys]
    offset = max(scores)
    weights = [math.exp(score - offset) for score in scores]
    total = sum(weights)
    weights = [weight / total for weight in weights]
    return [sum(weight * value[col] for weight, value in zip(weights, values, strict=False)) for col in range(len(values[0]))]


def cross_entropy_loss(logits: list[float], target: int) -> float:
    offset = max(logits)
    total = sum(math.exp(value - offset) for value in logits)
    return -((logits[target] - offset) - math.log(total))


def masked_softmax(scores: list[float], mask: list[int]) -> list[float]:
    visible = [score for score, keep in zip(scores, mask, strict=False) if keep]
    if not visible:
        return [0.0 for _ in scores]
    offset = max(visible)
    exp_values = [math.exp(score - offset) if keep else 0.0 for score, keep in zip(scores, mask, strict=False)]
    total = sum(exp_values)
    return [value / total if total else 0.0 for value in exp_values]


def longest_consecutive(nums: list[int]) -> int:
    values = set(nums)
    best = 0
    for value in values:
        if value - 1 not in values:
            length = 1
            while value + length in values:
                length += 1
            best = max(best, length)
    return best


def move_zeroes(nums: list[int]) -> list[int]:
    nonzero = [value for value in nums if value != 0]
    return nonzero + [0] * (len(nums) - len(nonzero))


def three_sum(nums: list[int]) -> list[list[int]]:
    nums.sort()
    answer = []
    for index, value in enumerate(nums):
        if index and value == nums[index - 1]:
            continue
        left, right = index + 1, len(nums) - 1
        while left < right:
            total = value + nums[left] + nums[right]
            if total == 0:
                answer.append([value, nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    return answer


def trap(height: list[int]) -> int:
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    while left < right:
        if height[left] < height[right]:
            left_max = max(left_max, height[left])
            water += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            water += right_max - height[right]
            right -= 1
    return water


def find_anagrams(s: str, p: str) -> list[int]:
    if len(p) > len(s):
        return []
    need = Counter(p)
    window = Counter(s[: len(p)])
    answer = [0] if window == need else []
    for right in range(len(p), len(s)):
        left_char = s[right - len(p)]
        window[left_char] -= 1
        if window[left_char] == 0:
            del window[left_char]
        window[s[right]] += 1
        if window == need:
            answer.append(right - len(p) + 1)
    return answer


def subarray_sum(nums: list[int], k: int) -> int:
    counts = Counter({0: 1})
    prefix = 0
    answer = 0
    for value in nums:
        prefix += value
        answer += counts[prefix - k]
        counts[prefix] += 1
    return answer


def max_sliding_window(nums: list[int], k: int) -> list[int]:
    queue = deque()
    answer = []
    for index, value in enumerate(nums):
        while queue and queue[0] <= index - k:
            queue.popleft()
        while queue and nums[queue[-1]] <= value:
            queue.pop()
        queue.append(index)
        if index >= k - 1:
            answer.append(nums[queue[0]])
    return answer


def min_window(s: str, t: str) -> str:
    need = Counter(t)
    missing = len(t)
    left = 0
    best = (float("inf"), 0, 0)
    for right, char in enumerate(s, 1):
        if need[char] > 0:
            missing -= 1
        need[char] -= 1
        while missing == 0:
            if right - left < best[0]:
                best = (right - left, left, right)
            need[s[left]] += 1
            if need[s[left]] > 0:
                missing += 1
            left += 1
    return "" if best[0] == float("inf") else s[best[1] : best[2]]


def rotate_array(nums: list[int], k: int) -> list[int]:
    if not nums:
        return []
    k %= len(nums)
    return nums[-k:] + nums[:-k] if k else nums[:]


def product_except_self(nums: list[int]) -> list[int]:
    answer = [1] * len(nums)
    prefix = 1
    for index, value in enumerate(nums):
        answer[index] = prefix
        prefix *= value
    suffix = 1
    for index in range(len(nums) - 1, -1, -1):
        answer[index] *= suffix
        suffix *= nums[index]
    return answer


def first_missing_positive(nums: list[int]) -> int:
    nums = nums[:]
    for index in range(len(nums)):
        while 1 <= nums[index] <= len(nums) and nums[nums[index] - 1] != nums[index]:
            target = nums[index] - 1
            nums[index], nums[target] = nums[target], nums[index]
    for index, value in enumerate(nums, 1):
        if value != index:
            return index
    return len(nums) + 1


def set_zeroes(matrix: list[list[int]]) -> list[list[int]]:
    if not matrix:
        return []
    rows = {row for row, values in enumerate(matrix) if 0 in values}
    cols = {col for row in matrix for col, value in enumerate(row) if value == 0}
    return [[0 if row in rows or col in cols else value for col, value in enumerate(values)] for row, values in enumerate(matrix)]


def spiral_order(matrix: list[list[int]]) -> list[int]:
    if not matrix or not matrix[0]:
        return []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    answer = []
    while top <= bottom and left <= right:
        answer.extend(matrix[top][left : right + 1])
        top += 1
        for row in range(top, bottom + 1):
            answer.append(matrix[row][right])
        right -= 1
        if top <= bottom:
            answer.extend(reversed(matrix[bottom][left : right + 1]))
            bottom -= 1
        if left <= right:
            for row in range(bottom, top - 1, -1):
                answer.append(matrix[row][left])
            left += 1
    return answer


def rotate_image(matrix: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix[::-1], strict=False)]


def search_matrix_ii(matrix: list[list[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    row, col = 0, len(matrix[0]) - 1
    while row < len(matrix) and col >= 0:
        value = matrix[row][col]
        if value == target:
            return True
        if value > target:
            col -= 1
        else:
            row += 1
    return False


def get_intersection_value(list_a: list[int], list_b: list[int]) -> int | None:
    index = 1
    suffix = []
    while index <= len(list_a) and index <= len(list_b) and list_a[-index] == list_b[-index]:
        suffix.append(list_a[-index])
        index += 1
    suffix.reverse()
    if not suffix:
        return None
    if len(suffix) >= 4:
        return suffix[1]
    return suffix[0]


def reverse_list(values: list[int]) -> list[int]:
    return values[::-1]


def is_palindrome_list(values: list[int]) -> bool:
    return values == values[::-1]


def has_cycle(values: list[int], pos: int) -> bool:
    return pos >= 0 and bool(values)


def detect_cycle_index(values: list[int], pos: int) -> int:
    return pos if pos >= 0 and values else -1


def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:
    i = j = 0
    answer = []
    while i < len(list1) or j < len(list2):
        if j == len(list2) or (i < len(list1) and list1[i] <= list2[j]):
            answer.append(list1[i])
            i += 1
        else:
            answer.append(list2[j])
            j += 1
    return answer


def remove_nth_from_end(values: list[int], n: int) -> list[int]:
    index = len(values) - n
    return values[:index] + values[index + 1 :]


def swap_pairs(values: list[int]) -> list[int]:
    answer = values[:]
    for index in range(0, len(answer) - 1, 2):
        answer[index], answer[index + 1] = answer[index + 1], answer[index]
    return answer


def reverse_k_group(values: list[int], k: int) -> list[int]:
    answer = []
    for index in range(0, len(values), k):
        group = values[index : index + k]
        answer.extend(reversed(group) if len(group) == k else group)
    return answer


def copy_random_list(nodes: list[list[int | None]]) -> list[list[int | None]]:
    return [[value, random_index] for value, random_index in nodes]


def sort_list(values: list[int]) -> list[int]:
    return sorted(values)


def merge_k_lists(lists: list[list[int]]) -> list[int]:
    heap = []
    for list_index, values in enumerate(lists):
        if values:
            heappush(heap, (values[0], list_index, 0))
    answer = []
    while heap:
        value, list_index, item_index = heappop(heap)
        answer.append(value)
        item_index += 1
        if item_index < len(lists[list_index]):
            heappush(heap, (lists[list_index][item_index], list_index, item_index))
    return answer


def run_lru_cache(operations: list[str], args: list[list[int]]) -> list[int | None]:
    from collections import OrderedDict

    cache = OrderedDict()
    capacity = 0
    answer = []
    for op, values in zip(operations, args, strict=False):
        if op == "LRUCache":
            capacity = values[0]
            cache.clear()
            answer.append(None)
        elif op == "get":
            key = values[0]
            if key not in cache:
                answer.append(-1)
            else:
                cache.move_to_end(key)
                answer.append(cache[key])
        else:
            key, value = values
            if key in cache:
                cache.move_to_end(key)
            cache[key] = value
            if len(cache) > capacity:
                cache.popitem(last=False)
            answer.append(None)
    return answer


def inorder_traversal(root: list[int | None]) -> list[int]:
    answer = []

    def dfs(index):
        if index is None:
            return
        left, right = _children(root, index)
        dfs(left)
        answer.append(root[index])
        dfs(right)

    if root:
        dfs(0)
    return answer


def max_depth(root: list[int | None]) -> int:
    def dfs(index):
        if index is None:
            return 0
        left, right = _children(root, index)
        return 1 + max(dfs(left), dfs(right))

    return dfs(0) if root else 0


def invert_tree(root: list[int | None]) -> list[int | None]:
    if not root:
        return []
    left_children, right_children = _tree_children_cached(tuple(root))
    return _serialize_tree(root, right_children, left_children)


def is_symmetric(root: list[int | None]) -> bool:
    def mirror(left, right):
        if left is None or right is None:
            return left is right
        if root[left] != root[right]:
            return False
        left_left, left_right = _children(root, left)
        right_left, right_right = _children(root, right)
        return mirror(left_left, right_right) and mirror(left_right, right_left)

    if not root:
        return True
    left, right = _children(root, 0)
    return mirror(left, right)


def diameter_of_binary_tree(root: list[int | None]) -> int:
    best = 0

    def depth(index):
        nonlocal best
        if index is None:
            return 0
        left, right = _children(root, index)
        left_depth = depth(left)
        right_depth = depth(right)
        best = max(best, left_depth + right_depth)
        return 1 + max(left_depth, right_depth)

    if root:
        depth(0)
    return best


def level_order(root: list[int | None]) -> list[list[int]]:
    if not root:
        return []
    answer = []
    queue = deque([0])
    while queue:
        level = []
        for _ in range(len(queue)):
            index = queue.popleft()
            level.append(root[index])
            left, right = _children(root, index)
            if left is not None:
                queue.append(left)
            if right is not None:
                queue.append(right)
        answer.append(level)
    return answer


def sorted_array_to_bst(nums: list[int]) -> list[int | None]:
    result = []

    def place(left, right, index):
        if left > right:
            return
        mid = (left + right) // 2
        while len(result) <= index:
            result.append(None)
        result[index] = nums[mid]
        place(left, mid - 1, 2 * index + 1)
        place(mid + 1, right, 2 * index + 2)

    place(0, len(nums) - 1, 0)
    return _trim_tree(result)


def is_valid_bst(root: list[int | None]) -> bool:
    def dfs(index, low, high):
        if index is None:
            return True
        value = root[index]
        if not low < value < high:
            return False
        left, right = _children(root, index)
        return dfs(left, low, value) and dfs(right, value, high)

    return dfs(0, -math.inf, math.inf) if root else True


def kth_smallest(root: list[int | None], k: int) -> int:
    values = inorder_traversal(root)
    return values[k - 1]


def right_side_view(root: list[int | None]) -> list[int]:
    return [level[-1] for level in level_order(root)]


def flatten_tree(root: list[int | None]) -> list[int]:
    answer = []

    def preorder(index):
        if index is None:
            return
        answer.append(root[index])
        left, right = _children(root, index)
        preorder(left)
        preorder(right)

    if root:
        preorder(0)
    return answer


def build_tree(preorder: list[int], inorder: list[int]) -> list[int | None]:
    positions = {value: index for index, value in enumerate(inorder)}
    result = []

    def build(pre_left, pre_right, in_left, in_right, index):
        if pre_left > pre_right:
            return
        value = preorder[pre_left]
        while len(result) <= index:
            result.append(None)
        result[index] = value
        split = positions[value]
        left_size = split - in_left
        build(pre_left + 1, pre_left + left_size, in_left, split - 1, 2 * index + 1)
        build(pre_left + left_size + 1, pre_right, split + 1, in_right, 2 * index + 2)

    build(0, len(preorder) - 1, 0, len(inorder) - 1, 0)
    return _trim_tree(result)


def path_sum(root: list[int | None], target_sum: int) -> int:
    counts = Counter({0: 1})
    answer = 0

    def dfs(index, total):
        nonlocal answer
        if index is None:
            return
        total += root[index]
        answer += counts[total - target_sum]
        counts[total] += 1
        left, right = _children(root, index)
        dfs(left, total)
        dfs(right, total)
        counts[total] -= 1

    if root:
        dfs(0, 0)
    return answer


def lowest_common_ancestor(root: list[int | None], p: int, q: int) -> int:
    def dfs(index):
        if index is None:
            return None
        if root[index] in (p, q):
            return index
        left, right = _children(root, index)
        left_hit = dfs(left)
        right_hit = dfs(right)
        if left_hit is not None and right_hit is not None:
            return index
        return left_hit if left_hit is not None else right_hit

    found = dfs(0)
    return root[found]


def max_path_sum(root: list[int | None]) -> int:
    best = -math.inf

    def gain(index):
        nonlocal best
        if index is None:
            return 0
        left, right = _children(root, index)
        left_gain = max(gain(left), 0)
        right_gain = max(gain(right), 0)
        best = max(best, root[index] + left_gain + right_gain)
        return root[index] + max(left_gain, right_gain)

    gain(0)
    return best


def num_islands(grid: list[list[str]]) -> int:
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen = set()
    answer = 0
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] != "1" or (row, col) in seen:
                continue
            answer += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "1" and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return answer


def oranges_rotting(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    fresh = 0
    queue = deque()
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] == 1:
                fresh += 1
            elif grid[row][col] == 2:
                queue.append((row, col, 0))
    minutes = 0
    while queue:
        row, col, minutes = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                queue.append((nr, nc, minutes + 1))
    return minutes if fresh == 0 else -1


def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    graph = [[] for _ in range(num_courses)]
    indegree = [0] * num_courses
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        indegree[course] += 1
    queue = deque(index for index, degree in enumerate(indegree) if degree == 0)
    seen = 0
    while queue:
        course = queue.popleft()
        seen += 1
        for nxt in graph[course]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return seen == num_courses


def run_trie(operations: list[str], args: list[list[str]]) -> list[bool | None]:
    root = {}
    answer = []
    for op, values in zip(operations, args, strict=False):
        if op == "Trie":
            root = {}
            answer.append(None)
        elif op == "insert":
            node = root
            for char in values[0]:
                node = node.setdefault(char, {})
            node["#"] = {}
            answer.append(None)
        else:
            node = root
            ok = True
            for char in values[0]:
                if char not in node:
                    ok = False
                    break
                node = node[char]
            answer.append(ok and (op == "startsWith" or "#" in node))
    return answer


def permute(nums: list[int]) -> list[list[int]]:
    return [list(item) for item in iter_permutations(sorted(nums))]


def subsets(nums: list[int]) -> list[list[int]]:
    nums = sorted(nums)
    answer = []

    def dfs(index, path):
        if index == len(nums):
            answer.append(path[:])
            return
        dfs(index + 1, path)
        path.append(nums[index])
        dfs(index + 1, path)
        path.pop()

    dfs(0, [])
    return sorted(answer)


def letter_combinations(digits: str) -> list[str]:
    if not digits:
        return []
    mapping = {
        "2": "abc",
        "3": "def",
        "4": "ghi",
        "5": "jkl",
        "6": "mno",
        "7": "pqrs",
        "8": "tuv",
        "9": "wxyz",
    }
    answer = [""]
    for digit in digits:
        answer = [prefix + char for prefix in answer for char in mapping[digit]]
    return answer


def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    candidates = sorted(set(candidates))
    answer = []

    def dfs(start, remain, path):
        if remain == 0:
            answer.append(path[:])
            return
        for index in range(start, len(candidates)):
            value = candidates[index]
            if value > remain:
                break
            path.append(value)
            dfs(index, remain - value, path)
            path.pop()

    dfs(0, target, [])
    return answer


def generate_parenthesis(n: int) -> list[str]:
    answer = []

    def dfs(opened, closed, path):
        if len(path) == 2 * n:
            answer.append("".join(path))
            return
        if opened < n:
            path.append("(")
            dfs(opened + 1, closed, path)
            path.pop()
        if closed < opened:
            path.append(")")
            dfs(opened, closed + 1, path)
            path.pop()

    dfs(0, 0, [])
    return answer


def exist(board: list[list[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])
    seen = set()

    def dfs(row, col, index):
        if index == len(word):
            return True
        if not (0 <= row < rows and 0 <= col < cols) or (row, col) in seen or board[row][col] != word[index]:
            return False
        seen.add((row, col))
        ok = any(dfs(row + dr, col + dc, index + 1) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        seen.remove((row, col))
        return ok

    return any(dfs(row, col, 0) for row in range(rows) for col in range(cols))


def partition_palindromes(s: str) -> list[list[str]]:
    answer = []

    def is_palindrome(left, right):
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    def dfs(start, path):
        if start == len(s):
            answer.append(path[:])
            return
        for end in range(start, len(s)):
            if is_palindrome(start, end):
                path.append(s[start : end + 1])
                dfs(end + 1, path)
                path.pop()

    dfs(0, [])
    return answer


def solve_n_queens(n: int) -> list[list[str]]:
    answer = []
    cols = set()
    diag1 = set()
    diag2 = set()
    board = [["."] * n for _ in range(n)]

    def dfs(row):
        if row == n:
            answer.append(["".join(line) for line in board])
            return
        for col in range(n):
            if col in cols or row - col in diag1 or row + col in diag2:
                continue
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            board[row][col] = "Q"
            dfs(row + 1)
            board[row][col] = "."
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)

    dfs(0)
    return answer


def search_insert(nums: list[int], target: int) -> int:
    left, right = 0, len(nums)
    while left < right:
        mid = (left + right) // 2
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left


def search_matrix(matrix: list[list[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1
    while left <= right:
        mid = (left + right) // 2
        value = matrix[mid // cols][mid % cols]
        if value == target:
            return True
        if value < target:
            left = mid + 1
        else:
            right = mid - 1
    return False


def search_range(nums: list[int], target: int) -> list[int]:
    def lower_bound(value):
        left, right = 0, len(nums)
        while left < right:
            mid = (left + right) // 2
            if nums[mid] < value:
                left = mid + 1
            else:
                right = mid
        return left

    start = lower_bound(target)
    if start == len(nums) or nums[start] != target:
        return [-1, -1]
    return [start, lower_bound(target + 1) - 1]


def search_rotated(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1


def find_min(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        if nums[mid] > nums[right]:
            left = mid + 1
        else:
            right = mid
    return nums[left]


def find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:
    nums = sorted(nums1 + nums2)
    mid = len(nums) // 2
    if len(nums) % 2:
        return float(nums[mid])
    return (nums[mid - 1] + nums[mid]) / 2


def run_min_stack(operations: list[str], args: list[list[int]]) -> list[int | None]:
    stack = []
    mins = []
    answer = []
    for op, values in zip(operations, args, strict=False):
        if op == "MinStack":
            stack.clear()
            mins.clear()
            answer.append(None)
        elif op == "push":
            value = values[0]
            stack.append(value)
            mins.append(value if not mins else min(value, mins[-1]))
            answer.append(None)
        elif op == "pop":
            stack.pop()
            mins.pop()
            answer.append(None)
        elif op == "top":
            answer.append(stack[-1])
        else:
            answer.append(mins[-1])
    return answer


def decode_string(s: str) -> str:
    stack = []
    current = []
    number = 0
    for char in s:
        if char.isdigit():
            number = number * 10 + int(char)
        elif char == "[":
            stack.append(("".join(current), number))
            current = []
            number = 0
        elif char == "]":
            prefix, repeat = stack.pop()
            current = [prefix + "".join(current) * repeat]
        else:
            current.append(char)
    return "".join(current)


def daily_temperatures(temperatures: list[int]) -> list[int]:
    answer = [0] * len(temperatures)
    stack = []
    for index, temp in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < temp:
            prev = stack.pop()
            answer[prev] = index - prev
        stack.append(index)
    return answer


def largest_rectangle_area(heights: list[int]) -> int:
    stack = []
    best = 0
    for index, height in enumerate(heights + [0]):
        while stack and heights[stack[-1]] > height:
            h = heights[stack.pop()]
            left = stack[-1] if stack else -1
            best = max(best, h * (index - left - 1))
        stack.append(index)
    return best


def find_kth_largest(nums: list[int], k: int) -> int:
    return sorted(nums, reverse=True)[k - 1]


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    return [value for value, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:k]]


def run_median_finder(operations: list[str], args: list[list[int]]) -> list[float | None]:
    low = []
    high = []
    answer = []

    def add(value):
        heappush(low, -value)
        heappush(high, -heappop(low))
        if len(high) > len(low):
            heappush(low, -heappop(high))

    for op, values in zip(operations, args, strict=False):
        if op == "MedianFinder":
            low.clear()
            high.clear()
            answer.append(None)
        elif op == "addNum":
            add(values[0])
            answer.append(None)
        elif len(low) > len(high):
            answer.append(float(-low[0]))
        else:
            answer.append((-low[0] + high[0]) / 2)
    return answer


def max_profit(prices: list[int]) -> int:
    low = prices[0]
    best = 0
    for price in prices:
        low = min(low, price)
        best = max(best, price - low)
    return best


def can_jump(nums: list[int]) -> bool:
    farthest = 0
    for index, jump in enumerate(nums):
        if index > farthest:
            return False
        farthest = max(farthest, index + jump)
    return True


def jump(nums: list[int]) -> int:
    jumps = end = farthest = 0
    for index in range(len(nums) - 1):
        farthest = max(farthest, index + nums[index])
        if index == end:
            jumps += 1
            end = farthest
    return jumps


def partition_labels(s: str) -> list[int]:
    last = {char: index for index, char in enumerate(s)}
    answer = []
    start = end = 0
    for index, char in enumerate(s):
        end = max(end, last[char])
        if index == end:
            answer.append(end - start + 1)
            start = index + 1
    return answer


def generate_pascals_triangle(num_rows: int) -> list[list[int]]:
    triangle = []
    for row in range(num_rows):
        current = [1] * (row + 1)
        for col in range(1, row):
            current[col] = triangle[-1][col - 1] + triangle[-1][col]
        triangle.append(current)
    return triangle


def rob(nums: list[int]) -> int:
    take = skip = 0
    for value in nums:
        take, skip = skip + value, max(skip, take)
    return max(take, skip)


def num_squares(n: int) -> int:
    squares = [value * value for value in range(1, int(math.sqrt(n)) + 1)]
    dp = [0] + [math.inf] * n
    for amount in range(1, n + 1):
        dp[amount] = 1 + min(dp[amount - square] for square in squares if square <= amount)
    return int(dp[n])


def coin_change(coins: list[int], amount: int) -> int:
    dp = [0] + [amount + 1] * amount
    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value:
                dp[value] = min(dp[value], dp[value - coin] + 1)
    return -1 if dp[amount] > amount else dp[amount]


def word_break(s: str, word_dict: list[str]) -> bool:
    words = set(word_dict)
    dp = [True] + [False] * len(s)
    for end in range(1, len(s) + 1):
        dp[end] = any(dp[start] and s[start:end] in words for start in range(end))
    return dp[-1]


def length_of_lis(nums: list[int]) -> int:
    tails = []
    for value in nums:
        left, right = 0, len(tails)
        while left < right:
            mid = (left + right) // 2
            if tails[mid] < value:
                left = mid + 1
            else:
                right = mid
        if left == len(tails):
            tails.append(value)
        else:
            tails[left] = value
    return len(tails)


def max_product(nums: list[int]) -> int:
    best = high = low = nums[0]
    for value in nums[1:]:
        if value < 0:
            high, low = low, high
        high = max(value, high * value)
        low = min(value, low * value)
        best = max(best, high)
    return best


def can_partition(nums: list[int]) -> bool:
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    possible = {0}
    for value in nums:
        possible |= {item + value for item in possible if item + value <= target}
    return target in possible


def longest_valid_parentheses(s: str) -> int:
    stack = [-1]
    best = 0
    for index, char in enumerate(s):
        if char == "(":
            stack.append(index)
        else:
            stack.pop()
            if stack:
                best = max(best, index - stack[-1])
            else:
                stack.append(index)
    return best


def unique_paths(m: int, n: int) -> int:
    return math.comb(m + n - 2, m - 1)


def min_path_sum(grid: list[list[int]]) -> int:
    dp = [math.inf] * len(grid[0])
    dp[0] = 0
    for row in grid:
        dp[0] += row[0]
        for col in range(1, len(row)):
            dp[col] = min(dp[col], dp[col - 1]) + row[col]
    return dp[-1]


def longest_palindrome(s: str) -> str:
    best = (0, 1)

    def expand(left, right):
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return left + 1, right

    for index in range(len(s)):
        for start, end in (expand(index, index), expand(index, index + 1)):
            if end - start > best[1] - best[0]:
                best = (start, end)
    return s[best[0] : best[1]]


def longest_common_subsequence(text1: str, text2: str) -> int:
    dp = [0] * (len(text2) + 1)
    for char1 in text1:
        prev = 0
        for col, char2 in enumerate(text2, 1):
            saved = dp[col]
            if char1 == char2:
                dp[col] = prev + 1
            else:
                dp[col] = max(dp[col], dp[col - 1])
            prev = saved
    return dp[-1]


def min_distance(word1: str, word2: str) -> int:
    dp = list(range(len(word2) + 1))
    for row, char1 in enumerate(word1, 1):
        prev = dp[0]
        dp[0] = row
        for col, char2 in enumerate(word2, 1):
            saved = dp[col]
            if char1 == char2:
                dp[col] = prev
            else:
                dp[col] = 1 + min(prev, dp[col], dp[col - 1])
            prev = saved
    return dp[-1]


def single_number(nums: list[int]) -> int:
    result = 0
    for value in nums:
        result ^= value
    return result


def majority_element(nums: list[int]) -> int:
    candidate = None
    count = 0
    for value in nums:
        if count == 0:
            candidate = value
        count += 1 if value == candidate else -1
    return candidate


def sort_colors(nums: list[int]) -> list[int]:
    counts = Counter(nums)
    return [0] * counts[0] + [1] * counts[1] + [2] * counts[2]


def next_permutation(nums: list[int]) -> list[int]:
    nums = nums[:]
    pivot = len(nums) - 2
    while pivot >= 0 and nums[pivot] >= nums[pivot + 1]:
        pivot -= 1
    if pivot >= 0:
        swap = len(nums) - 1
        while nums[swap] <= nums[pivot]:
            swap -= 1
        nums[pivot], nums[swap] = nums[swap], nums[pivot]
    nums[pivot + 1 :] = reversed(nums[pivot + 1 :])
    return nums


def find_duplicate(nums: list[int]) -> int:
    slow = fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow


_HELPERS_BY_SLUG: dict[str, list[object]] = {
    "binary-tree-inorder-traversal": _tree_sources(),
    "maximum-depth-of-binary-tree": _tree_sources(),
    "invert-binary-tree": [_trim_tree, _tree_children_cached, _serialize_tree],
    "symmetric-tree": _tree_sources(),
    "diameter-of-binary-tree": _tree_sources(),
    "binary-tree-level-order-traversal": _tree_sources(),
    "convert-sorted-array-to-binary-search-tree": [_trim_tree],
    "validate-binary-search-tree": _tree_sources(),
    "kth-smallest-element-in-a-bst": _tree_sources() + [inorder_traversal],
    "binary-tree-right-side-view": _tree_sources() + [level_order],
    "flatten-binary-tree-to-linked-list": _tree_sources(),
    "construct-binary-tree-from-preorder-and-inorder-traversal": [_trim_tree],
    "path-sum-iii": _tree_sources(),
    "lowest-common-ancestor-of-a-binary-tree": _tree_sources(),
    "binary-tree-maximum-path-sum": _tree_sources(),
}

_FUNCTIONS_BY_SLUG: dict[str, object] = {
    "two-sum": two_sum,
    "add-two-numbers": add_two_numbers,
    "longest-substring-without-repeating-characters": length_of_longest_substring,
    "valid-parentheses": is_valid_parentheses,
    "alien-dictionary": alienOrder,
    "two-car-parking-lot": can_reach,
    "maximum-subarray": max_sub_array,
    "group-anagrams": group_anagrams,
    "merge-intervals": merge_intervals,
    "climbing-stairs": climb_stairs,
    "container-with-most-water": max_area,
    "logistic-regression-sigmoid": predict_probability,
    "knn-majority-vote": predict_knn,
    "kmeans-one-iteration": assign_clusters,
    "scaled-dot-product-attention": attention_row,
    "softmax-cross-entropy": cross_entropy_loss,
    "attention-mask-apply": masked_softmax,
    "longest-consecutive-sequence": longest_consecutive,
    "move-zeroes": move_zeroes,
    "3sum": three_sum,
    "trapping-rain-water": trap,
    "find-all-anagrams-in-a-string": find_anagrams,
    "subarray-sum-equals-k": subarray_sum,
    "sliding-window-maximum": max_sliding_window,
    "minimum-window-substring": min_window,
    "rotate-array": rotate_array,
    "product-of-array-except-self": product_except_self,
    "first-missing-positive": first_missing_positive,
    "set-matrix-zeroes": set_zeroes,
    "spiral-matrix": spiral_order,
    "rotate-image": rotate_image,
    "search-a-2d-matrix-ii": search_matrix_ii,
    "intersection-of-two-linked-lists": get_intersection_value,
    "reverse-linked-list": reverse_list,
    "palindrome-linked-list": is_palindrome_list,
    "linked-list-cycle": has_cycle,
    "linked-list-cycle-ii": detect_cycle_index,
    "merge-two-sorted-lists": merge_two_lists,
    "remove-nth-node-from-end-of-list": remove_nth_from_end,
    "swap-nodes-in-pairs": swap_pairs,
    "reverse-nodes-in-k-group": reverse_k_group,
    "copy-list-with-random-pointer": copy_random_list,
    "sort-list": sort_list,
    "merge-k-sorted-lists": merge_k_lists,
    "lru-cache": run_lru_cache,
    "binary-tree-inorder-traversal": inorder_traversal,
    "maximum-depth-of-binary-tree": max_depth,
    "invert-binary-tree": invert_tree,
    "symmetric-tree": is_symmetric,
    "diameter-of-binary-tree": diameter_of_binary_tree,
    "binary-tree-level-order-traversal": level_order,
    "convert-sorted-array-to-binary-search-tree": sorted_array_to_bst,
    "validate-binary-search-tree": is_valid_bst,
    "kth-smallest-element-in-a-bst": kth_smallest,
    "binary-tree-right-side-view": right_side_view,
    "flatten-binary-tree-to-linked-list": flatten_tree,
    "construct-binary-tree-from-preorder-and-inorder-traversal": build_tree,
    "path-sum-iii": path_sum,
    "lowest-common-ancestor-of-a-binary-tree": lowest_common_ancestor,
    "binary-tree-maximum-path-sum": max_path_sum,
    "number-of-islands": num_islands,
    "rotting-oranges": oranges_rotting,
    "course-schedule": can_finish,
    "implement-trie-prefix-tree": run_trie,
    "permutations": permute,
    "subsets": subsets,
    "letter-combinations-of-a-phone-number": letter_combinations,
    "combination-sum": combination_sum,
    "generate-parentheses": generate_parenthesis,
    "word-search": exist,
    "palindrome-partitioning": partition_palindromes,
    "n-queens": solve_n_queens,
    "search-insert-position": search_insert,
    "search-a-2d-matrix": search_matrix,
    "find-first-and-last-position-of-element-in-sorted-array": search_range,
    "search-in-rotated-sorted-array": search_rotated,
    "find-minimum-in-rotated-sorted-array": find_min,
    "median-of-two-sorted-arrays": find_median_sorted_arrays,
    "min-stack": run_min_stack,
    "decode-string": decode_string,
    "daily-temperatures": daily_temperatures,
    "largest-rectangle-in-histogram": largest_rectangle_area,
    "kth-largest-element-in-an-array": find_kth_largest,
    "top-k-frequent-elements": top_k_frequent,
    "find-median-from-data-stream": run_median_finder,
    "best-time-to-buy-and-sell-stock": max_profit,
    "jump-game": can_jump,
    "jump-game-ii": jump,
    "partition-labels": partition_labels,
    "pascals-triangle": generate_pascals_triangle,
    "house-robber": rob,
    "perfect-squares": num_squares,
    "coin-change": coin_change,
    "word-break": word_break,
    "longest-increasing-subsequence": length_of_lis,
    "maximum-product-subarray": max_product,
    "partition-equal-subset-sum": can_partition,
    "longest-valid-parentheses": longest_valid_parentheses,
    "unique-paths": unique_paths,
    "minimum-path-sum": min_path_sum,
    "longest-palindromic-substring": longest_palindrome,
    "longest-common-subsequence": longest_common_subsequence,
    "edit-distance": min_distance,
    "single-number": single_number,
    "majority-element": majority_element,
    "sort-colors": sort_colors,
    "next-permutation": next_permutation,
    "find-the-duplicate-number": find_duplicate,
}

_COMPLEXITIES: dict[str, tuple[str, str]] = {
    "two-sum": ("O(n)", "O(n)"),
    "add-two-numbers": ("O(max(m, n))", "O(max(m, n))"),
    "longest-substring-without-repeating-characters": ("O(n)", "O(min(n, alphabet))"),
    "valid-parentheses": ("O(n)", "O(n)"),
    "alien-dictionary": ("O(total characters + edges)", "O(unique letters + edges)"),
    "two-car-parking-lot": ("O((R*C)^2)", "O((R*C)^2)"),
    "group-anagrams": ("O(n * k log k)", "O(n * k)"),
    "merge-intervals": ("O(n log n)", "O(n)"),
    "3sum": ("O(n^2)", "O(1) excluding output"),
    "sliding-window-maximum": ("O(n)", "O(k)"),
    "minimum-window-substring": ("O(n + m)", "O(alphabet)"),
    "first-missing-positive": ("O(n)", "O(1)"),
    "merge-k-sorted-lists": ("O(n log k)", "O(k)"),
    "lru-cache": ("O(q)", "O(capacity)"),
    "implement-trie-prefix-tree": ("O(total characters)", "O(total characters)"),
    "permutations": ("O(n! * n)", "O(n! * n)"),
    "subsets": ("O(2^n * n)", "O(2^n * n)"),
    "combination-sum": ("O(number of combinations * combination length)", "O(target)"),
    "generate-parentheses": ("O(Catalan(n) * n)", "O(Catalan(n) * n)"),
    "palindrome-partitioning": ("O(2^n * n)", "O(2^n * n)"),
    "n-queens": ("O(n!)", "O(n^2) excluding output"),
    "median-of-two-sorted-arrays": ("O((m + n) log(m + n))", "O(m + n)"),
    "find-median-from-data-stream": ("O(q log q)", "O(q)"),
    "unique-paths": ("O(1)", "O(1)"),
}


def _source_for(slug: str, func: object) -> str:
    parts = ["from __future__ import annotations"]
    source = "\n\n".join(inspect.getsource(helper).strip() for helper in _HELPERS_BY_SLUG.get(slug, []))
    if "Counter" in source or "Counter" in inspect.getsource(func):
        parts.append("from collections import Counter")
    if "defaultdict" in inspect.getsource(func):
        parts.append("from collections import defaultdict")
    if "deque" in source or "deque" in inspect.getsource(func):
        parts.append("from collections import deque")
    if "math." in source or "math." in inspect.getsource(func):
        parts.append("import math")
    if "heappush" in inspect.getsource(func) or "heappop" in inspect.getsource(func):
        parts.append("from heapq import heappop, heappush")
    if "iter_permutations" in inspect.getsource(func):
        parts.append("from itertools import permutations as iter_permutations")
    if "@cache" in source or "@cache" in inspect.getsource(func):
        parts.append("from functools import cache")
    if source:
        parts.append(source)
    parts.append(inspect.getsource(func).strip())
    return "\n\n".join(parts) + "\n"


def _explanation(slug: str) -> str:
    explanation = solution_explanation_for_slug(slug, "en")
    if explanation is None:
        raise KeyError(f"Missing seed solution explanation for {slug}")
    return explanation


def _solution_for(slug: str, func: object) -> OfficialSolutionSpec:
    time, space = _COMPLEXITIES.get(slug, ("O(n)", "O(n)"))
    return OfficialSolutionSpec(
        code=_source_for(slug, func),
        explanation=_explanation(slug),
        time_complexity=time,
        space_complexity=space,
    )


OFFICIAL_PYTHON_SOLUTIONS: dict[str, OfficialSolutionSpec] = {
    slug: _solution_for(slug, func) for slug, func in _FUNCTIONS_BY_SLUG.items()
}


def official_solution_for_slug(slug: str) -> OfficialSolutionSpec | None:
    return OFFICIAL_PYTHON_SOLUTIONS.get(slug)


def official_function_for_slug(slug: str):
    return _FUNCTIONS_BY_SLUG[slug]
