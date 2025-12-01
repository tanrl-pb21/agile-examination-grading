import pytest
from datetime import date, time
from unittest.mock import patch, MagicMock

from src.services.submission_service import SubmissionService


# ============================================================
# PURE FUNCTION TESTS
# ============================================================

class TestPureFunctions:

    def test_calculate_percentage(self):
        svc = SubmissionService()
        assert svc.calculate_percentage(50, 100) == 50
        assert svc.calculate_percentage(None, 100) is None
        assert svc.calculate_percentage(50, 0) is None
        assert svc.calculate_percentage(50, -1) is None

    def test_resolve_status(self):
        svc = SubmissionService()
        assert svc.resolve_status("graded") == "graded"
        assert svc.resolve_status("pending") == "pending"
        assert svc.resolve_status("submitted") == "submitted"
        assert svc.resolve_status(None) == "submitted"
        assert svc.resolve_status("") == "submitted"

    def test_format_date(self):
        svc = SubmissionService()
        assert svc.format_date(date(2025, 1, 2)) == "01/02/2025"
        assert svc.format_date(None) is None

    def test_format_time(self):
        svc = SubmissionService()
        assert svc.format_time(time(12, 30)) == "12:30:00"
        assert svc.format_time(None) is None

    def test_format_submission_id(self):
        svc = SubmissionService()
        assert svc.format_submission_id(10) == "sub10"


# ============================================================
# DB BATCH TOTAL MARKS (mock DB)
# ============================================================

@patch("src.services.submission_service.get_conn")
def test_fetch_total_marks_batch(mock_conn):
    # Fake cursor rows
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        {"exam_id": 1, "total_marks": 100},
        {"exam_id": 2, "total_marks": 80},
    ]

    # Fake connection context
    mock_conn().__enter__().cursor.return_value.__enter__.return_value = cursor

    svc = SubmissionService()
    exam_ids = [1, 2]

    result = svc._fetch_total_marks_batch(exam_ids)

    assert result == {1: 100, 2: 80}
    cursor.execute.assert_called_once()


# ============================================================
# MAIN ORCHESTRATOR: get_student_submissions
# ============================================================

@patch.object(SubmissionService, "_fetch_total_marks_batch")
@patch.object(SubmissionService, "_fetch_submissions")
def test_get_student_submissions(mock_fetch_submissions, mock_total_batch):
    svc = SubmissionService()

    # ---------- Mock _fetch_submissions ----------
    mock_fetch_submissions.return_value = [
        {
            "id": 10,
            "exam_code": 1,
            "submission_date": date(2025, 1, 2),
            "submission_time": time(9, 30),
            "score": 45,
            "score_grade": "B",
            "status": "graded",
            "exam_title": "Math Exam",
            "exam_id": "MATH01",
        },
        {
            "id": 11,
            "exam_code": 2,
            "submission_date": date(2025, 1, 3),
            "submission_time": time(10, 15),
            "score": None,
            "score_grade": None,
            "status": "submitted",
            "exam_title": "Science Exam",
            "exam_id": "SCI01",
        }
    ]

    # ---------- Mock batch marks ----------
    mock_total_batch.return_value = {1: 50, 2: 80}

    result = svc.get_student_submissions(user_id=123)

    # ============================================================
    # VALIDATE OUTPUT
    # ============================================================

    assert len(result) == 2

    # --- First submission ---
    s1 = result[0]
    assert s1["id"] == 10
    assert s1["submission_id"] == "sub10"
    assert s1["exam_title"] == "Math Exam"
    assert s1["exam_id"] == "MATH01"
    assert s1["date"] == "01/02/2025"
    assert s1["time"] == "09:30:00"
    assert s1["score"] == "45/50"
    assert s1["percentage"] == "90.0%"
    assert s1["status"] == "graded"

    # --- Second submission ---
    s2 = result[1]
    assert s2["id"] == 11
    assert s2["submission_id"] == "sub11"
    assert s2["score"] is None
    assert s2["percentage"] is None
    assert s2["status"] == "submitted"

    # Validate calls
    mock_fetch_submissions.assert_called_once_with(123)
    mock_total_batch.assert_called_once_with([1, 2])
