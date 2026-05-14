from dataclasses import dataclass

from backend.core.config import settings

AIModelProfile = str


@dataclass(frozen=True)
class AIConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int
    max_output_tokens: int

    @classmethod
    def from_settings(cls, model_profile: AIModelProfile | None = None) -> "AIConfig":
        profile = (model_profile or "default").strip().lower()
        if profile == "deepseek":
            return cls(
                provider=settings.AI_PROVIDER,
                base_url=settings.AI_DEEPSEEK_BASE_URL.rstrip("/"),
                api_key=settings.AI_DEEPSEEK_API_KEY or settings.AI_API_KEY,
                model=settings.AI_DEEPSEEK_MODEL,
                timeout_seconds=settings.AI_TIMEOUT_SECONDS,
                max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS,
            )
        if profile == "qwen-local":
            return cls(
                provider=settings.AI_PROVIDER,
                base_url=settings.AI_QWEN_BASE_URL.rstrip("/"),
                api_key=settings.AI_QWEN_API_KEY,
                model=settings.AI_QWEN_MODEL,
                timeout_seconds=settings.AI_TIMEOUT_SECONDS,
                max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS,
            )
        return cls(
            provider=settings.AI_PROVIDER,
            base_url=settings.AI_BASE_URL.rstrip("/"),
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL,
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )
