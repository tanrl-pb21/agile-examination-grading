import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def mock_db():
    """Returns a fake DB connection + cursor"""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()

    # get_conn() → conn
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    # default fake DB values
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []

    return mock_conn, mock_cursor


# ------------------------------
# TEST: SUBMIT LATE EXAM
# ------------------------------
def test_submit_late_returns_error():

    mock_conn, mock_cursor = mock_db()

    with (
        patch("src.services.take_exam_service.get_conn", return_value=mock_conn),   # <-- FIXED
        patch("src.services.take_exam_service.ExamRepository.get_exam_by_code") as mock_get_exam,
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate") as mock_validate,
    ):

        mock_get_exam.return_value = {
            "id": 1,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        }

        mock_validate.side_effect = ValueError("Submission rejected: late")

        res = client.post(
            "/take-exam/submit",
            json={"exam_code": "EXAM_LATE", "user_id": 1, "answers": []},
        )

        assert res.status_code == 400
        assert "late" in res.json()["detail"].lower()


# ------------------------------
# TEST: RESUBMIT EXAM
# ------------------------------
def test_resubmit_returns_error():

    mock_conn, mock_cursor = mock_db()

    with (
        patch("src.services.take_exam_service.get_conn", return_value=mock_conn),  # <-- FIXED
        patch("src.services.take_exam_service.ExamRepository.get_exam_by_code") as mock_get_exam,
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate") as mock_validate,
    ):

        mock_get_exam.return_value = {
            "id": 1,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        }

        mock_validate.side_effect = ValueError("You have already submitted this exam")

        res = client.post(
            "/take-exam/submit",
            json={"exam_code": "EXAM_RESUBMIT", "user_id": 1, "answers": []},
        )

        assert res.status_code == 400
        assert "already submitted" in res.json()["detail"].lower()


# ------------------------------
# TEST: SUCCESSFUL SUBMISSION
# ------------------------------
def test_submit_success_fully_mocked():

    mock_conn, mock_cursor = mock_db()

    with (
        patch("src.services.take_exam_service.get_conn", return_value=mock_conn),  # <-- FIXED
        patch("src.services.take_exam_service.ExamRepository.get_exam_by_code") as mock_get_exam,
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate") as mock_validate,
        patch("src.services.take_exam_service.SubmissionRepository.create_submission") as mock_create_sub,
        patch("src.services.take_exam_service.SubmissionRepository.update_submission_final") as mock_update,
        patch("src.services.take_exam_service.QuestionRepository.get_question_by_id") as mock_get_q,
        patch("src.services.take_exam_service.QuestionRepository.get_correct_option_id") as mock_get_correct,
        patch("src.services.take_exam_service.AnswerRepository.create_submission_answer") as mock_create_ans,
        patch("src.services.take_exam_service.AnswerRepository.save_mcq_answer") as mock_save_mcq,
    ):

        mock_get_exam.return_value = {
            "id": 1,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        }
        mock_validate.return_value = True
        mock_create_sub.return_value = 1001
        mock_get_q.return_value = {"id": 1, "question_type": "mcq", "marks": 10}
        mock_get_correct.return_value = 2
        mock_create_ans.return_value = 5001
        mock_save_mcq.return_value = None

        res = client.post(
            "/take-exam/submit",
            json={
                "exam_code": "EXAM_OK",
                "user_id": 1,
                "answers": [{"question_id": 1, "answer": 2}],
            },
        )

        assert res.status_code == 200
        data = res.json()
        assert data["submission_id"] == 1001
        assert data["total_score"] == 10
        assert data["grade"] == "A+"
        assert len(data["results"]) == 1
        assert data["results"][0]["is_correct"] is True


def test_submit_at_end_time_allowed():

    mock_conn, mock_cursor = mock_db()

    # ★ Override fetchone specifically for this test
    mock_cursor.fetchone.return_value = {"id": 555}  # fake submission id

    with (
        patch("src.services.take_exam_service.get_conn", return_value=mock_conn),
        patch("src.services.take_exam_service.ExamRepository.get_exam_by_code") as mock_get_exam,
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate") as mock_validate,
    ):

        mock_get_exam.return_value = {
            "id": 239,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        }

        mock_validate.return_value = True

        res = client.post(
            "/take-exam/submit",
            json={"exam_code": "EXAM_ON_TIME", "user_id": 1, "answers": []},
        )

        assert res.status_code == 200
        assert "submission_id" in res.json()


def test_submit_just_late():

    mock_conn, mock_cursor = mock_db()

    with (
        patch("src.services.take_exam_service.get_conn", return_value=mock_conn),  # <-- FIXED
        patch("src.services.take_exam_service.ExamRepository.get_exam_by_code") as mock_get_exam,
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate") as mock_validate,
    ):

        mock_get_exam.return_value = {
            "id": 1,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        }

        mock_validate.side_effect = ValueError(
            "Submission rejected: The exam ended at 10:00. You are 1 minute(s) late."
        )

        res = client.post(
            "/take-exam/submit",
            json={"exam_code": "EXAM_1_MIN_LATE", "user_id": 1, "answers": []},
        )

        assert res.status_code == 400
        assert "late" in res.json()["detail"].lower()


def test_resubmit_after_late():

    mock_conn, mock_cursor = mock_db()

    with (
        patch("src.services.take_exam_service.get_conn", return_value=mock_conn),  # <-- FIXED
        patch("src.services.take_exam_service.ExamRepository.get_exam_by_code") as mock_get_exam,
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate") as mock_validate,
    ):

        mock_get_exam.return_value = {
            "id": 1,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        }

        mock_validate.side_effect = ValueError(
            "Submission rejected: The exam ended at 10:00. You are 5 minute(s) late."
        )

        for _ in range(2):
            res = client.post(
                "/take-exam/submit",
                json={"exam_code": "EXAM_LATE_RESUBMIT", "user_id": 1, "answers": []},
            )
            assert res.status_code == 400
            assert "late" in res.json()["detail"].lower()


@pytest.mark.parametrize("exam_code", ["EXAM_LATE1", "EXAM_LATE2", "EXAM_LATE3"])
def test_multiple_exams_late(exam_code):

    mock_conn, mock_cursor = mock_db()

    with (
        patch("src.services.take_exam_service.get_conn", return_value=mock_conn),  # <-- FIXED
        patch("src.services.take_exam_service.ExamRepository.get_exam_by_code") as mock_get_exam,
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate") as mock_validate,
    ):

        mock_get_exam.return_value = {
            "id": 99,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        }

        mock_validate.side_effect = ValueError(
            "Submission rejected: Late submissions are not accepted."
        )

        res = client.post(
            "/take-exam/submit",
            json={"exam_code": exam_code, "user_id": 1, "answers": []},
        )

        assert res.status_code == 400
        assert "late" in res.json()["detail"].lower()
