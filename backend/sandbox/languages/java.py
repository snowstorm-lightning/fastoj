from backend.sandbox.languages.base import LanguageRunner


class JavaRunner(LanguageRunner):
    """Java language runner."""

    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        return f"javac {source_file}"

    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        # Java needs the class name to run
        class_name = self.get_class_name(source_file)
        return f"java -cp . {class_name}"

    def needs_compilation(self) -> bool:
        return True

    def get_file_extension(self) -> str:
        return ".java"

    def get_class_name(self, source_file: str) -> str:
        """Extract class name from Java file."""
        # Simple extraction - would need proper parsing in production
        return "Main"
