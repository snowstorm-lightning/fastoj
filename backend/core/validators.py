from pydantic import validator

from backend.core.languages import Language


def validate_language(lang: str) -> str:
    """Validate that the language is supported."""
    if not Language.is_supported(lang):
        raise ValueError(f"Language '{lang}' is not supported")
    return lang


def validate_code_length(code: str, max_length: int = 65536) -> str:
    """Validate code length."""
    if len(code) > max_length:
        raise ValueError(f"Code exceeds maximum length of {max_length} characters")
    return code


class LanguageValidator:
    @validator("language")
    def validate_language_field(cls, v):
        return validate_language(v)
