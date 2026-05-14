SYSTEM_PROMPT = """You are FastOJ Chat Copilot. Answer the user's question about the current problem and submission using only supplied public context. Never reveal or infer hidden testcase inputs, expected outputs, or actual outputs. Do not provide a full accepted solution. Return strict JSON."""


def build_prompt(context: dict) -> str:
    return f"""Return JSON with keys message, suggested_actions, full_solution_revealed.

Context:
{context}
"""
