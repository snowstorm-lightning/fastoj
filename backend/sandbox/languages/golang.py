from backend.sandbox.languages.base import LanguageRunner


class GolangRunner(LanguageRunner):
    """Go language runner."""

    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        return None  # Go can run directly with 'go run'

    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        return f"go run {source_file}"

    def needs_compilation(self) -> bool:
        return False

    def get_file_extension(self) -> str:
        return ".go"
