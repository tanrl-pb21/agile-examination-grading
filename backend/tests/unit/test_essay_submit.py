import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


# ============================================================================
# HAPPY PATH: SUCCESSFUL SUBMISSIONS
# ============================================================================


@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_single_essay(mock_submit, mock_validate):
    """Test submitting a single essay answer"""
    mock_validate.return_value = True
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

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": "This is my essay answer."}
        ]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grade"] == "Pending"
    assert "total_score" in data
    assert "submitted" in data["message"].lower()


@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_multiple_essays(mock_submit, mock_validate):
    """Test submitting multiple essay answers"""
    mock_validate.return_value = True
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

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": "Essay answer 1."},
            {"question_id": 21, "answer": "Essay answer 2."},
        ]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grade"].lower() == "pending"
    assert "submitted" in data["message"].lower()


@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_empty_essay_answer(mock_submit, mock_validate):
    """Test submitting an empty essay answer"""
    mock_validate.return_value = True
    mock_submit.return_value = {
        "submission_id": 1,
        "status": "pending",
        "total_score": 0,
        "max_score": 10,
        "grade": "Pending",
        "message": "Exam submitted successfully. Essays are pending teacher review.",
        "results": [],
    }

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": ""}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"


@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_very_long_essay(mock_submit, mock_validate):
    """Test submitting a very long essay answer"""
    long_text = "Lorem ipsum " * 1000
    
    mock_validate.return_value = True
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

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": long_text}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grade"].lower() == "pending"


@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_no_answers(mock_submit, mock_validate):
    """Test submitting with no answers"""
    mock_validate.return_value = True
    mock_submit.return_value = {
        "submission_id": 1,
        "status": "graded",
        "total_score": 0,
        "max_score": 10,
        "grade": "F",
        "message": "Exam submitted successfully.",
        "results": [],
    }

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": []
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "graded"


# ============================================================================
# VALIDATION FAILURES (422)
# ============================================================================

def test_submit_missing_answer_field():
    """Test validation error when answer field is missing"""
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 7}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_missing_question_id_field():
    """Test validation error when question_id field is missing"""
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_missing_exam_code():
    """Test validation error when exam_code is missing"""
    payload = {
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_missing_user_id():
    """Test validation error when user_id is missing"""
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
    """Test validation error for invalid exam_code type (number instead of string)"""
    payload = {
        "exam_code": 666,
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_invalid_user_id_type():
    """Test validation error for invalid user_id type (string instead of int)"""
    payload = {
        "exam_code": "666",
        "user_id": "invalid",
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 422


def test_submit_invalid_question_id_type():
    """Test validation error for invalid question_id type (string instead of int)"""
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

@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
def test_submit_for_nonexistent_exam(mock_validate):
    """Test error when submitting for non-existent exam"""
    mock_validate.side_effect = ValueError("Exam with code 'NONEXISTENT' not found")

    payload = {
        "exam_code": "NONEXISTENT",
        "user_id": 1,
        "answers": [{"question_id": 7, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 400


@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_for_nonexistent_question(mock_submit, mock_validate):
    """Test error when submitting for non-existent question"""
    mock_validate.return_value = True
    mock_submit.side_effect = ValueError("Question 9999 not found for this exam")

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [{"question_id": 9999, "answer": "Some answer"}]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code in (400, 404)


# ============================================================================
# MIXED SCENARIOS
# ============================================================================

@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_mixed_mcq_and_essay(mock_submit, mock_validate):
    """Test submitting a mix of MCQ and essay answers"""
    mock_validate.return_value = True
    mock_submit.return_value = {
        "submission_id": 1,
        "status": "pending",
        "total_score": 5,
        "max_score": 15,
        "grade": "Pending",
        "message": "Exam submitted successfully. Essays are pending teacher review.",
        "results": [],
    }

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 1, "answer": 2},
            {"question_id": 7, "answer": "Essay answer"},
        ]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 200


@patch('src.routers.take_exam.TakeExamService.validate_submission_time')
@patch('src.routers.take_exam.TakeExamService.submit_exam')
def test_submit_only_mcq_answers(mock_submit, mock_validate):
    """Test submitting only MCQ answers"""
    mock_validate.return_value = True
    mock_submit.return_value = {
        "submission_id": 1,
        "status": "graded",
        "total_score": 10,
        "max_score": 10,
        "grade": "A+",
        "message": "Exam submitted and graded successfully.",
        "results": [],
    }

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 1, "answer": 2},
            {"question_id": 2, "answer": 3},
        ]
    }

    response = client.post("/take-exam/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grade"] == "A+"