import httpx

from backend.ai.config import AIConfig
from backend.ai.providers.base import BaseAIProvider


class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, config: AIConfig):
        self.config = config

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        response = httpx.post(
            f"{self.config.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": self.config.max_output_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
