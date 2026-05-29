from enum import Enum


class Language(str, Enum):
    PYTHON = "python"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GOLANG = "golang"

    @classmethod
    def get_supported_languages(cls):
        return [
            cls.PYTHON,
            cls.C,
            cls.CPP,
            cls.JAVA,
            cls.JAVASCRIPT,
            cls.TYPESCRIPT,
            cls.GOLANG,
        ]

    @classmethod
    def is_supported(cls, lang: str) -> bool:
        return lang in [l.value for l in cls.get_supported_languages()]
