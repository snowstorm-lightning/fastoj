from backend.ai.providers.base import AIProviderUnavailableError, BaseAIProvider


class DisabledAIProvider(BaseAIProvider):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        raise AIProviderUnavailableError("AI provider is disabled. Set AI_PROVIDER=openai_compatible.")
