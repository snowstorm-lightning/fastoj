import httpx

from backend.ai.config import AIConfig
from backend.ai.providers.base import AIProviderUnavailableError, BaseAIProvider


class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, config: AIConfig):
        self.config = config

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if self._requires_real_api_key() and not self._has_real_api_key():
            message = (
                "DeepSeek profile is not configured. Set AI_DEEPSEEK_API_KEY or AI_API_KEY in .env, "
                "then restart Docker services."
            )
            self._mark_unavailable(message)
            raise AIProviderUnavailableError(message)
        try:
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
        except httpx.RequestError as exc:
            message = "AI provider is unreachable. If you selected Qwen local, start the local OpenAI-compatible server first."
            self._mark_unavailable(message)
            raise AIProviderUnavailableError(message) from exc
        except httpx.HTTPStatusError as exc:
            message = f"AI provider returned HTTP {exc.response.status_code} for model {self.config.model}."
            self._mark_unavailable(message)
            raise AIProviderUnavailableError(message) from exc
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            message = "AI provider returned an invalid chat-completions response."
            self._mark_unavailable(message)
            raise AIProviderUnavailableError(message) from exc

    def _requires_real_api_key(self) -> bool:
        return "api.deepseek.com" in self.config.base_url.lower()

    def _has_real_api_key(self) -> bool:
        key = self.config.api_key.strip()
        return bool(key) and key != "sk-no-key-required"

    def _mark_unavailable(self, reason: str) -> None:
        from backend.ai.profiles import mark_ai_profile_unavailable

        mark_ai_profile_unavailable(self.config.profile, reason)
