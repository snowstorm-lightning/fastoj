from typing import Any

DEFAULT_LOCALE = "zh"

LOCALE_META = {
    "zh": {
        "html_lang": "zh-CN",
        "label": "中文",
        "ai_response_language": "Simplified Chinese",
        "source_text": False,
    },
    "en": {
        "html_lang": "en",
        "label": "English",
        "ai_response_language": "English",
        "source_text": True,
    },
}

SUPPORTED_LOCALES = tuple(LOCALE_META.keys())


def normalize_locale(value: Any, default: str = DEFAULT_LOCALE) -> str:
    if isinstance(value, str) and value in LOCALE_META:
        return value
    return default


def validate_locale(value: Any) -> str:
    if isinstance(value, str) and value in LOCALE_META:
        return value
    supported = ", ".join(SUPPORTED_LOCALES)
    raise ValueError(f"Unsupported locale: {value!r}. Supported locales: {supported}")


def ai_response_language(locale: str | None) -> str:
    normalized = normalize_locale(locale)
    return str(LOCALE_META[normalized]["ai_response_language"])


def uses_source_text(locale: str | None) -> bool:
    normalized = normalize_locale(locale)
    return bool(LOCALE_META[normalized]["source_text"])


def localized_system_prompt(prompt: str, locale: str | None) -> str:
    language = ai_response_language(locale)
    return f"{prompt}\nRespond in {language} for every user-facing string inside the JSON values."
