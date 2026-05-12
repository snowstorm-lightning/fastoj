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


# Language configuration
LANGUAGE_CONFIG = {
    "python": {
        "display_name": "Python",
        "extension": ".py",
        "compile_command": None,
        "run_command": "python3 {filename}",
        "time_limit_multiplier": 1.0,
    },
    "c": {
        "display_name": "C",
        "extension": ".c",
        "compile_command": "gcc -o {output} {source} -O2 -std=c11",
        "run_command": "{output}",
        "time_limit_multiplier": 1.0,
    },
    "cpp": {
        "display_name": "C++",
        "extension": ".cpp",
        "compile_command": "g++ -o {output} {source} -O2 -std=c++17",
        "run_command": "{output}",
        "time_limit_multiplier": 1.0,
    },
    "java": {
        "display_name": "Java",
        "extension": ".java",
        "compile_command": "javac {filename}",
        "run_command": "java -cp . {classname}",
        "time_limit_multiplier": 2.0,
    },
    "javascript": {
        "display_name": "JavaScript",
        "extension": ".js",
        "compile_command": None,
        "run_command": "node {filename}",
        "time_limit_multiplier": 1.0,
    },
    "typescript": {
        "display_name": "TypeScript",
        "extension": ".ts",
        "compile_command": "tsc {filename} --outDir {outdir}",
        "run_command": "node {outdir}/{filename}.js",
        "time_limit_multiplier": 1.5,
    },
    "golang": {
        "display_name": "Go",
        "extension": ".go",
        "compile_command": None,
        "run_command": "go run {filename}",
        "time_limit_multiplier": 1.0,
    },
}
