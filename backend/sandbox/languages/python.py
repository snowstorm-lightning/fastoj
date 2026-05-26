import sys

from backend.sandbox.languages.base import LanguageRunner


class PythonRunner(LanguageRunner):
    """Python language runner."""

    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        """Python doesn't need compilation."""
        return None

    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        executable = "python" if sys.platform == "win32" else "python3"
        return f"{executable} {source_file}"

    def needs_compilation(self) -> bool:
        return False

    def get_file_extension(self) -> str:
        return ".py"
