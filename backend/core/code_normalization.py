SMART_QUOTE_TRANSLATION = str.maketrans(
    {
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        "＂": '"',
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "＇": "'",
    }
)


def normalize_source_code(value: str) -> str:
    """Normalize common rich-text punctuation that breaks source code."""

    return value.translate(SMART_QUOTE_TRANSLATION)
