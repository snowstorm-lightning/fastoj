#!/usr/bin/env python3
"""Simple mock server for FastOJ frontend demo."""

import json
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8080

# Mock data
MOCK_PROBLEMS = [
    {
        "id": "1",
        "title": "两数之和",
        "slug": "two-sum",
        "difficulty": "easy",
        "tags": ["数组", "哈希表"],
        "total_submissions": 100,
        "accepted_submissions": 45,
        "ac_rate": 0.45,
        "time_limit": 1000,
        "memory_limit": 256,
        "description": "## 题目描述\n\n给定一个整数数组 `nums` 和一个整数目标值 `target`...",
        "sample_testcases": [
            {"input": "[2,7,11,15]\n9", "output": "[0,1]"},
            {"input": "[3,2,4]\n6", "output": "[1,2]"}
        ]
    },
    {
        "id": "2",
        "title": "两数相加",
        "slug": "add-two-numbers",
        "difficulty": "medium",
        "tags": ["链表", "数学"],
        "total_submissions": 80,
        "accepted_submissions": 30,
        "ac_rate": 0.375,
        "time_limit": 2000,
        "memory_limit": 256,
        "description": "## 题目描述\n\n给出两个非空的链表...",
        "sample_testcases": [
            {"input": "[2,4,3]\n[5,6,4]", "output": "[7,0,8]"}
        ]
    },
    {
        "id": "3",
        "title": "无重复字符的最长子串",
        "slug": "longest-substring-without-repeating",
        "difficulty": "medium",
        "tags": ["字符串", "哈希表", "滑动窗口"],
        "total_submissions": 60,
        "accepted_submissions": 20,
        "ac_rate": 0.333,
        "time_limit": 2000,
        "memory_limit": 256,
        "description": "## 题目描述\n\n给定一个字符串...",
        "sample_testcases": [
            {"input": "abcabcbb", "output": "3"}
        ]
    }
]

MOCK_SUBMISSIONS = [
    {
        "id": "sub1",
        "problem_id": "1",
        "language": "python",
        "status": "finished",
        "result": "ac",
        "score": 100,
        "execute_time": 45,
        "memory_used": 12,
        "created_at": "2026-04-01T10:00:00"
    }
]


class FastOJHandler(SimpleHTTPRequestHandler):
    """Custom handler for FastOJ."""

    def do_GET(self):
        """Handle GET requests."""
        path = urlparse(self.path).path

        # API endpoints
        if path == "/api/v1/health":
            self.send_json({"status": "healthy", "app": "FastOJ"})
        elif path == "/api/v1/problems":
            self.send_json({
                "success": True,
                "data": MOCK_PROBLEMS,
                "pagination": {"page": 1, "page_size": 20, "total": 3, "total_pages": 1}
            })
        elif path.startswith("/api/v1/problems/"):
            problem_id = path.split("/")[-1]
            for p in MOCK_PROBLEMS:
                if p["id"] == problem_id:
                    self.send_json(p)
                    return
            self.send_error(404, "Problem not found")
        elif path == "/api/v1/submissions":
            self.send_json({
                "success": True,
                "data": MOCK_SUBMISSIONS
            })
        elif path.startswith("/api/v1/submissions/"):
            sub_id = path.split("/")[-1]
            for s in MOCK_SUBMISSIONS:
                if s["id"] == sub_id:
                    self.send_json(s)
                    return
            self.send_error(404, "Submission not found")
        else:
            # Serve static files
            if path == "/":
                path = "/static/index.html"
            elif not path.startswith("/static"):
                path = "/static" + path

            static_path = f"backend{path}"
            try:
                with open(static_path, "rb") as f:
                    content = f.read()
                ext = static_path.split(".")[-1]
                content_type = {
                    "html": "text/html",
                    "css": "text/css",
                    "js": "application/javascript",
                }.get(ext, "text/plain")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "File not found")

    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"

        if path == "/api/v1/auth/register":
            self.send_json({
                "id": "new-user-id",
                "username": json.loads(body).get("username"),
                "email": json.loads(body).get("email"),
                "created_at": "2026-04-01T00:00:00"
            }, status=201)
        elif path == "/api/v1/auth/login":
            self.send_json({
                "access_token": "mock-token-12345",
                "refresh_token": "mock-refresh-12345",
                "token_type": "bearer",
                "expires_in": 1800
            })
        elif path == "/api/v1/submissions/run":
            self.send_json({
                "success": True,
                "message": "代码提交成功",
                "submission_id": "sub-mock-" + str(hash(body))[:8]
            })
        else:
            self.send_error(404, "Endpoint not found")

    def send_json(self, data, status=200):
        """Send JSON response."""
        response = json.dumps(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response.encode())

    def end_headers(self):
        """Add CORS headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.end_headers()


def main():
    """Start the server."""
    server = HTTPServer(("", PORT), FastOJHandler)
    print(f"[FastOJ] Server running at http://localhost:{PORT}")
    print(f"[FastOJ] Open http://localhost:{PORT}/ in your browser")
    server.serve_forever()


if __name__ == "__main__":
    main()
