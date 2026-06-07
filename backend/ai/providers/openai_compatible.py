import httpx

from backend.ai.config import AIConfig
from backend.ai.providers.base import (
    AICompletion,
    AIProviderEmptyResponseError,
    AIProviderUnavailableError,
    BaseAIProvider,
)


class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, config: AIConfig):
        self.config = config

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        return self.complete_json_with_metadata(system_prompt, user_prompt).content

    def complete_json_with_metadata(self, system_prompt: str, user_prompt: str) -> AICompletion:
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
            choice = data["choices"][0]
            message_data = choice["message"]
            content = str(message_data.get("content") or "")
            metadata = self._completion_metadata(data, choice, message_data, content)
            if not content.strip():
                raise AIProviderEmptyResponseError(self._empty_response_message(metadata), metadata)
            return AICompletion(content=content, metadata=metadata)
        except httpx.RequestError as exc:
            message = "AI provider is unreachable. If you selected Qwen local, start the local OpenAI-compatible server first."
            self._mark_unavailable(message)
            raise AIProviderUnavailableError(message) from exc
        except httpx.HTTPStatusError as exc:
            message = f"AI provider returned HTTP {exc.response.status_code} for model {self.config.model}."
            self._mark_unavailable(message)
            raise AIProviderUnavailableError(message) from exc
        except AIProviderEmptyResponseError:
            raise
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

    def _completion_metadata(
        self,
        data: dict,
        choice: dict,
        message_data: dict,
        content: str,
    ) -> dict:
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        completion_details = (
            usage.get("completion_tokens_details") if isinstance(usage.get("completion_tokens_details"), dict) else {}
        )
        reasoning = message_data.get("reasoning_content") or message_data.get("reasoning") or ""
        return {
            "model": data.get("model") or self.config.model,
            "finish_reason": choice.get("finish_reason"),
            "content_len": len(content),
            "reasoning_len": len(str(reasoning)),
            "message_keys": sorted(str(key) for key in message_data.keys()),
            "usage": usage or None,
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": completion_details.get("reasoning_tokens"),
            "max_tokens": self.config.max_output_tokens,
        }

    def _empty_response_message(self, metadata: dict) -> str:
        finish_reason = metadata.get("finish_reason") or "unknown"
        reasoning_tokens = metadata.get("reasoning_tokens")
        max_tokens = metadata.get("max_tokens")
        if finish_reason == "length":
            return (
                "AI provider returned an empty response body because the model exhausted the output budget "
                f"before JSON content started (finish_reason=length, reasoning_tokens={reasoning_tokens}, "
                f"max_tokens={max_tokens})."
            )
        return (
            "AI provider returned an empty response body "
            f"(finish_reason={finish_reason}, reasoning_tokens={reasoning_tokens}, max_tokens={max_tokens})."
        )
