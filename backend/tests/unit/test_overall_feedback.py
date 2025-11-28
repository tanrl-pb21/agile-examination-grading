import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime

client = TestClient(app)

def test_save_empty_overall_feedback():
    payload = {
        "submission_id": 21,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": None,
        "overall_feedback": ""  # empty string feedback
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True

    # Confirm retrieving shows empty string or None
    get_response = client.get(f"/grading/submission/21")
    assert get_response.status_code == 200
    feedback = get_response.json()['submission'].get('overall_feedback')
    assert feedback == "" or feedback is None
    
def test_save_too_long_overall_feedback():
    long_feedback = "A" * 6000

    payload = {
        "submission_id": 21,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": None,
        "overall_feedback": long_feedback
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 400  
    data = response.json()
    assert "exceeds maximum length" in data["detail"]

def test_save_missing_overall_feedback_field():
    payload = {
        "submission_id": 21,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": "A"
        # overall_feedback omitted
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True

def test_save_invalid_submission_id():
    payload = {
        "submission_id": 9999999,  # nonexistent submission ID
        "essay_grades": [],
        "total_score": 0,
        "score_grade": "A",
        "overall_feedback": "Invalid submission test"
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == "Submission not found"
    
def test_save_overall_feedback_special_characters():
    feedback = "Great job! 😊👍🏽\nKeep up the good work! 💯"

    payload = {
        "submission_id": 21,
        "essay_grades": [],
        "total_score": 100,
        "score_grade": "A",
        "overall_feedback": feedback
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200

    get_response = client.get(f"/grading/submission/21")
    assert get_response.status_code == 200
    assert get_response.json()['submission']['overall_feedback'] == feedback

def test_save_with_missing_essay_grade_fields():
    payload = {
        "submission_id": 21,
        "essay_grades": [
            {"score": 10}  # missing submission_answer_id
        ],
        "total_score": 10,
        "score_grade": "A",
        "overall_feedback": "Missing fields test"
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 422  # validation error expected
