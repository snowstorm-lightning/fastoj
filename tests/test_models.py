"""Tests for database models (enum tests only)."""

import pytest

from backend.models import (
    Difficulty,
    Language,
    SubmissionResult,
    SubmissionStatus,
)


class TestDifficulty:
    """Test Difficulty enum."""

    def test_difficulty_values(self):
        """Test Difficulty enum has expected values."""
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.MEDIUM.value == "medium"
        assert Difficulty.HARD.value == "hard"

    def test_difficulty_is_string_enum(self):
        """Test Difficulty is a string enum."""
        assert issubclass(Difficulty, str)


class TestLanguage:
    """Test Language enum."""

    def test_language_values(self):
        """Test Language enum has expected values."""
        assert Language.PYTHON.value == "python"
        assert Language.C.value == "c"
        assert Language.CPP.value == "cpp"
        assert Language.JAVA.value == "java"
        assert Language.JAVASCRIPT.value == "javascript"
        assert Language.GOLANG.value == "golang"

    def test_language_is_string_enum(self):
        """Test Language is a string enum."""
        assert issubclass(Language, str)


class TestSubmissionStatus:
    """Test SubmissionStatus enum."""

    def test_status_values(self):
        """Test SubmissionStatus enum has expected values."""
        assert SubmissionStatus.PENDING.value == "pending"
        assert SubmissionStatus.JUDGING.value == "judging"
        assert SubmissionStatus.FINISHED.value == "finished"

    def test_status_is_string_enum(self):
        """Test SubmissionStatus is a string enum."""
        assert issubclass(SubmissionStatus, str)


class TestSubmissionResult:
    """Test SubmissionResult enum."""

    def test_result_values(self):
        """Test SubmissionResult enum has expected values."""
        assert SubmissionResult.AC.value == "ac"
        assert SubmissionResult.WA.value == "wa"
        assert SubmissionResult.TLE.value == "tle"
        assert SubmissionResult.MLE.value == "mle"
        assert SubmissionResult.CE.value == "ce"
        assert SubmissionResult.RE.value == "re"
        assert SubmissionResult.SE.value == "se"

    def test_result_is_string_enum(self):
        """Test SubmissionResult is a string enum."""
        assert issubclass(SubmissionResult, str)
