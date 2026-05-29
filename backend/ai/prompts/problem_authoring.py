import json
from typing import Any

SYSTEM_PROMPT = """You are FastOJ's admin-only Problem Authoring Agent.
Create original algorithm practice problems for an online judge.
Return only valid JSON matching the requested schema. Do not wrap it in Markdown.
Do not generate copyrighted problem statements.
Public samples must be small and explainable. When hidden testcases are included, they must cover boundary cases.
Do not place hidden testcase content outside the hidden_testcases field.
For function mode, provide a clear Python-style function_signature and testcase inputs that match the function arguments.
Prefer JSON-line inputs with one JSON value per argument line; a single JSON object keyed by argument name is also acceptable.
For ACM mode, provide stdin/stdout testcases and clear input_format/output_format.
For both mode, provide both function_signature and input_format/output_format. Testcase input should use the function JSON argument format; ACM submissions receive the same input through stdin.
Always include official solution code, explanation, time complexity, space complexity, and validation notes.
When target_languages contains multiple languages, include one official solution per requested language.
For both mode, every official solution must be a function-style canonical solution, not a main/stdin program.
Use ASCII straight quotes inside code. Do not use curly or smart quotes."""

SOLUTION_SYSTEM_PROMPT = """You are FastOJ's admin-only official solution assistant.
Generate one correct official solution for an existing problem draft in the requested programming language.
Return only valid JSON matching the requested schema. Do not wrap it in Markdown.
Use the problem statement, signature, formats, public samples, and existing official solutions as context.
Do not rely on hidden testcase content; hidden testcase content is intentionally omitted.
For function mode, define the function represented by function_signature in the requested language.
For ACM mode, read stdin and write stdout.
For both mode, define the function represented by function_signature; do not include a main function or stdin parsing.
Use ASCII straight quotes inside code. Do not use curly or smart quotes."""

JSON_SCHEMA: dict[str, Any] = {
    "title": "string",
    "slug_candidate": "lowercase-kebab-case-string",
    "description": "string",
    "input_format": "string or null",
    "output_format": "string or null",
    "function_signature": "string or null, e.g. def solve(nums: list[int], target: int) -> list[int]:",
    "difficulty": "easy | medium | hard",
    "tags": ["string"],
    "mode": "function | acm | both",
    "time_limit": "integer milliseconds",
    "memory_limit": "integer MB",
    "hint": "string",
    "official_solution_language": "primary language string",
    "official_solution_code": "primary official solution code string",
    "official_solution_explanation": "primary official solution explanation string",
    "official_solutions": [
        {"language": "python | cpp | java | javascript | typescript | golang | c", "code": "string", "explanation": "string"}
    ],
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

SOLUTION_JSON_SCHEMA: dict[str, Any] = {
    "language": "requested language string",
    "code": "complete official solution code string",
    "explanation": "short official solution explanation string",
}


def build_prompt(context: dict[str, Any]) -> str:
    payload = {
        "task": "Generate one FastOJ problem draft.",
        "input": context,
        "required_json_schema": JSON_SCHEMA,
        "hard_requirements": [
            "At least 1 public_sample_testcase.",
            "Use enough total testcases to cover meaningful behavior and boundaries; do not pad duplicate cases.",
            "Hidden testcases are recommended for non-trivial problems, but simple deterministic or no-input tasks may use zero hidden_testcases.",
            "Every testcase output must be non-empty.",
            "official_solutions must include exactly one solution object for every requested target_languages entry.",
            "official_solution_language/code/explanation should mirror the first official_solutions entry for backward compatibility.",
            "For function mode, every official solution should define the function represented by function_signature in that language.",
            "For both mode, every official solution should define only the function represented by function_signature; do not generate main methods, stdin readers, or stdout printing.",
            "For function or both mode, testcase input must be either newline-separated JSON values matching the function arguments, a single JSON array matching all arguments, or a single JSON object keyed by argument names.",
            "For function or both mode, testcase output must be the JSON-serializable return value, not printed stdout text.",
            "For combination or set-like outputs, make the official solution and expected outputs use deterministic canonical ordering.",
            "For ACM-only mode, every official solution must read stdin and write stdout.",
            "Use only ASCII straight quotes in source code, never curly or smart quotes.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def build_solution_prompt(context: dict[str, Any]) -> str:
    payload = {
        "task": "Generate one official solution for an existing FastOJ draft.",
        "input": context,
        "required_json_schema": SOLUTION_JSON_SCHEMA,
        "hard_requirements": [
            "Return exactly one solution for target_language.",
            "Do not include hidden testcase input or expected output.",
            "Use deterministic canonical ordering for set-like or combination outputs.",
            "For function or both mode, return the problem's return value from the named function; do not print from the function and do not include ACM stdin/stdout scaffolding.",
            "For ACM-only mode, read stdin and print the answer.",
            "Use only ASCII straight quotes in source code, never curly or smart quotes.",
            "The explanation must describe the algorithm and why it is correct.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)
