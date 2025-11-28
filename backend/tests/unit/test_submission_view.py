import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime

client = TestClient(app)


def test_view_student_score_valid_submission():
    """Test retrieving a valid submission for grading"""
    submission_id = 21

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


def test_view_student_score_invalid_submissionId():
    """Test retrieving non-existent submission"""
    invalid_submission_id = 9999999

    response = client.get(f"/grading/submission/{invalid_submission_id}")

    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == "Submission not found"


def test_score_range():
    """Test that score is within valid range"""
    response = client.get(f"/grading/submission/21")
    
    assert response.status_code == 200
    data = response.json()
    
    submission = data['submission']
    current_score = submission.get('current_score')
    
    # current_score should be 0-100 or None (not graded)
    assert current_score is None or (0 <= current_score <= 100), \
        f"Score {current_score} is out of valid range"


def test_invalid_submissionId_type():
    """Test with non-integer submission ID"""
    response = client.get(f"/grading/submission/abc")
    
    # FastAPI validates path parameter type
    assert response.status_code == 422  # Validation error



def test_submission_with_pending_status():
    """Test submission that hasn't been graded"""
    response = client.get(f"/grading/submission/26")  # ID of pending submission
    
    assert response.status_code == 200
    data = response.json()
    
    submission = data['submission']
    assert submission['score_grade'] is None or submission['score_grade'] == 'Pending'


def test_submission_response_structure():
    """Test that response has correct structure"""
    response = client.get(f"/grading/submission/21")
    
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
        
def test_questions_list_completeness():
    response = client.get(f"/grading/submission/21")
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

        
def test_overall_feedback_field():
    response = client.get(f"/grading/submission/21")
    assert response.status_code == 200
    data = response.json()

    feedback = data['submission'].get('overall_feedback')
    assert feedback is None or isinstance(feedback, str)
    if feedback:
        assert len(feedback) < 5000  # arbitrary max length limit


def test_submitted_at_timestamp_format():
    response = client.get(f"/grading/submission/21")
    assert response.status_code == 200
    data = response.json()

    submitted_at = data['submission'].get('submitted_at')
    assert isinstance(submitted_at, str)

    # Try parsing it to datetime
    try:
        datetime.fromisoformat(submitted_at)
    except ValueError:
        pytest.fail(f"submitted_at '{submitted_at}' is not valid ISO format")

