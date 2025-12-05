import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app   # adjust if needed


client = TestClient(app)


# ============================================================
# 1. GET /take-exam/duration/{exam_code}
# ============================================================

@patch("src.routers.take_exam.take_exam_service")
def test_get_exam_duration_success(mock_service):
    mock_service.get_exam_duration_by_code.return_value = {"duration": 60}

    resp = client.get("/take-exam/duration/EXAM100")
    assert resp.status_code == 200
    assert resp.json() == {"duration": 60}


@patch("src.routers.take_exam.take_exam_service")
def test_get_exam_duration_value_error(mock_service):
    mock_service.get_exam_duration_by_code.side_effect = ValueError("Exam not found")

    resp = client.get("/take-exam/duration/EXAM404")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Exam not found"


@patch("src.routers.take_exam.take_exam_service")
def test_get_exam_duration_unexpected_error(mock_service):
    mock_service.get_exam_duration_by_code.side_effect = Exception("DB down")

    resp = client.get("/take-exam/duration/EX")
    assert resp.status_code == 500
    assert "DB down" in resp.json()["detail"]


# ============================================================
# 2. GET /take-exam/availability/{exam_code}
# ============================================================

@patch("src.routers.take_exam.take_exam_service")
def test_check_exam_availability_success(mock_service):
    mock_service.check_exam_availability.return_value = {"available": True}

    resp = client.get("/take-exam/availability/EXAM1")
    assert resp.status_code == 200
    assert resp.json() == {"available": True}


@patch("src.routers.take_exam.take_exam_service")
def test_check_exam_availability_value_error(mock_service):
    mock_service.check_exam_availability.side_effect = ValueError("Exam expired")

    resp = client.get("/take-exam/availability/EXAMX")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Exam expired"


@patch("src.routers.take_exam.take_exam_service")
def test_check_exam_availability_unexpected_error(mock_service):
    mock_service.check_exam_availability.side_effect = Exception("Server error")

    resp = client.get("/take-exam/availability/ERR")
    assert resp.status_code == 500
    assert "Server error" in resp.json()["detail"]


# ============================================================
# 3. GET /take-exam/check-submission/{exam_code}/{user_id}
# ============================================================

@patch("src.routers.take_exam.take_exam_service")
def test_check_if_submitted_success(mock_service):
    mock_service.check_if_student_submitted.return_value = True

    resp = client.get("/take-exam/check-submission/EXAM123/5")
    assert resp.status_code == 200
    assert resp.json() == {"submitted": True}


@patch("src.routers.take_exam.take_exam_service")
def test_check_if_submitted_value_error(mock_service):
    mock_service.check_if_student_submitted.side_effect = ValueError("Invalid exam code")

    resp = client.get("/take-exam/check-submission/BAD/5")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Invalid exam code"


@patch("src.routers.take_exam.take_exam_service")
def test_check_if_submitted_unexpected_error(mock_service):
    mock_service.check_if_student_submitted.side_effect = Exception("DB timeout")

    resp = client.get("/take-exam/check-submission/ERR/5")
    assert resp.status_code == 500
    assert "DB timeout" in resp.json()["detail"]


# ============================================================
# 4. GET /take-exam/questions/{exam_code}
# ============================================================

@patch("src.routers.take_exam.take_exam_service")
def test_get_exam_questions_success(mock_service):
    mock_service.get_questions_by_exam_code.return_value = {
        "questions": [{"id": 1, "text": "Q1"}]
    }

    resp = client.get("/take-exam/questions/EXAMQ")
    assert resp.status_code == 200
    assert resp.json()["questions"][0]["text"] == "Q1"


@patch("src.routers.take_exam.take_exam_service")
def test_get_exam_questions_value_error(mock_service):
    mock_service.get_questions_by_exam_code.side_effect = ValueError("No such exam")

    resp = client.get("/take-exam/questions/NOEXAM")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No such exam"


@patch("src.routers.take_exam.take_exam_service")
def test_get_exam_questions_unexpected_error(mock_service):
    mock_service.get_questions_by_exam_code.side_effect = Exception("DB offline")

    resp = client.get("/take-exam/questions/ERR")
    assert resp.status_code == 500
    assert "DB offline" in resp.json()["detail"]


# ============================================================
# 5. POST /take-exam/submit
# ============================================================

payload = {
    "exam_code": "EXAM100",
    "user_id": 3,
    "answers": [{"question_id": 1, "answer": "A"}]
}


@patch("src.routers.take_exam.take_exam_service")
def test_submit_exam_success(mock_service):
    mock_service.validate_submission_time.return_value = True
    mock_service.submit_exam.return_value = {"status": "ok", "score": 10}

    resp = client.post("/take-exam/submit", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@patch("src.routers.take_exam.take_exam_service")
def test_submit_exam_value_error(mock_service):
    mock_service.validate_submission_time.side_effect = ValueError("Late submission")

    resp = client.post("/take-exam/submit", json=payload)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Late submission"


@patch("src.routers.take_exam.take_exam_service")
def test_submit_exam_unexpected_error(mock_service):
    mock_service.validate_submission_time.return_value = True
    mock_service.submit_exam.side_effect = Exception("Internal error")

    resp = client.post("/take-exam/submit", json=payload)
    assert resp.status_code == 500
    assert "Internal error" in resp.json()["detail"]
