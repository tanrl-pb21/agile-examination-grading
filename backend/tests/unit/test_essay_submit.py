import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ============================================================================
# HAPPY PATH: SUCCESSFUL SUBMISSIONS
# ============================================================================


def test_submit_single_essay():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": "This is my essay answer."}
        ]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.return_value = {
                "submission_id": 1,
                "status": "pending",
                "total_score": 0,
                "max_score": 10,
                "grade": "Pending",
                "message": "Exam submitted successfully. Essays are pending teacher review.",
                "results": [
                    {
                        "question_id": 7,
                        "type": "essay",
                        "status": "pending",
                        "max_score": 10,
                    }
                ],
            }

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["grade"] == "Pending"
            assert "total_score" in data
            assert "submitted" in data["message"].lower()


def test_submit_multiple_essays():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": "Essay answer 1."},
            {"question_id": 21, "answer": "Essay answer 2."},
        ]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.return_value = {
                "submission_id": 1,
                "status": "pending",
                "total_score": 0,
                "max_score": 20,
                "grade": "Pending",
                "message": "Exam submitted successfully. Essays are pending teacher review.",
                "results": [
                    {
                        "question_id": 7,
                        "type": "essay",
                        "status": "pending",
                        "max_score": 10,
                    },
                    {
                        "question_id": 21,
                        "type": "essay",
                        "status": "pending",
                        "max_score": 10,
                    },
                ],
            }

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["grade"].lower() == "pending"
            assert "submitted" in data["message"].lower()


def test_submit_empty_essay_answer():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": ""}]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.return_value = {
                "submission_id": 1,
                "status": "pending",
                "total_score": 0,
                "max_score": 10,
                "grade": "Pending",
                "message": "Exam submitted successfully. Essays are pending teacher review.",
                "results": [],
            }

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"


def test_submit_very_long_essay():
    long_text = "Lorem ipsum " * 1000

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": long_text}]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.return_value = {
                "submission_id": 1,
                "status": "pending",
                "total_score": 0,
                "max_score": 10,
                "grade": "Pending",
                "message": "Exam submitted successfully. Essays are pending teacher review.",
                "results": [
                    {
                        "question_id": 7,
                        "type": "essay",
                        "status": "pending",
                        "max_score": 10,
                    }
                ],
            }

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["grade"].lower() == "pending"


def test_submit_no_answers():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": []
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.return_value = {
                "submission_id": 1,
                "status": "graded",
                "total_score": 0,
                "max_score": 10,
                "grade": "F",
                "message": "Exam submitted successfully.",
                "results": [],
            }

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "graded"


# ============================================================================
# VALIDATION FAILURES (422)
# ============================================================================

def test_submit_missing_answer_field():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 7}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_missing_question_id_field():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_missing_exam_code():
    payload = {
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_missing_user_id():
    payload = {
        "exam_code": "666",
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


# ============================================================================
# INVALID DATA TYPES (422)
# ============================================================================

def test_submit_invalid_exam_code_type():
    payload = {
        "exam_code": 666,
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_invalid_user_id_type():
    payload = {
        "exam_code": "666",
        "user_id": "invalid",
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_invalid_question_id_type():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": "xxx", "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


# ============================================================================
# BUSINESS LOGIC VALIDATION (400)
# ============================================================================

def test_submit_for_nonexistent_exam():
    payload = {
        "exam_code": "NONEXISTENT",
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.side_effect = ValueError("Exam with code 'NONEXISTENT' not found")

        response = client.post("/take-exam/submit", json=payload)
        assert response.status_code == 400


def test_submit_for_nonexistent_question():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 9999, "answer": "Some answer"}]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.side_effect = ValueError("Question 9999 not found for this exam")

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code in (400, 404)


# ============================================================================
# MIXED SCENARIOS
# ============================================================================

def test_submit_mixed_mcq_and_essay():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 1, "answer": 2},
            {"question_id": 7, "answer": "Essay answer"},
        ]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.return_value = {
                "submission_id": 1,
                "status": "pending",
                "total_score": 5,
                "max_score": 15,
                "grade": "Pending",
                "message": "Exam submitted successfully. Essays are pending teacher review.",
                "results": [],
            }

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code == 200


def test_submit_only_mcq_answers():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 1, "answer": 2},
            {"question_id": 2, "answer": 3},
        ]
    }

    with patch("src.services.take_exam_service.TakeExamService.validate_submission_time") as mock_validate:
        mock_validate.return_value = True

        with patch("src.services.take_exam_service.TakeExamService.submit_exam") as mock_submit:
            mock_submit.return_value = {
                "submission_id": 1,
                "status": "graded",
                "total_score": 10,
                "max_score": 10,
                "grade": "A+",
                "message": "Exam submitted and graded successfully.",
                "results": [],
            }

            response = client.post("/take-exam/submit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["grade"] == "A+"
