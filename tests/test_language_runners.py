"""Tests for language runners."""

import pytest

from backend.sandbox.languages.cpp import CppRunner, CRunner
from backend.sandbox.languages.golang import GolangRunner
from backend.sandbox.languages.java import JavaRunner
from backend.sandbox.languages.javascript import JavaScriptRunner, TypeScriptRunner
from backend.sandbox.languages.python import PythonRunner


class TestPythonRunner:
    """Test cases for PythonRunner."""

    def test_needs_compilation(self):
        """Python does not need compilation."""
        runner = PythonRunner()
        assert runner.needs_compilation() is False

    def test_get_file_extension(self):
        """Python uses .py extension."""
        runner = PythonRunner()
        assert runner.get_file_extension() == ".py"

    def test_get_compile_command_returns_none(self):
        """Python compile command should return None."""
        runner = PythonRunner()
        result = runner.get_compile_command("test.py")
        assert result is None

    def test_get_run_command(self):
        """Python run command should use python3 on Unix or python on Windows."""
        runner = PythonRunner()
        result = runner.get_run_command("test.py")
        import sys
        expected = f"python{'3' if sys.platform != 'win32' else ''} test.py"
        assert result == expected
        assert "python" in result
        assert "test.py" in result


class TestJavaScriptRunner:
    """Test cases for JavaScriptRunner."""

    def test_needs_compilation(self):
        """JavaScript does not need compilation."""
        runner = JavaScriptRunner()
        assert runner.needs_compilation() is False

    def test_get_file_extension(self):
        """JavaScript uses .js extension."""
        runner = JavaScriptRunner()
        assert runner.get_file_extension() == ".js"

    def test_get_compile_command_returns_none(self):
        """JavaScript compile command should return None."""
        runner = JavaScriptRunner()
        result = runner.get_compile_command("test.js")
        assert result is None

    def test_get_run_command(self):
        """JavaScript run command should use node."""
        runner = JavaScriptRunner()
        result = runner.get_run_command("test.js")
        assert result == "node test.js"
        assert "node" in result


class TestTypeScriptRunner:
    """Test cases for TypeScriptRunner."""

    def test_needs_compilation(self):
        """TypeScript needs compilation."""
        runner = TypeScriptRunner()
        assert runner.needs_compilation() is True

    def test_get_file_extension(self):
        """TypeScript uses .ts extension."""
        runner = TypeScriptRunner()
        assert runner.get_file_extension() == ".ts"

    def test_get_compile_command(self):
        """TypeScript compile command should use tsc."""
        runner = TypeScriptRunner()
        result = runner.get_compile_command("test.ts")
        assert "tsc" in result
        assert "test.ts" in result

    def test_get_run_command(self):
        """TypeScript run command should use node."""
        runner = TypeScriptRunner()
        result = runner.get_run_command("test.ts")
        assert "node" in result


class TestJavaRunner:
    """Test cases for JavaRunner."""

    def test_needs_compilation(self):
        """Java needs compilation."""
        runner = JavaRunner()
        assert runner.needs_compilation() is True

    def test_get_file_extension(self):
        """Java uses .java extension."""
        runner = JavaRunner()
        assert runner.get_file_extension() == ".java"

    def test_get_compile_command(self):
        """Java compile command should use javac."""
        runner = JavaRunner()
        result = runner.get_compile_command("Main.java")
        assert "javac" in result
        assert "Main.java" in result

    def test_get_run_command(self):
        """Java run command should use java."""
        runner = JavaRunner()
        result = runner.get_run_command("Main.java")
        assert "java" in result
        assert "-cp" in result


class TestGolangRunner:
    """Test cases for GolangRunner."""

    def test_needs_compilation(self):
        """Go does not need compilation (uses go run)."""
        runner = GolangRunner()
        assert runner.needs_compilation() is False

    def test_get_file_extension(self):
        """Go uses .go extension."""
        runner = GolangRunner()
        assert runner.get_file_extension() == ".go"

    def test_get_compile_command_returns_none(self):
        """Go compile command should return None (uses go run)."""
        runner = GolangRunner()
        result = runner.get_compile_command("main.go")
        assert result is None

    def test_get_run_command(self):
        """Go run command should use go run."""
        runner = GolangRunner()
        result = runner.get_run_command("main.go")
        assert "go run" in result
        assert "main.go" in result


class TestCppRunner:
    """Test cases for CppRunner."""

    def test_needs_compilation(self):
        """C++ needs compilation."""
        runner = CppRunner()
        assert runner.needs_compilation() is True

    def test_get_file_extension(self):
        """C++ uses .cpp extension."""
        runner = CppRunner()
        assert runner.get_file_extension() == ".cpp"

    def test_get_compile_command(self):
        """C++ compile command should use g++."""
        runner = CppRunner()
        result = runner.get_compile_command("main.cpp")
        assert "g++" in result
        assert "main.cpp" in result
        assert "-std=c++17" in result

    def test_get_run_command(self):
        """C++ run command should execute the compiled binary."""
        runner = CppRunner()
        result = runner.get_run_command("main.cpp", "main")
        assert "./main" in result


class TestCRunner:
    """Test cases for CRunner."""

    def test_needs_compilation(self):
        """C needs compilation."""
        runner = CRunner()
        assert runner.needs_compilation() is True

    def test_get_file_extension(self):
        """C uses .c extension."""
        runner = CRunner()
        assert runner.get_file_extension() == ".c"

    def test_get_compile_command(self):
        """C compile command should use gcc."""
        runner = CRunner()
        result = runner.get_compile_command("main.c")
        assert "gcc" in result
        assert "main.c" in result
        assert "-std=c11" in result

    def test_get_run_command(self):
        """C run command should execute the compiled binary."""
        runner = CRunner()
        result = runner.get_run_command("main.c", "main")
        assert "./main" in result
