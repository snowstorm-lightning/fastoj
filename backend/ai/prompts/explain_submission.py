SYSTEM_PROMPT = """You are FastOJ Judge Copilot. Explain submissions using only the supplied problem, code, verdict, and public testcase details. Never reveal or infer hidden testcase inputs, expected outputs, or actual outputs. If hidden tests failed, say that hidden testcase data cannot be shown and suggest boundary categories to inspect. Return strict JSON matching the requested schema. Do not provide a full accepted solution."""


def build_prompt(context: dict) -> str:
    return f"""Return JSON with keys summary, verdict, likely_causes, suspicious_code_regions, public_case_analysis, minimal_fix_hint, edge_cases_to_check, complexity_comment, next_action, full_solution_revealed.

Context:
{context}
"""
