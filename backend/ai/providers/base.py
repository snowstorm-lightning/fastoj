from abc import ABC, abstractmethod


class AIProviderUnavailableError(RuntimeError):
    pass


class BaseAIProvider(ABC):
    @abstractmethod
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model response as text. Callers validate and repair JSON."""
