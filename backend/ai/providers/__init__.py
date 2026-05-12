from backend.ai.config import AIConfig
from backend.ai.providers.base import AIProviderUnavailableError, BaseAIProvider
from backend.ai.providers.disabled import DisabledAIProvider
from backend.ai.providers.openai_compatible import OpenAICompatibleProvider


def build_provider(config: AIConfig) -> BaseAIProvider:
    if config.provider == "openai_compatible":
        return OpenAICompatibleProvider(config)
    return DisabledAIProvider()


__all__ = ["AIProviderUnavailableError", "BaseAIProvider", "build_provider"]
