import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime

client = TestClient(app)


# ============================================================================
# SAVE FEEDBACK TESTS
# ============================================================================


def test_save_empty_overall_feedback():
    """Test saving empty overall feedback."""
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": None,
        "overall_feedback": ""  # empty string feedback
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


def test_save_empty_feedback_then_retrieve():
    """Test saving empty feedback and retrieving it."""
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": None,
        "overall_feedback": ""
    }
    
    # Save feedback
    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200
    
    # Retrieve and verify
    get_response = client.get("/grading/submission/219")
    if get_response.status_code == 200:
        feedback = get_response.json()['submission'].get('overall_feedback')
        assert feedback == "" or feedback is None


def test_save_too_long_overall_feedback():
    """Test saving feedback exceeding maximum length."""
    long_feedback = "A" * 6000

    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": None,
        "overall_feedback": long_feedback
    }

    response = client.post("/grading/save", json=payload)
    
    # Should fail with 400 (bad request) or 422 (validation)
    assert response.status_code in (400, 422)
    data = response.json()
    assert "exceeds" in data.get("detail", "").lower() or "length" in data.get("detail", "").lower()


def test_save_missing_overall_feedback_field():
    """Test saving without overall_feedback field (should be optional)."""
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": "A"
        # overall_feedback omitted
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


def test_save_special_characters_feedback():
    """Test saving feedback with special characters and emojis."""
    feedback = "Great job! 😊👍🏽\nKeep up the good work! 💯"

    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 100,
        "score_grade": "A",
        "overall_feedback": feedback
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200
    
    # Retrieve and verify special characters preserved
    get_response = client.get("/grading/submission/219")
    if get_response.status_code == 200:
        retrieved_feedback = get_response.json()['submission']['overall_feedback']
        assert retrieved_feedback == feedback
        assert "😊" in retrieved_feedback
        assert "💯" in retrieved_feedback


def test_save_multiline_feedback():
    """Test saving feedback with newlines."""
    feedback = "Line 1\nLine 2\nLine 3"

    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 80,
        "score_grade": "B",
        "overall_feedback": feedback
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


def test_save_max_length_feedback():
    """Test saving feedback at maximum allowed length."""
    feedback = "B" * 5000  # exactly at limit

    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 85,
        "score_grade": "B",
        "overall_feedback": feedback
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


# ============================================================================
# VALIDATION FAILURES
# ============================================================================


def test_save_invalid_submission_id():
    """Test saving feedback for non-existent submission."""
    payload = {
        "submission_id": 9999999,  # nonexistent submission ID
        "essay_grades": [],
        "total_score": 0,
        "score_grade": "A",
        "overall_feedback": "Invalid submission test"
    }

    response = client.post("/grading/save", json=payload)
    
    # Should return 404 or 400
    assert response.status_code in (400, 404)
    data = response.json()
    assert "not found" in data.get("detail", "").lower() or "submission" in data.get("detail", "").lower()


def test_save_with_missing_essay_grade_fields():
    """Test saving with missing essay grade fields fails validation."""
    payload = {
        "submission_id": 219,
        "essay_grades": [
            {"score": 10}  # missing submission_answer_id
        ],
        "total_score": 10,
        "score_grade": "A",
        "overall_feedback": "Missing fields test"
    }

    response = client.post("/grading/save", json=payload)
    
    # Pydantic validation should catch this
    assert response.status_code == 422


def test_save_without_submission_id():
    """Test saving without submission_id field fails validation."""
    payload = {
        "essay_grades": [],
        "total_score": 0,
        "score_grade": "A",
        "overall_feedback": "No submission ID"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_save_without_essay_grades():
    """Test saving without essay_grades field fails validation."""
    payload = {
        "submission_id": 219,
        "total_score": 0,
        "score_grade": "A",
        "overall_feedback": "No essay grades"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_save_without_total_score():
    """Test saving without total_score field fails validation."""
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "score_grade": "A",
        "overall_feedback": "No total score"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


# ============================================================================
# ESSAY GRADES VALIDATION
# ============================================================================


def test_save_with_valid_essay_grades():
    """Test saving with valid essay grades."""
    payload = {
        "submission_id": 219,
        "essay_grades": [
            {"submission_answer_id": 1, "score": 25},
            {"submission_answer_id": 2, "score": 25}
        ],
        "total_score": 50,
        "score_grade": "D",
        "overall_feedback": "Valid essay grades"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


def test_save_essay_grade_missing_score():
    """Test essay grade missing score field fails validation."""
    payload = {
        "submission_id": 219,
        "essay_grades": [
            {"submission_answer_id": 1}  # missing score
        ],
        "total_score": 25,
        "score_grade": "D",
        "overall_feedback": "Missing score"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


# ============================================================================
# DATA PERSISTENCE
# ============================================================================


def test_save_feedback_persists():
    """Test that saved feedback persists and is retrievable."""
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 92,
        "score_grade": "A",
        "overall_feedback": "Persistent text"
    }

    # Save
    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200
    
    # Retrieve
    get_response = client.get("/grading/submission/219")
    if get_response.status_code == 200:
        submission = get_response.json()['submission']
        assert submission['overall_feedback'] == "Persistent text"
        assert submission['score_grade'] == "A"


def test_update_feedback_overwrites_previous():
    """Test that updating feedback overwrites the previous value."""
    initial_payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 80,
        "score_grade": "B",
        "overall_feedback": "First feedback"
    }
    
    updated_payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 88,
        "score_grade": "B",
        "overall_feedback": "Updated feedback"
    }

    # Save initial
    response1 = client.post("/grading/save", json=initial_payload)
    assert response1.status_code == 200
    
    # Update with new feedback
    response2 = client.post("/grading/save", json=updated_payload)
    assert response2.status_code == 200
    
    # Retrieve and verify updated
    get_response = client.get("/grading/submission/219")
    if get_response.status_code == 200:
        submission = get_response.json()['submission']
        assert submission['overall_feedback'] == "Updated feedback"
        assert submission['score_grade'] == "B"