#!/usr/bin/env python3
"""Seed sample data for FastOJ."""

import json
import uuid

from backend.core.database import Base, SessionLocal, engine
from backend.core.time import utc_now
from backend.models import Difficulty, Problem, Solution, TestCase
from backend.scripts.hot100_data import HOT100_LEGACY_SLUG_ALIASES, HOT100_PROBLEMS_DATA
from backend.scripts.problem_statement_details import enrich_problem_descriptions
from backend.scripts.seed_official_solutions import official_solution_for_slug
from backend.scripts.seed_testcase_augmentation import augmented_testcases
from backend.services.problem_modes import FUNCTION_SIGNATURES

PROBLEMS_DATA = [
    {
        "problem": {
            "title": "Two Sum",
            "slug": "two-sum",
            "description": "Given an integer array nums and an integer target, return indices of the two numbers such that they add up to target.",
            "difficulty": Difficulty.EASY,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Array", "Hash Table", "Function"],
            "hint": "Use a hash table to remember values already scanned.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "[2,7,11,15]\n9", "output": "[0,1]", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[3,2,4]\n6", "output": "[1,2]", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "[3,3]\n6", "output": "[0,1]", "is_sample": False, "is_hidden": True, "score": 30},
        ],
        "solution": {
            "language": "python",
            "code": "def two_sum(nums, target):\n    seen = {}\n    for i, value in enumerate(nums):\n        if target - value in seen:\n            return [seen[target - value], i]\n        seen[value] = i\n    return []\n",
            "explanation": "Scan once and store the index of each visited value. The complement check gives O(n) time.",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
        },
    },
    {
        "problem": {
            "title": "Add Two Numbers",
            "slug": "add-two-numbers",
            "description": "Two digit arrays store numbers in reverse order. Return the reverse-order digit array for their sum.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 2000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Linked List", "Math", "Function"],
            "hint": "Walk both arrays and carry one digit at a time.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "[2,4,3]\n[5,6,4]", "output": "[7,0,8]", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[0]\n[0]", "output": "[0]", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "[9,9,9,9,9,9,9]\n[9,9,9,9]", "output": "[8,9,9,9,0,0,0,1]", "is_sample": False, "is_hidden": True, "score": 60},
        ],
    },
    {
        "problem": {
            "title": "Longest Substring Without Repeating Characters",
            "slug": "longest-substring-without-repeating-characters",
            "description": "Given a string s, find the length of the longest substring without repeated characters.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 2000,
            "memory_limit": 256,
            "tags": ["Hot 100", "String", "Hash Table", "Sliding Window", "Function"],
            "hint": "Keep a moving left boundary and last-seen positions.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "abcabcbb", "output": "3", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "bbbbb", "output": "1", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "pwwkew", "output": "3", "is_sample": False, "is_hidden": True, "score": 30},
        ],
    },
    {
        "problem": {
            "title": "Valid Parentheses",
            "slug": "valid-parentheses",
            "description": "Given a string containing only parentheses characters, determine whether every bracket is closed in the correct order.",
            "difficulty": Difficulty.EASY,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Interview", "Stack", "String"],
            "hint": "Use a stack of expected closing brackets.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "()[]{}", "output": "true", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "(]", "output": "false", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "([{}])", "output": "true", "is_sample": False, "is_hidden": True, "score": 60},
        ],
    },
    {
        "problem": {
            "title": "Alien Dictionary",
            "slug": "alien-dictionary",
            "description": "Given words sorted by an unknown alien alphabet, infer one valid ordering of the letters or return an empty string when no valid alphabet order exists.",
            "difficulty": Difficulty.HARD,
            "time_limit": 2000,
            "memory_limit": 256,
            "tags": ["Interview", "Graph", "Topological Sort", "Breadth-First Search", "Function"],
            "hint": "Compare adjacent words, add the first differing character as a directed edge, then run topological sort.",
            "source": "FastOJ interview practice",
        },
        "testcases": [
            {"input": "[\"wrt\",\"wrf\",\"er\",\"ett\",\"rftt\"]", "output": "wertf", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[\"z\",\"x\"]", "output": "zx", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": "[\"z\",\"x\",\"z\"]", "output": "", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": "[\"abc\",\"ab\"]", "output": "", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": "[\"ab\",\"ac\",\"bc\",\"bd\",\"cd\"]", "output": "abcd", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": "[\"a\",\"b\",\"c\",\"d\"]", "output": "abcd", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": "[\"abc\",\"abd\",\"acd\",\"bcd\"]", "output": "abcd", "is_sample": False, "is_hidden": True, "score": 15},
        ],
        "solution": {
            "language": "python",
            "code": "from collections import defaultdict, deque\n\n\ndef alienOrder(words):\n    graph = defaultdict(set)\n    indegree = {}\n\n    for word in words:\n        for ch in word:\n            indegree.setdefault(ch, 0)\n\n    for first, second in zip(words, words[1:]):\n        if len(first) > len(second) and first.startswith(second):\n            return \"\"\n\n        for left, right in zip(first, second):\n            if left != right:\n                if right not in graph[left]:\n                    graph[left].add(right)\n                    indegree[right] += 1\n                break\n\n    queue = deque(ch for ch in indegree if indegree[ch] == 0)\n    order = []\n\n    while queue:\n        ch = queue.popleft()\n        order.append(ch)\n        for nxt in sorted(graph[ch]):\n            indegree[nxt] -= 1\n            if indegree[nxt] == 0:\n                queue.append(nxt)\n\n    if len(order) != len(indegree):\n        return \"\"\n    return \"\".join(order)\n",
            "explanation": "Build precedence edges from the first differing character in each adjacent word pair. Kahn's topological sort returns an ordering when all characters can be processed; a prefix conflict or remaining cycle means no valid order exists.",
            "time_complexity": "O(total characters + edges)",
            "space_complexity": "O(unique letters + edges)",
        },
    },
    {
        "problem": {
            "title": "Two-Car Parking Lot",
            "slug": "two-car-parking-lot",
            "description": "Given a parking-lot grid with two cars and two matching parking spots, decide whether both cars can be parked in their own spots.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 2000,
            "memory_limit": 256,
            "tags": ["Interview", "Graph", "Breadth-First Search", "Grid", "Function"],
            "hint": "Search states containing both car positions, not each car independently.",
            "source": "FastOJ interview practice",
        },
        "testcases": [
            {"input": '[["A",".","a"],["#","#","."],["B",".","b"]]', "output": "true", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": '[["A","#","a"],["#","#","."],["B",".","b"]]', "output": "false", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": '[["A","B","b","a"]]', "output": "false", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": '[["A","B","b","a"],[".",".",".","."]]', "output": "true", "is_sample": False, "is_hidden": True, "score": 15},
            {"input": '[["A",".","b"],[".","#","."],["a",".","B"]]', "output": "true", "is_sample": False, "is_hidden": True, "score": 15},
        ],
    },
    {
        "problem": {
            "title": "Maximum Subarray",
            "slug": "maximum-subarray",
            "description": "Given an integer array, return the maximum possible sum of a non-empty contiguous subarray.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Interview", "Array", "Dynamic Programming"],
            "hint": "Track the best subarray ending at the current position.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[1]", "output": "1", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "[5,4,-1,7,8]", "output": "23", "is_sample": False, "is_hidden": True, "score": 60},
        ],
    },
    {
        "problem": {
            "title": "Group Anagrams",
            "slug": "group-anagrams",
            "description": "Group strings that are anagrams. Return groups in deterministic sorted order.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 2000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Interview", "Array", "Hash Table", "String"],
            "hint": "Use the sorted characters of each word as the hash key.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "[\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"]", "output": "[[\"ate\",\"eat\",\"tea\"],[\"bat\"],[\"nat\",\"tan\"]]", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[\"\"]", "output": "[[\"\"]]", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "[\"a\"]", "output": "[[\"a\"]]", "is_sample": False, "is_hidden": True, "score": 60},
        ],
    },
    {
        "problem": {
            "title": "Merge Intervals",
            "slug": "merge-intervals",
            "description": "Merge all overlapping intervals and output the merged interval list ordered by start.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Interview", "Array", "Sorting"],
            "hint": "Sort by left endpoint, then extend or start a new interval.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "[[1,3],[2,6],[8,10],[15,18]]", "output": "[[1,6],[8,10],[15,18]]", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[[1,4],[4,5]]", "output": "[[1,5]]", "is_sample": False, "is_hidden": True, "score": 45},
            {"input": "[[1,4],[0,2],[3,5]]", "output": "[[0,5]]", "is_sample": False, "is_hidden": True, "score": 45},
        ],
    },
    {
        "problem": {
            "title": "Climbing Stairs",
            "slug": "climbing-stairs",
            "description": "Each move climbs 1 or 2 steps. Given n, return how many distinct ways can reach the top.",
            "difficulty": Difficulty.EASY,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Interview", "Dynamic Programming", "Math"],
            "hint": "This is Fibonacci with small shifted base cases.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "2", "output": "2", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "3", "output": "3", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "10", "output": "89", "is_sample": False, "is_hidden": True, "score": 60},
        ],
    },
    {
        "problem": {
            "title": "Container With Most Water",
            "slug": "container-with-most-water",
            "description": "Given heights, choose two lines that together with the x-axis hold the most water.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["Hot 100", "Interview", "Array", "Two Pointers"],
            "hint": "Move the pointer at the shorter line inward.",
            "source": "Hot 100 practice",
        },
        "testcases": [
            {"input": "[1,8,6,2,5,4,8,3,7]", "output": "49", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[1,1]", "output": "1", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "[4,3,2,1,4]", "output": "16", "is_sample": False, "is_hidden": True, "score": 60},
        ],
    },
    {
        "problem": {
            "title": "Logistic Regression Sigmoid",
            "slug": "logistic-regression-sigmoid",
            "description": "Implement the prediction probability p=sigmoid(w dot x + b) without using machine-learning libraries.",
            "difficulty": Difficulty.EASY,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["AI", "ML", "Logistic Regression", "Function"],
            "hint": "Compute the linear score first, then apply 1/(1+exp(-z)).",
            "source": "FastOJ AI practice",
        },
        "testcases": [
            {"input": "[0.5,-0.25]\n0.1\n[2.0,4.0]", "output": "0.5250", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[1.0,1.0]\n0.0\n[0.0,0.0]", "output": "0.5000", "is_sample": False, "is_hidden": True, "score": 30},
            {"input": "[-1.0,2.0]\n0.5\n[1.0,1.5]", "output": "0.9241", "is_sample": False, "is_hidden": True, "score": 60},
        ],
    },
    {
        "problem": {
            "title": "KNN Majority Vote",
            "slug": "knn-majority-vote",
            "description": "Predict a query label by Euclidean distance and majority vote among the k nearest training points.",
            "difficulty": Difficulty.EASY,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["AI", "ML", "KNN", "Function"],
            "hint": "Sort by squared distance; squared distance is enough for ranking.",
            "source": "FastOJ AI practice",
        },
        "testcases": [
            {"input": "[[0,0],[1,1],[5,5]]\n[\"A\",\"A\",\"B\"]\n[0.2,0.1]\n3", "output": "A", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[[0,0],[3,3],[4,4],[10,10]]\n[\"A\",\"B\",\"B\",\"A\"]\n[3.5,3.6]\n3", "output": "B", "is_sample": False, "is_hidden": True, "score": 45},
            {"input": "[[0],[2],[4],[6]]\n[\"A\",\"B\",\"B\",\"A\"]\n[3]\n2", "output": "B", "is_sample": False, "is_hidden": True, "score": 45},
        ],
    },
    {
        "problem": {
            "title": "KMeans One Iteration",
            "slug": "kmeans-one-iteration",
            "description": "Given fixed centroids, assign every point to the nearest centroid. Return zero-based cluster indices.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["AI", "ML", "KMeans", "Function"],
            "hint": "This is the assignment step before centroid recomputation.",
            "source": "FastOJ AI practice",
        },
        "testcases": [
            {"input": "[[0,0],[1,1],[8,8]]\n[[0,0],[10,10]]", "output": "[0,0,1]", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[[2,2],[9,9],[6,6]]\n[[1,1],[8,8]]", "output": "[0,1,1]", "is_sample": False, "is_hidden": True, "score": 45},
            {"input": "[[0],[5],[9]]\n[[1],[10]]", "output": "[0,0,1]", "is_sample": False, "is_hidden": True, "score": 45},
        ],
    },
    {
        "problem": {
            "title": "Scaled Dot-Product Attention",
            "slug": "scaled-dot-product-attention",
            "description": "Hand-write one query row of scaled dot-product attention. Return the weighted value vector rounded by the judge.",
            "difficulty": Difficulty.HARD,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["AI", "Deep Learning", "MHA", "Function"],
            "hint": "Use a numerically stable softmax by subtracting the maximum score.",
            "source": "FastOJ AI practice",
        },
        "testcases": [
            {"input": "[1,0]\n[[1,0],[0,1]]\n[[10,0],[0,10]]", "output": "[6.6976,3.3024]", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[0,1]\n[[1,0],[0,1]]\n[[10,0],[0,10]]", "output": "[3.3024,6.6976]", "is_sample": False, "is_hidden": True, "score": 45},
            {"input": "[1,1]\n[[1,1],[1,0]]\n[[2,4],[8,0]]", "output": "[3.9814,2.6790]", "is_sample": False, "is_hidden": True, "score": 45},
        ],
    },
    {
        "problem": {
            "title": "Softmax Cross Entropy",
            "slug": "softmax-cross-entropy",
            "description": "Given logits and a target index, compute the numerically stable softmax cross-entropy loss rounded to 4 decimals.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["AI", "ML", "Softmax", "Function"],
            "hint": "Subtract the maximum logit before exponentiation.",
            "source": "FastOJ AI practice",
        },
        "testcases": [
            {"input": "[2.0,1.0,0.1]\n0", "output": "0.4170", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[0.0,0.0]\n1", "output": "0.6931", "is_sample": False, "is_hidden": True, "score": 45},
            {"input": "[1.5,3.0,-0.5]\n1", "output": "0.2258", "is_sample": False, "is_hidden": True, "score": 45},
        ],
    },
    {
        "problem": {
            "title": "Attention Mask Apply",
            "slug": "attention-mask-apply",
            "description": "Apply an attention mask to a score row before softmax. Masked positions must receive probability 0.",
            "difficulty": Difficulty.MEDIUM,
            "time_limit": 1000,
            "memory_limit": 256,
            "tags": ["AI", "Deep Learning", "MHA", "Softmax", "Function"],
            "hint": "Ignore masked scores when computing the softmax denominator.",
            "source": "FastOJ AI practice",
        },
        "testcases": [
            {"input": "[1.0,2.0,3.0]\n[1,1,0]", "output": "[0.2689,0.7311,0.0000]", "is_sample": True, "is_hidden": False, "score": 10},
            {"input": "[0.0,0.0]\n[1,0]", "output": "[1.0000,0.0000]", "is_sample": False, "is_hidden": True, "score": 45},
            {"input": "[2.0,1.0,0.0]\n[1,1,1]", "output": "[0.6652,0.2447,0.0900]", "is_sample": False, "is_hidden": True, "score": 45},
        ],
    },
]

PROBLEMS_DATA.extend(HOT100_PROBLEMS_DATA)


for item in PROBLEMS_DATA:
    signature = FUNCTION_SIGNATURES.get(item["problem"]["slug"])
    if signature:
        item["problem"]["mode"] = "both"
        item["problem"]["function_signature"] = signature

enrich_problem_descriptions(PROBLEMS_DATA)


DEFAULT_SOLUTIONS = {
    "add-two-numbers": {
        "code": "def add_two_numbers(l1, l2):\n    ans, carry, i = [], 0, 0\n    while i < len(l1) or i < len(l2) or carry:\n        total = carry\n        if i < len(l1): total += l1[i]\n        if i < len(l2): total += l2[i]\n        ans.append(total % 10)\n        carry = total // 10\n        i += 1\n    return ans\n",
        "explanation": "Walk both reversed digit arrays from low to high digits. Keep a carry and append total % 10 each step.",
    },
    "longest-substring-without-repeating-characters": {
        "code": "def length_of_longest_substring(s):\n    left = 0\n    last = {}\n    best = 0\n    for right, ch in enumerate(s):\n        if ch in last and last[ch] >= left:\n            left = last[ch] + 1\n        last[ch] = right\n        best = max(best, right - left + 1)\n    return best\n",
        "explanation": "Use a sliding window. When a repeated character appears inside the window, move the left boundary after its previous position.",
    },
    "longest-substring-without-repeating": {
        "code": "def length_of_longest_substring(s):\n    left = 0\n    last = {}\n    best = 0\n    for right, ch in enumerate(s):\n        if ch in last and last[ch] >= left:\n            left = last[ch] + 1\n        last[ch] = right\n        best = max(best, right - left + 1)\n    return best\n",
        "explanation": "Use a sliding window. When a repeated character appears inside the window, move the left boundary after its previous position.",
    },
    "valid-parentheses": {
        "code": "import sys\ns = sys.stdin.read().strip()\nstack = []\npairs = {'(': ')', '[': ']', '{': '}'}\nok = True\nfor ch in s:\n    if ch in pairs:\n        stack.append(pairs[ch])\n    elif not stack or stack.pop() != ch:\n        ok = False\n        break\nprint('true' if ok and not stack else 'false')\n",
        "explanation": "Push the expected closing bracket for every opening bracket. Each closing bracket must match the current stack top.",
    },
    "maximum-subarray": {
        "code": "import json, sys\nnums = json.loads(sys.stdin.read())\nbest = cur = nums[0]\nfor x in nums[1:]:\n    cur = max(x, cur + x)\n    best = max(best, cur)\nprint(best)\n",
        "explanation": "Kadane's algorithm keeps the best subarray ending at the current index and the global best answer.",
    },
    "group-anagrams": {
        "code": "import json, sys\nwords = json.loads(sys.stdin.read())\ngroups = {}\nfor word in words:\n    groups.setdefault(''.join(sorted(word)), []).append(word)\nans = [sorted(group) for group in groups.values()]\nans.sort(key=lambda group: group[0] if group else '')\nprint(json.dumps(ans, separators=(',', ':')))\n",
        "explanation": "Anagrams have the same sorted-character key. Group by that key, then sort groups deterministically for judging.",
    },
    "merge-intervals": {
        "code": "import json, sys\nintervals = json.loads(sys.stdin.read())\nintervals.sort()\nans = []\nfor left, right in intervals:\n    if not ans or left > ans[-1][1]:\n        ans.append([left, right])\n    else:\n        ans[-1][1] = max(ans[-1][1], right)\nprint(json.dumps(ans, separators=(',', ':')))\n",
        "explanation": "Sort intervals by start. Merge into the last interval when ranges overlap; otherwise start a new interval.",
    },
    "climbing-stairs": {
        "code": "import sys\nn = int(sys.stdin.read())\na, b = 1, 1\nfor _ in range(n):\n    a, b = b, a + b\nprint(a)\n",
        "explanation": "The number of ways follows Fibonacci-style recurrence: ways[n] = ways[n-1] + ways[n-2].",
    },
    "container-with-most-water": {
        "code": "import json, sys\nh = json.loads(sys.stdin.read())\nleft, right = 0, len(h) - 1\nbest = 0\nwhile left < right:\n    best = max(best, min(h[left], h[right]) * (right - left))\n    if h[left] < h[right]: left += 1\n    else: right -= 1\nprint(best)\n",
        "explanation": "Use two pointers. The area is limited by the shorter side, so move the shorter side inward.",
    },
}


def _default_solution(item: dict) -> dict | None:
    slug = item["problem"]["slug"]
    official = official_solution_for_slug(slug)
    if official:
        return official.as_seed_solution()
    if item.get("solution"):
        return item["solution"]
    data = DEFAULT_SOLUTIONS.get(slug)
    if data:
        return {
            "language": "python",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            **data,
        }
    return None


def _expanded_testcases(item: dict) -> list[dict]:
    """Return policy-normalized augmented testcases."""
    return augmented_testcases(item)


def _case_with_io_metadata(case_data: dict) -> dict:
    """Translate io_metadata into the TestCase model column name."""

    normalized = dict(case_data)
    io_metadata = normalized.pop("io_metadata", None)
    normalized["io_metadata_json"] = json.dumps(io_metadata, separators=(",", ":")) if isinstance(io_metadata, dict) else None
    return normalized


def seed_problems():
    """Seed or normalize sample problems by slug."""
    db = SessionLocal()

    try:
        created = 0
        normalized = 0
        for item in PROBLEMS_DATA:
            problem_data = item["problem"]
            existing = db.query(Problem).filter(Problem.slug == problem_data["slug"]).first()
            if not existing:
                legacy_slugs = HOT100_LEGACY_SLUG_ALIASES.get(problem_data["slug"], [])
                if legacy_slugs:
                    existing = db.query(Problem).filter(Problem.slug.in_(legacy_slugs)).first()
            if existing:
                problem = existing
                for key, value in problem_data.items():
                    setattr(problem, key, value)
                normalized += 1
            else:
                problem = Problem(
                    id=uuid.uuid4(),
                    total_submissions=0,
                    accepted_submissions=0,
                    is_public=True,
                    created_at=utc_now(),
                    **problem_data,
                )
                db.add(problem)
                db.flush()
                created += 1

            existing_cases = (
                db.query(TestCase)
                .filter(TestCase.problem_id == problem.id)
                .order_by(TestCase.order.asc(), TestCase.created_at.asc())
                .all()
            )
            testcases = _expanded_testcases(item)
            for order, tc_data in enumerate(testcases):
                tc_data = _case_with_io_metadata(tc_data)
                tc_data.pop("order", None)
                if order < len(existing_cases):
                    testcase = existing_cases[order]
                    testcase.order = order
                    for key, value in tc_data.items():
                        setattr(testcase, key, value)
                else:
                    db.add(
                        TestCase(
                            id=uuid.uuid4(),
                            problem_id=problem.id,
                            order=order,
                            created_at=utc_now(),
                            **tc_data,
                        )
                    )

            if len(existing_cases) > len(testcases):
                neutral_case = testcases[-1]
                for order, testcase in enumerate(existing_cases[len(testcases) :], start=len(testcases)):
                    testcase.order = order
                    testcase.input = neutral_case["input"]
                    testcase.output = neutral_case["output"]
                    testcase.is_sample = False
                    testcase.is_hidden = True
                    testcase.score = 0

            solution_data = _default_solution(item)
            if solution_data:
                solution = (
                    db.query(Solution)
                    .filter(
                        Solution.problem_id == problem.id,
                        Solution.language == solution_data["language"],
                        Solution.is_official == True,
                    )
                    .first()
                )
                if solution:
                    for key, value in solution_data.items():
                        setattr(solution, key, value)
                else:
                    db.add(
                        Solution(
                            id=uuid.uuid4(),
                            problem_id=problem.id,
                            is_official=True,
                            created_at=utc_now(),
                            **solution_data,
                        )
                    )

        db.commit()
        print(f"Seed complete, created {created} missing problems and normalized {normalized} existing problems.")

    except Exception as exc:
        print(f"Error seeding data: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_problems()
