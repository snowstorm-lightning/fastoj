from backend.sandbox.languages.base import LanguageRunner


class CppRunner(LanguageRunner):
    """C++ language runner."""

    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        if not output_file:
            output_file = "solution"
        return f"g++ -o {output_file} {source_file} -O2 -std=c++17"

    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        if not output_file:
            output_file = "solution"
        return f"./{output_file}"

    def needs_compilation(self) -> bool:
        return True

    def get_file_extension(self) -> str:
        return ".cpp"


class CRunner(LanguageRunner):
    """C language runner."""

    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        if not output_file:
            output_file = "solution"
        return f"gcc -o {output_file} {source_file} -O2 -std=c11"

    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        if not output_file:
            output_file = "solution"
        return f"./{output_file}"

    def needs_compilation(self) -> bool:
        return True

    def get_file_extension(self) -> str:
        return ".c"
