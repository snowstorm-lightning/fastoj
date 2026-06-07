from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class AIProviderUnavailableError(RuntimeError):
    pass


class AIProviderEmptyResponseError(RuntimeError):
    def __init__(self, message: str, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.metadata = metadata or {}


@dataclass(frozen=True)
class AICompletion:
    content: str
    metadata: dict[str, Any]


class BaseAIProvider(ABC):
    @abstractmethod
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model response as text. Callers validate and repair JSON."""

    def complete_json_with_metadata(self, system_prompt: str, user_prompt: str) -> AICompletion:
        content = self.complete_json(system_prompt, user_prompt)
        return AICompletion(
            content=content,
            metadata={
                "content_len": len(content),
                "finish_reason": None,
                "usage": None,
            },
        )
