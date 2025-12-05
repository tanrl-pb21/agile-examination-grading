# tests/acceptance/test_mcq_grading_story.py

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

# Load feature file
scenarios('../feature/mcq_grading.feature')

# Fixtures
@pytest.fixture
def mock_db_cursor():
    """Mock database cursor"""
    cursor = Mock()
    return cursor

@pytest.fixture
def exam_context():
    """Context to share data between steps"""
    return {
        'exam_id': 1,
        'user_id': 101,
        'question_id': 5,
        'selected_option': None,
        'correct_option': 2,
        'marks': 5,
        'grading_result': None
    }

# Given steps
@given("a student is taking an MCQ exam")
def student_taking_exam(exam_context):
    """Student has started the exam"""
    assert exam_context['exam_id'] is not None
    assert exam_context['user_id'] is not None

@given(parsers.parse('an MCQ question worth {marks:d} marks'))
def mcq_question_exists(exam_context, marks):
    """MCQ question with specific marks exists"""
    exam_context['marks'] = marks

@given(parsers.parse('the correct answer is option {option_id:d}'))
def correct_answer_set(exam_context, mock_db_cursor, option_id):
    """Set the correct answer for the question"""
    exam_context['correct_option'] = option_id
    
    # Mock database response for correct option
    mock_db_cursor.fetchone.return_value = {'id': option_id}

# When steps
@when(parsers.parse('the student selects option {option_id:d}'))
def student_selects_option(exam_context, option_id):
    """Student selects an option"""
    exam_context['selected_option'] = option_id

@when("the exam is submitted")
def exam_submitted(exam_context, mock_db_cursor):
    """Process the exam submission and grading"""
    from src.services.take_exam_service import MCQAnswerGrader
    
    grader = MCQAnswerGrader()
    exam_context['grading_result'] = grader.grade(
        selected_option_id=exam_context['selected_option'],
        correct_option_id=exam_context['correct_option'],
        marks=exam_context['marks']
    )

# Then steps
@then(parsers.parse('the student should receive {expected_score:d} marks'))
def verify_score(exam_context, expected_score):
    """Verify the awarded score"""
    actual_score = exam_context['grading_result']['score']
    assert actual_score == expected_score, f"Expected {expected_score} marks, got {actual_score}"

@then('the feedback should be "Correct"')
def verify_correct_feedback(exam_context):
    """Verify correct feedback"""
    feedback = exam_context['grading_result']['feedback']
    assert feedback == "Correct", f"Expected 'Correct', got '{feedback}'"

@then('the feedback should be "Incorrect"')
def verify_incorrect_feedback(exam_context):
    """Verify incorrect feedback"""
    feedback = exam_context['grading_result']['feedback']
    assert feedback == "Incorrect", f"Expected 'Incorrect', got '{feedback}'"

@then("the answer should be marked as correct")
def verify_marked_correct(exam_context):
    """Verify answer is marked correct"""
    is_correct = exam_context['grading_result']['is_correct']
    assert is_correct is True, "Answer should be marked as correct"

@then("the answer should be marked as incorrect")
def verify_marked_incorrect(exam_context):
    """Verify answer is marked incorrect"""
    is_correct = exam_context['grading_result']['is_correct']
    assert is_correct is False, "Answer should be marked as incorrect"