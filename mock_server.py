#!/usr/bin/env python3
"""Small local demo server for the static FastOJ frontend."""

import json
from datetime import UTC, datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = 8080
STATIC_ROOT = Path(__file__).resolve().parent / "frontend" / "src"

MOCK_PROBLEMS = [
    {
        "id": "1",
        "title": "两数之和",
        "slug": "two-sum",
        "difficulty": "easy",
        "tags": ["数组", "哈希表"],
        "total_submissions": 128,
        "accepted_submissions": 91,
        "ac_rate": 0.71,
        "time_limit": 1000,
        "memory_limit": 256,
        "description": "## 题目描述\n\n给定整数数组 `nums` 和目标值 `target`，返回和为目标值的两个下标。\n\n## 输入格式\n\n第一行是数组，第二行是目标值。",
        "sample_testcases": [
            {"input": "[2,7,11,15]\n9", "output": "[0,1]"},
            {"input": "[3,2,4]\n6", "output": "[1,2]"},
        ],
        "hint": "使用哈希表记录已经访问过的数字。",
    },
    {
        "id": "2",
        "title": "无重复字符的最长子串",
        "slug": "longest-substring-without-repeating-characters",
        "difficulty": "medium",
        "tags": ["字符串", "滑动窗口"],
        "total_submissions": 96,
        "accepted_submissions": 43,
        "ac_rate": 0.45,
        "time_limit": 2000,
        "memory_limit": 256,
        "description": "## 题目描述\n\n给定字符串 `s`，返回不含重复字符的最长子串长度。",
        "sample_testcases": [
            {"input": "abcabcbb", "output": "3"},
            {"input": "bbbbb", "output": "1"},
        ],
        "hint": "维护一个窗口，发现重复字符时移动左边界。",
    },
]

MOCK_SOLUTIONS = {
    "1": {
        "id": "sol-1",
        "language": "python",
        "code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target - num], i]\n        seen[num] = i",
        "explanation": "## 思路\n\n遍历数组，用哈希表保存数字到下标的映射。每次检查 `target - num` 是否已经出现。",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    }
}

MOCK_SUBMISSIONS = []


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat()


class FastOJHandler(SimpleHTTPRequestHandler):
    """HTTP handler with a tiny mock API and static file serving."""

    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        if path == "/api/v1/health":
            self.send_json({"status": "healthy", "app": "FastOJ"})
        elif path == "/api/v1/problems":
            problems = filter_problems(query)
            self.send_json(
                {
                    "success": True,
                    "data": problems,
                    "pagination": {
                        "page": int(query.get("page", ["1"])[0]),
                        "page_size": 20,
                        "total": len(problems),
                        "total_pages": 1,
                    },
                }
            )
        elif path.startswith("/api/v1/problems/") and path.endswith("/solutions"):
            problem_id = path.split("/")[4]
            solution = MOCK_SOLUTIONS.get(problem_id)
            self.send_json({"success": True, "data": [solution] if solution else []})
        elif path.startswith("/api/v1/problems/"):
            problem_id = path.split("/")[-1]
            problem = next((item for item in MOCK_PROBLEMS if item["id"] == problem_id), None)
            if problem:
                self.send_json({"success": True, "data": problem})
            else:
                self.send_error(404, "Problem not found")
        elif path == "/api/v1/submissions":
            self.send_json({"success": True, "data": MOCK_SUBMISSIONS})
        elif path.startswith("/api/v1/submissions/"):
            submission_id = path.split("/")[-1]
            submission = next((item for item in MOCK_SUBMISSIONS if item["id"] == submission_id), None)
            if submission:
                self.send_json(submission)
            else:
                self.send_error(404, "Submission not found")
        else:
            self.serve_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        if path == "/api/v1/auth/register":
            payload = json.loads(body)
            self.send_json(
                {
                    "id": "mock-user-id",
                    "username": payload.get("username"),
                    "email": payload.get("email"),
                    "created_at": utc_now_iso(),
                },
                status=201,
            )
        elif path == "/api/v1/auth/login":
            self.send_json(
                {
                    "access_token": "mock-token",
                    "refresh_token": "mock-refresh-token",
                    "token_type": "bearer",
                    "expires_in": 1800,
                }
            )
        elif path in {"/api/v1/submissions", "/api/v1/submissions/run"}:
            payload = json.loads(body)
            submission = build_submission(payload, path.endswith("/run"))
            MOCK_SUBMISSIONS.insert(0, submission)
            self.send_json(submission, status=201)
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def serve_static(self, path):
        if path in {"/", "/static", "/static/"}:
            file_path = STATIC_ROOT / "index.html"
        elif path.startswith("/static/"):
            file_path = STATIC_ROOT / path.removeprefix("/static/")
        else:
            file_path = STATIC_ROOT / path.lstrip("/")

        if not file_path.is_file() or STATIC_ROOT not in file_path.resolve().parents:
            self.send_error(404, "File not found")
            return

        content = file_path.read_bytes()
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }.get(file_path.suffix, "text/plain; charset=utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()


def filter_problems(query):
    difficulty = query.get("difficulty", [""])[0]
    keyword = query.get("keyword", [""])[0].lower()
    tags = [tag.strip() for tag in query.get("tags", [""])[0].split(",") if tag.strip()]

    problems = MOCK_PROBLEMS
    if difficulty:
        problems = [item for item in problems if item["difficulty"] == difficulty]
    if keyword:
        problems = [
            item for item in problems if keyword in item["title"].lower() or keyword in item["slug"].lower()
        ]
    if tags:
        problems = [item for item in problems if all(tag in item["tags"] for tag in tags)]
    return problems


def build_submission(payload, public_only):
    submission_id = f"sub-{len(MOCK_SUBMISSIONS) + 1}"
    problem = next((item for item in MOCK_PROBLEMS if item["id"] == payload.get("problem_id")), MOCK_PROBLEMS[0])
    testcase = problem["sample_testcases"][0]
    result = "ac" if "pass" not in payload.get("code", "") else "wa"
    return {
        "id": submission_id,
        "problem_id": problem["id"],
        "user_id": "mock-user-id",
        "code": payload.get("code", ""),
        "language": payload.get("language", "python"),
        "status": "finished",
        "result": result,
        "error_message": None if result == "ac" else "示例服务器未执行代码，请连接真实后端查看准确结果。",
        "execute_time": 12,
        "memory_used": 16,
        "score": 100 if result == "ac" else 0,
        "created_at": utc_now_iso(),
        "finished_at": utc_now_iso(),
        "testcase_results": [
            {
                "id": f"{submission_id}-case-1",
                "testcase_id": "case-1",
                "status": result,
                "input": testcase["input"],
                "expected_output": testcase["output"],
                "actual_output": testcase["output"] if result == "ac" else "",
                "execute_time": 12,
                "memory_used": 16,
                "is_hidden": False,
            }
        ],
        "problem": {"id": problem["id"], "title": problem["title"], "slug": problem["slug"]},
        "public_only": public_only,
    }


def main():
    server = HTTPServer(("127.0.0.1", PORT), FastOJHandler)
    print(f"FastOJ demo server: http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
