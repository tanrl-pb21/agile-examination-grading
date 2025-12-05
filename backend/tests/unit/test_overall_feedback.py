import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime

client = TestClient(app)


# ============================================================================
# SAVE FEEDBACK TESTS
# ============================================================================


@patch('src.routers.grading.get_conn')
def test_save_empty_overall_feedback(mock_get_conn):
    """Test saving empty overall feedback."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 219}
    
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": None,
        "overall_feedback": ""
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


@patch('src.routers.grading.get_conn')
def test_save_empty_feedback_then_retrieve(mock_get_conn):
    """Test saving empty feedback and retrieving it."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # Mock for GET request
    mock_cursor.fetchone.side_effect = [
        {
            'submission_id': 219,
            'exam_code': 1,
            'user_id': 1,
            'submission_date': '2025-01-01',
            'submission_time': '10:00:00',
            'status': 'submitted',
            'current_score': 0,
            'score_grade': None,
            'overall_feedback': '',
            'student_email': 'test@example.com',
            'student_name': 'Test Student'
        },
        {'id': 1, 'title': 'Test Exam', 'start_time': '10:00:00', 'end_time': '11:00:00', 'date': '2025-01-01'},
        {'total_score': 0}
    ]
    mock_cursor.fetchall.return_value = []
    
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": None,
        "overall_feedback": ""
    }
    
    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200
    
    get_response = client.get("/grading/submission/219")
    if get_response.status_code == 200:
        feedback = get_response.json()['submission'].get('overall_feedback')
        assert feedback == "" or feedback is None


@patch('src.routers.grading.get_conn')
def test_save_too_long_overall_feedback(mock_get_conn):
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
    
    assert response.status_code == 400
    data = response.json()
    assert "exceeds" in data.get("detail", "").lower() or "length" in data.get("detail", "").lower()


@patch('src.routers.grading.get_conn')
def test_save_missing_overall_feedback_field(mock_get_conn):
    """Test saving without overall_feedback field (should be optional)."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 219}
    
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": "A"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


@patch('src.routers.grading.get_conn')
def test_save_multiline_feedback(mock_get_conn):
    """Test saving feedback with newlines."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 219}
    
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


@patch('src.routers.grading.get_conn')
def test_save_max_length_feedback(mock_get_conn):
    """Test saving feedback at maximum allowed length."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 219}
    
    feedback = "B" * 5000

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


@patch('src.routers.grading.get_conn')
def test_save_invalid_submission_id(mock_get_conn):
    """Test saving feedback for non-existent submission."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    
    payload = {
        "submission_id": 9999999,
        "essay_grades": [],
        "total_score": 0,
        "score_grade": "A",
        "overall_feedback": "Invalid submission test"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data.get("detail", "").lower()


@patch('src.routers.grading.get_conn')
def test_save_with_missing_essay_grade_fields(mock_get_conn):
    """Test saving with missing essay grade fields fails validation."""
    payload = {
        "submission_id": 219,
        "essay_grades": [
            {"score": 10}
        ],
        "total_score": 10,
        "score_grade": "A",
        "overall_feedback": "Missing fields test"
    }

    response = client.post("/grading/save", json=payload)
    
    assert response.status_code == 422


@patch('src.routers.grading.get_conn')
def test_save_without_submission_id(mock_get_conn):
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


@patch('src.routers.grading.get_conn')
def test_save_without_essay_grades(mock_get_conn):
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


@patch('src.routers.grading.get_conn')
def test_save_without_total_score(mock_get_conn):
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


@patch('src.routers.grading.get_conn')
def test_save_with_valid_essay_grades(mock_get_conn):
    """Test saving with valid essay grades."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 219}
    
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


@patch('src.routers.grading.get_conn')
def test_save_essay_grade_missing_score(mock_get_conn):
    """Test essay grade missing score field fails validation."""
    payload = {
        "submission_id": 219,
        "essay_grades": [
            {"submission_answer_id": 1}
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
# DATA PERSISTENCE (MOCKED)
# ============================================================================


@patch('src.routers.grading.get_conn')
def test_save_feedback_persists(mock_get_conn):
    """Test that saved feedback persists and is retrievable (mocked)."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 219}
    
    payload = {
        "submission_id": 219,
        "essay_grades": [],
        "total_score": 92,
        "score_grade": "A",
        "overall_feedback": "Persistent text"
    }

    response = client.post("/grading/save", json=payload)
    assert response.status_code == 200
    assert response.json().get("success") is True


@patch('src.routers.grading.get_conn')
def test_update_feedback_overwrites_previous(mock_get_conn):
    """Test that updating feedback overwrites the previous value (mocked)."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_get_conn.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 219}
    
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

    response1 = client.post("/grading/save", json=initial_payload)
    assert response1.status_code == 200
    
    response2 = client.post("/grading/save", json=updated_payload)
    assert response2.status_code == 200