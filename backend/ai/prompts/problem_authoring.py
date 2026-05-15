import json
from typing import Any

SYSTEM_PROMPT = """You are FastOJ's admin-only Problem Authoring Agent.
Create original algorithm practice problems for an online judge.
Return only valid JSON matching the requested schema. Do not wrap it in Markdown.
Do not generate copyrighted problem statements.
Public samples must be small and explainable. Hidden testcases must cover boundary cases.
Do not place hidden testcase content outside the hidden_testcases field.
For function mode, provide a clear Python-style function_signature and JSON-line testcase inputs, one JSON value per argument line.
For ACM mode, provide stdin/stdout testcases and clear input_format/output_format.
Always include official solution code, explanation, time complexity, space complexity, and validation notes."""

JSON_SCHEMA: dict[str, Any] = {
    "title": "string",
    "slug_candidate": "lowercase-kebab-case-string",
    "description": "string",
    "input_format": "string or null",
    "output_format": "string or null",
    "function_signature": "string or null, e.g. def solve(nums: list[int], target: int) -> list[int]:",
    "difficulty": "easy | medium | hard",
    "tags": ["string"],
    "mode": "function | acm",
    "time_limit": "integer milliseconds",
    "memory_limit": "integer MB",
    "hint": "string",
    "official_solution_language": "python",
    "official_solution_code": "string",
    "official_solution_explanation": "string",
    "time_complexity": "string",
    "space_complexity": "string",
    "public_sample_testcases": [
        {"input": "string", "output": "string", "explanation": "string"}
    ],
    "hidden_testcases": [
        {"input": "string", "output": "string", "explanation": "string"}
    ],
    "validation_notes": "string",
}


def build_prompt(context: dict[str, Any]) -> str:
    payload = {
        "task": "Generate one FastOJ problem draft.",
        "input": context,
        "required_json_schema": JSON_SCHEMA,
        "hard_requirements": [
            "At least 2 public_sample_testcases.",
            "At least 6 hidden_testcases.",
            "Every testcase output must be non-empty.",
            "official_solution_language should match target_language when possible.",
            "For function mode, official_solution_code should define the function named in function_signature.",
            "For function mode, each testcase input must be newline-separated JSON values matching the function arguments.",
            "For ACM mode, official_solution_code must read stdin and write stdout.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)
