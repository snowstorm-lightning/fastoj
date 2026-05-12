#!/usr/bin/env python3
"""
Seed sample data for FastOJ.
"""
import uuid
from datetime import datetime

from backend.core.database import Base, SessionLocal, engine
from backend.models import Difficulty, Problem, Solution, TestCase


def seed_problems():
    """Seed sample problems."""
    db = SessionLocal()

    try:
        # Check if problems already exist
        if db.query(Problem).first():
            print("Problems already exist, skipping seed.")
            return

        problems_data = [
            {
                "title": "两数之和",
                "slug": "two-sum",
                "description": """## 题目描述

给定一个整数数组 `nums` 和一个整数目标值 `target`，请你在该数组中找出和为目标值 `target` 的那两个整数，并返回它们的数组下标。

你可以假设每种输入只会对应一个答案，且同样的元素不能被重复利用。

## 示例

**示例 1:**
```
输入: nums = [2,7,11,15], target = 9
输出: [0,1]
解释: 因为 nums[0] + nums[1] == 9 ，返回 [0, 1] 。
```

**示例 2:**
```
输入: nums = [3,2,4], target = 6
输出: [1,2]
```

## 提示

- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- -10^9 <= target <= 10^9
- 只会存在一个有效答案
""",
                "difficulty": Difficulty.EASY,
                "time_limit": 1000,
                "memory_limit": 256,
                "tags": ["数组", "哈希表"],
                "hint": "使用哈希表可以做到 O(n) 时间复杂度",
                "source": "LeetCode",
            },
            {
                "title": "两数相加",
                "slug": "add-two-numbers",
                "description": """## 题目描述

给出两个非空的链表用来表示两个非负的整数。其中，它们各自的位数是按照逆序的方式存储的，并且它们的每个节点只能存储一位数字。

如果，我们将这两个数相加起来，则会返回一个新的链表来表示它们的和。

你可以假设除了数字 0 之外，这两个数都不会以 0 开头。

## 示例

**示例 1:**
```
输入: l1 = [2,4,3], l2 = [5,6,4]
输出: [7,0,8]
解释: 342 + 465 = 807.
```
""",
                "difficulty": Difficulty.MEDIUM,
                "time_limit": 2000,
                "memory_limit": 256,
                "tags": ["链表", "数学"],
                "hint": "考虑进位",
                "source": "LeetCode",
            },
            {
                "title": "无重复字符的最长子串",
                "slug": "longest-substring-without-repeating",
                "description": """## 题目描述

给定一个字符串，请你找出其中不含有重复字符的 最长子串 的长度。

## 示例

**示例 1:**
```
输入: s = "abcabcbb"
输出: 3
解释: 因为无重复字符的最长子串是 "abc"，所以其长度为 3。
```

**示例 2:**
```
输入: s = "bbbbb"
输出: 1
解释: 因为无重复字符的最长子串是 "b"，所以其长度为 1。
```
""",
                "difficulty": Difficulty.MEDIUM,
                "time_limit": 2000,
                "memory_limit": 256,
                "tags": ["字符串", "哈希表", "滑动窗口"],
                "hint": "使用滑动窗口",
                "source": "LeetCode",
            },
        ]

        for problem_data in problems_data:
            problem = Problem(
                id=uuid.uuid4(),
                total_submissions=0,
                accepted_submissions=0,
                is_public=True,
                created_at=datetime.utcnow(),
                **problem_data,
            )
            db.add(problem)
            db.flush()

            # Add testcases
            if problem.slug == "two-sum":
                testcases = [
                    {"input": "[2,7,11,15]\n9", "output": "[0,1]", "is_sample": True, "is_hidden": False, "score": 10},
                    {"input": "[3,2,4]\n6", "output": "[1,2]", "is_sample": False, "is_hidden": True, "score": 30},
                    {"input": "[3,3]\n6", "output": "[0,1]", "is_sample": False, "is_hidden": True, "score": 30},
                    {"input": "[1,2,3,4,5]\n9", "output": "[3,4]", "is_sample": False, "is_hidden": True, "score": 30},
                ]
            elif problem.slug == "add-two-numbers":
                testcases = [
                    {"input": "[2,4,3]\n[5,6,4]", "output": "[7,0,8]", "is_sample": True, "is_hidden": False, "score": 10},
                    {"input": "[0]\n[0]", "output": "[0]", "is_sample": False, "is_hidden": True, "score": 30},
                    {"input": "[9,9,9,9,9,9,9]\n[9,9,9,9]", "output": "[8,9,9,9,0,0,0,1]", "is_sample": False, "is_hidden": True, "score": 60},
                ]
            else:
                testcases = [
                    {"input": "abcabcbb", "output": "3", "is_sample": True, "is_hidden": False, "score": 10},
                    {"input": "bbbbb", "output": "1", "is_sample": False, "is_hidden": True, "score": 30},
                    {"input": "pwwkew", "output": "3", "is_sample": False, "is_hidden": True, "score": 30},
                ]

            for i, tc_data in enumerate(testcases):
                testcase = TestCase(
                    id=uuid.uuid4(),
                    problem_id=problem.id,
                    order=i,
                    created_at=datetime.utcnow(),
                    **tc_data,
                )
                db.add(testcase)

            # Add solution
            if problem.slug == "two-sum":
                solution = Solution(
                    id=uuid.uuid4(),
                    problem_id=problem.id,
                    language="python",
                    code="""class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []""",
                    explanation="""## 解题思路

使用哈希表存储已经遍历过的数字及其下标。

对于每个数字 nums[i]，检查 target - nums[i] 是否在哈希表中：
- 如果在，说明找到了答案，返回两个下标
- 如果不在，将当前数字和下标存入哈希表

时间复杂度：O(n)
空间复杂度：O(n)""",
                    time_complexity="O(n)",
                    space_complexity="O(n)",
                    is_official=True,
                    created_at=datetime.utcnow(),
                )
                db.add(solution)

        db.commit()
        print(f"Successfully seeded {len(problems_data)} problems")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created")

    # Seed data
    seed_problems()
    print("Done!")
