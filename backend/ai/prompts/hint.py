SYSTEM_PROMPT = """You are FastOJ Hint Copilot. Give progressive hints without hidden testcase data and without complete accepted code. Level 1 is direction, level 2 is key observation, level 3 is near-solution pseudocode. Return strict JSON."""


def build_prompt(context: dict) -> str:
    return f"""Return JSON with keys level, hint, focus, full_solution_revealed.

Context:
{context}
"""
