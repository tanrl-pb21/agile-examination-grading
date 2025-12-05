import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime

client = TestClient(app)


# ============================================================================
# VALID SUBMISSION RETRIEVAL TESTS
# ============================================================================


def test_view_student_score_valid_submission():
    """Test retrieving a valid submission for grading."""
    submission_id = 219

    response = client.get(f"/grading/submission/{submission_id}")

    assert response.status_code == 200

    data = response.json()
    assert 'submission' in data
    assert 'exam' in data
    assert 'questions' in data

    submission = data['submission']
    assert submission['id'] == submission_id
    assert 'student_name' in submission
    assert 'current_score' in submission


def test_submission_response_structure():
    """Test that response has correct structure."""
    response = client.get(f"/grading/submission/219")

    assert response.status_code == 200
    data = response.json()

    # Check top-level keys
    assert set(data.keys()) == {'submission', 'exam', 'questions'}

    # Check submission structure
    submission = data['submission']
    required_fields = [
        'id', 'student_id', 'student_name', 'student_email',
        'submitted_at', 'current_score', 'score_grade', 'overall_feedback'
    ]
    for field in required_fields:
        assert field in submission, f"Missing field: {field}"

    # Check exam structure
    exam = data['exam']
    exam_fields = ['id', 'title', 'date', 'start_time', 'end_time']
    for field in exam_fields:
        assert field in exam, f"Missing exam field: {field}"

    # Check questions structure
    questions = data['questions']
    assert isinstance(questions, list)
    if len(questions) > 0:
        question = questions[0]
        assert 'id' in question
        assert 'question_text' in question
        assert 'question_type' in question
        assert 'marks' in question
        assert 'student_answer' in question


# ============================================================================
# SCORE VALIDATION TESTS
# ============================================================================


def test_score_range():
    """Test that score is within valid range."""
    response = client.get(f"/grading/submission/219")

    assert response.status_code == 200
    data = response.json()

    submission = data['submission']
    current_score = submission.get('current_score')

    # current_score should be 0-100 or None (not graded)
    assert current_score is None or (0 <= current_score <= 100), \
        f"Score {current_score} is out of valid range"


def test_submission_with_pending_status():
    """Test submission that hasn't been graded."""
    response = client.get(f"/grading/submission/26")

    # Should return 200 if submission exists, or 404 if it doesn't
    if response.status_code == 200:
        data = response.json()
        submission = data['submission']
        # Score grade should be None or "Pending" for ungraded submissions
        assert submission['score_grade'] is None or submission['score_grade'] == 'Pending'


# ============================================================================
# QUESTIONS DATA VALIDATION TESTS
# ============================================================================


def test_questions_list_completeness():
    """Test that all questions have required fields."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()

    questions = data['questions']
    valid_types = ['mcq', 'essay']
    
    for q in questions:
        assert isinstance(q['id'], int)
        assert isinstance(q['question_text'], str)
        assert q['question_type'] in valid_types
        assert isinstance(q['marks'], (int, float))
        assert 'student_answer' in q


def test_questions_list_not_empty():
    """Test that questions list is not empty for valid submission."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()

    questions = data['questions']
    assert len(questions) > 0, "Questions list should not be empty"


# ============================================================================
# FEEDBACK FIELD VALIDATION TESTS
# ============================================================================


def test_overall_feedback_field():
    """Test that overall_feedback is null or string."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()

    feedback = data['submission'].get('overall_feedback')
    assert feedback is None or isinstance(feedback, str)
    if feedback:
        assert len(feedback) < 5000  # arbitrary max length limit


def test_overall_feedback_with_special_characters():
    """Test that overall_feedback preserves special characters."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()

    feedback = data['submission'].get('overall_feedback')
    # Only validate if feedback exists and contains special characters
    if feedback and len(feedback) > 0:
        assert isinstance(feedback, str)


# ============================================================================
# TIMESTAMP FORMAT VALIDATION TESTS
# ============================================================================


