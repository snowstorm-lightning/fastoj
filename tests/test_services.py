"""Tests for services."""

import uuid
from unittest.mock import MagicMock

import pytest

from backend.models import Difficulty, Problem
from backend.services.problem_service import ProblemService
from backend.services.submission_service import SubmissionService


class TestProblemService:
    """Test cases for ProblemService."""

    def test_create_problem_service(self):
        """Test creating a ProblemService instance."""
        mock_db = MagicMock()
        service = ProblemService(mock_db)
        assert service.db is not None

    def test_get_public_testcases_returns_list(self):
        """Test getting public testcases returns a list."""
        mock_db = MagicMock()
        problem_id = uuid.uuid4()

        # Create mock testcases
        mock_tc1 = MagicMock()
        mock_tc1.is_hidden = False

        mock_tc2 = MagicMock()
        mock_tc2.is_hidden = True

        # Setup query chain
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_tc1]

        service = ProblemService(mock_db)
        public_testcases = service.get_public_testcases(str(problem_id))

        # Verify it returns a list with the correct testcases
        assert isinstance(public_testcases, list)
        assert len(public_testcases) == 1

    def test_get_all_testcases_returns_list(self):
        """Test getting all testcases returns a list."""
        mock_db = MagicMock()
        problem_id = uuid.uuid4()

        # Create mock testcases
        mock_tc1 = MagicMock()
        mock_tc1.is_hidden = False

        mock_tc2 = MagicMock()
        mock_tc2.is_hidden = True

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_tc1, mock_tc2]

        service = ProblemService(mock_db)
        all_testcases = service.get_all_testcases(str(problem_id))

        assert isinstance(all_testcases, list)
        assert len(all_testcases) == 2


class TestSubmissionService:
    """Test cases for SubmissionService."""

    def test_create_submission_service(self):
        """Test creating a SubmissionService instance."""
        mock_db = MagicMock()
        service = SubmissionService(mock_db)
        assert service.db is not None

    def test_get_submission_for_judge_with_mock(self):
        """Test getting submission for judge worker using mocks."""
        mock_db = MagicMock()
        submission_id = uuid.uuid4()

        # Create mock submission
        mock_submission = MagicMock()
        mock_submission.id = submission_id

        mock_db.query.return_value.filter.return_value.first.return_value = mock_submission

        service = SubmissionService(mock_db)
        result = service.get_submission_for_judge(str(submission_id))

        assert result is not None
        assert result.id == submission_id

    def test_get_submission_for_judge_not_found(self):
        """Test getting non-existent submission returns None."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = SubmissionService(mock_db)
        result = service.get_submission_for_judge(str(uuid.uuid4()))

        assert result is None
