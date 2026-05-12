from abc import ABC, abstractmethod


class LanguageRunner(ABC):
    """Base class for language-specific code execution."""

    @abstractmethod
    def get_compile_command(self, source_file: str, output_file: str | None = None) -> str | None:
        """Get the compile command for this language."""
        pass

    @abstractmethod
    def get_run_command(self, source_file: str, output_file: str | None = None) -> str | None:
        """Get the run command for this language."""
        pass

    @abstractmethod
    def needs_compilation(self) -> bool:
        """Whether this language needs compilation before execution."""
        pass

    def get_file_extension(self) -> str:
        """Get the file extension for this language."""
        return ".txt"

    def get_class_name(self, source_file: str) -> str:
        """Get the class name from source file (for Java)."""
        return "Main"