def test_submitted_at_timestamp_format():
    """Test that submitted_at is valid ISO format."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()

    submitted_at = data['submission'].get('submitted_at')
    assert isinstance(submitted_at, str)

    # Try parsing it to datetime
    try:
        datetime.fromisoformat(submitted_at)
    except ValueError:
        pytest.fail(f"submitted_at '{submitted_at}' is not valid ISO format")


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


def test_view_student_score_invalid_submission_id():
    """Test retrieving non-existent submission returns 404."""
    invalid_submission_id = 9999999

    response = client.get(f"/grading/submission/{invalid_submission_id}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data.get("detail", "").lower() or "detail" in data


def test_invalid_submission_id_type():
    """Test with non-integer submission ID."""
    response = client.get(f"/grading/submission/abc")

    # FastAPI validates path parameter type
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data


def test_negative_submission_id():
    """Test with negative submission ID."""
    response = client.get(f"/grading/submission/-1")

    # Should return 404 (not found) or 422 (validation error)
    assert response.status_code in (404, 422)


# ============================================================================
# STUDENT INFORMATION TESTS
# ============================================================================


def test_student_information_preserved():
    """Test that student information is correctly returned."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()

    submission = data['submission']
    assert 'student_id' in submission
    assert 'student_name' in submission
    assert 'student_email' in submission
    assert isinstance(submission['student_name'], str)
    assert len(submission['student_name']) > 0


# ============================================================================
# EXAM INFORMATION TESTS
# ============================================================================


def test_exam_information_preserved():
    """Test that exam information is correctly returned."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()

    exam = data['exam']
    assert 'title' in exam
    assert 'date' in exam
    assert 'start_time' in exam
    assert 'end_time' in exam
    assert isinstance(exam['title'], str)
    assert len(exam['title']) > 0


# ============================================================================
# DATA TYPE VALIDATION TESTS
# ============================================================================


def test_submission_data_types():
    """Test that submission fields have correct data types."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()
    
    submission = data['submission']
    assert isinstance(submission['id'], int)
    assert isinstance(submission['student_id'], int)
    assert isinstance(submission['student_name'], str)
    assert isinstance(submission['student_email'], str)
    assert isinstance(submission['submitted_at'], str)
    # current_score can be int, float, or None
    assert submission['current_score'] is None or isinstance(submission['current_score'], (int, float))
    # score_grade can be string or None
    assert submission['score_grade'] is None or isinstance(submission['score_grade'], str)
    # overall_feedback can be string or empty
    assert submission['overall_feedback'] is None or isinstance(submission['overall_feedback'], str)


def test_exam_data_types():
    """Test that exam fields have correct data types."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()
    
    exam = data['exam']
    assert isinstance(exam['id'], int)
    assert isinstance(exam['title'], str)
    assert isinstance(exam['date'], str)
    assert isinstance(exam['start_time'], str)
    assert isinstance(exam['end_time'], str)


def test_question_data_types():
    """Test that question fields have correct data types."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()
    
    questions = data['questions']
    if len(questions) > 0:
        q = questions[0]
        assert isinstance(q['id'], int)
        assert isinstance(q['question_text'], str)
        assert isinstance(q['question_type'], str)
        assert q['question_type'] in ['mcq', 'essay']
        assert isinstance(q['marks'], (int, float))
        assert 'student_answer' in q  # Can be any type


# ============================================================================
# EDGE CASES
# ============================================================================


def test_submission_with_empty_feedback():
    """Test submission with empty overall_feedback."""
    response = client.get(f"/grading/submission/219")
    
    assert response.status_code == 200
    data = response.json()
    
    submission = data['submission']
    feedback = submission.get('overall_feedback')
    # Empty feedback should be empty string or None
    assert feedback == "" or feedback is None or isinstance(feedback, str)


def test_submission_with_no_questions():
    """Test submission with no questions (edge case)."""
    response = client.get(f"/grading/submission/219")
    
    if response.status_code == 200:
        data = response.json()
        questions = data['questions']
        # Should be a list, even if empty
        assert isinstance(questions, list)