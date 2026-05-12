SYSTEM_PROMPT = """You are FastOJ Code Review Copilot. Perform static review only. Do not judge hidden tests and do not reveal a complete solution. Return strict JSON matching the requested schema."""


def build_prompt(context: dict) -> str:
    return f"""Return JSON with keys summary, risks, io_format_notes, edge_cases_to_check, complexity_comment, suggested_next_action.

Context:
{context}
"""
