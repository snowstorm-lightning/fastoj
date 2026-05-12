from backend.sandbox.languages.base import LanguageRunner


class JavaScriptRunner(LanguageRunner):
    """JavaScript (Node.js) language runner."""

    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        return None

    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        return f"node {source_file}"

    def needs_compilation(self) -> bool:
        return False

    def get_file_extension(self) -> str:
        return ".js"


class TypeScriptRunner(LanguageRunner):
    """TypeScript language runner."""

    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        if not output_file:
            output_file = "out"
        return f"tsc {source_file} --outDir {output_file}"

    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        if not output_file:
            output_file = "out"
        # Remove extension from source file
        base_name = source_file.replace(".ts", "")
        return f"node {output_file}/{base_name}.js"

    def needs_compilation(self) -> bool:
        return True

    def get_file_extension(self) -> str:
        return ".ts"
