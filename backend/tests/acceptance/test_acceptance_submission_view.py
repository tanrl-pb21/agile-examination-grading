from __future__ import annotations

from typing import Any, Dict
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when

from main import app


# --- Test client fixture -------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """Shared FastAPI test client for grading API."""
    return TestClient(app)


# --- Load BDD scenarios from feature file --------------------------------


scenarios("../feature/submission_view.feature")


# --- Shared context for BDD steps ----------------------------------------


class ViewScoreContext:
    def __init__(self) -> None:
        self.last_response = None  # type: ignore[assignment]
        self.retrieved_data = None  # type: ignore[assignment]
        self.submission = None  # type: ignore[assignment]
        self.exam = None  # type: ignore[assignment]
        self.questions = None  # type: ignore[assignment]


@pytest.fixture
def context() -> ViewScoreContext:
    return ViewScoreContext()


# ============================================================================
# BACKGROUND STEPS
# ============================================================================


@bdd_given("the API is running")
def step_api_is_running(client: TestClient, context: ViewScoreContext) -> None:
    """Ensure API and test client are ready."""
    context.last_response = None


@bdd_given("the grading database is populated")
def step_grading_database_populated(client: TestClient) -> None:
    """Ensure database has test data."""
    pass


# ============================================================================
# THEN STEPS: ASSERTIONS (DEFINED EARLY)
# ============================================================================


@bdd_then(parsers.parse("I receive status code {code:d}"))
def step_receive_status_code(context: ViewScoreContext, code: int) -> None:
    """Verify the response status code."""
    assert context.last_response is not None
    assert context.last_response.status_code == code, (
        f"Expected {code}, got {context.last_response.status_code}. "
        f"Response: {context.last_response.text}"
    )


@bdd_then(parsers.parse("I receive status code {code1:d} or {code2:d}"))
def step_receive_status_code_or(context: ViewScoreContext, code1: int, code2: int) -> None:
    """Verify response status is one of two values."""
    assert context.last_response is not None
    assert context.last_response.status_code in (code1, code2), (
        f"Expected {code1} or {code2}, got {context.last_response.status_code}"
    )


@bdd_then(parsers.parse("the response contains submission details"))
def step_response_contains_submission(context: ViewScoreContext) -> None:
    """Verify response contains submission section."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert "submission" in data, "submission key not found in response"
    context.submission = data.get("submission")


@bdd_then(parsers.parse("the response contains exam information"))
def step_response_contains_exam(context: ViewScoreContext) -> None:
    """Verify response contains exam section."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert "exam" in data, "exam key not found in response"
    context.exam = data.get("exam")


@bdd_then(parsers.parse("the response contains questions list"))
def step_response_contains_questions(context: ViewScoreContext) -> None:
    """Verify response contains questions section."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert "questions" in data, "questions key not found in response"
    context.questions = data.get("questions")


@bdd_then(parsers.parse("the submission has ID {expected_id:d}"))
def step_submission_has_id(context: ViewScoreContext, expected_id: int) -> None:
    """Verify submission has correct ID."""
    assert context.submission is not None
    actual_id = context.submission.get("id")
    assert actual_id == expected_id, f"Expected ID {expected_id}, got {actual_id}"


@bdd_then(parsers.parse('the submission has {field_name} field'))
def step_submission_has_field(context: ViewScoreContext, field_name: str) -> None:
    """Verify submission has a specific field."""
    assert context.submission is not None
    assert field_name in context.submission, f"Field '{field_name}' not found in submission"


@bdd_then(parsers.parse("the submission contains all required fields"))
def step_submission_has_all_fields(context: ViewScoreContext) -> None:
    """Verify submission has all required fields."""
    assert context.submission is not None
    required_fields = [
        "id",
        "student_id",
        "student_name",
        "student_email",
        "submitted_at",
        "current_score",
        "score_grade",
        "overall_feedback",
    ]
    for field in required_fields:
        assert field in context.submission, f"Missing required field: {field}"


@bdd_then(parsers.parse("the exam contains all required fields"))
def step_exam_has_all_fields(context: ViewScoreContext) -> None:
    """Verify exam has all required fields."""
    assert context.exam is not None
    required_fields = ["id", "title", "date", "start_time", "end_time"]
    for field in required_fields:
        assert field in context.exam, f"Missing exam field: {field}"


@bdd_then(parsers.parse("the questions contain all required fields"))
def step_questions_have_all_fields(context: ViewScoreContext) -> None:
    """Verify questions have all required fields."""
    assert context.questions is not None
    assert isinstance(context.questions, list)
    if len(context.questions) > 0:
        required_fields = ["id", "question_text", "question_type", "marks", "student_answer"]
        for question in context.questions:
            for field in required_fields:
                assert field in question, f"Missing question field: {field}"


@bdd_then("the response has exactly these keys: submission, exam, questions")
def step_response_has_exact_keys(context: ViewScoreContext) -> None:
    """Verify response has exactly the expected keys."""
    assert context.last_response is not None
    data = context.last_response.json()
    expected_keys = {"submission", "exam", "questions"}
    actual_keys = set(data.keys())
    assert actual_keys == expected_keys, f"Expected {expected_keys}, got {actual_keys}"


@bdd_then("submission is a dictionary")
def step_submission_is_dict(context: ViewScoreContext) -> None:
    """Verify submission is a dictionary."""
    assert context.submission is not None
    assert isinstance(context.submission, dict), "submission is not a dictionary"


@bdd_then("exam is a dictionary")
def step_exam_is_dict(context: ViewScoreContext) -> None:
    """Verify exam is a dictionary."""
    assert context.exam is not None
    assert isinstance(context.exam, dict), "exam is not a dictionary"


@bdd_then("questions is a list")
def step_questions_is_list(context: ViewScoreContext) -> None:
    """Verify questions is a list."""
    assert context.questions is not None
    assert isinstance(context.questions, list), "questions is not a list"


@bdd_then("the current_score is null or between 0 and 100")
def step_current_score_valid_range(context: ViewScoreContext) -> None:
    """Verify current_score is in valid range."""
    assert context.submission is not None
    score = context.submission.get("current_score")
    assert score is None or (0 <= score <= 100), f"Score {score} out of valid range"


@bdd_then("the score_grade is present")
def step_score_grade_present(context: ViewScoreContext) -> None:
    """Verify score_grade field exists."""
    assert context.submission is not None
    assert "score_grade" in context.submission, "score_grade field not found"


@bdd_then(parsers.parse('the score_grade is null or "{expected_value}"'))
def step_score_grade_null_or_value(context: ViewScoreContext, expected_value: str) -> None:
    """Verify score_grade is null or has expected value."""
    assert context.submission is not None
    grade = context.submission.get("score_grade")
    assert grade is None or grade == expected_value, f"Expected null or '{expected_value}', got '{grade}'"


@bdd_then("the overall_feedback is null or a string")
def step_overall_feedback_type(context: ViewScoreContext) -> None:
    """Verify overall_feedback is null or string."""
    assert context.submission is not None
    feedback = context.submission.get("overall_feedback")
    assert feedback is None or isinstance(feedback, str), f"Expected null or string, got {type(feedback)}"


@bdd_then("the overall_feedback length is less than 5000 characters")
def step_overall_feedback_length(context: ViewScoreContext) -> None:
    """Verify overall_feedback length is within limit."""
    assert context.submission is not None
    feedback = context.submission.get("overall_feedback")
    if feedback:
        assert len(feedback) < 5000, f"Feedback length {len(feedback)} exceeds limit"


@bdd_then("the submitted_at is a valid ISO format timestamp")
def step_submitted_at_valid_format(context: ViewScoreContext) -> None:
    """Verify submitted_at is valid ISO format."""
    assert context.submission is not None
    submitted_at = context.submission.get("submitted_at")
    assert isinstance(submitted_at, str), "submitted_at is not a string"
    try:
        datetime.fromisoformat(submitted_at)
    except ValueError:
        pytest.fail(f"submitted_at '{submitted_at}' is not valid ISO format")


@bdd_then("the questions list contains valid question objects")
def step_questions_valid_objects(context: ViewScoreContext) -> None:
    """Verify questions are valid objects."""
    assert context.questions is not None
    assert isinstance(context.questions, list), "questions is not a list"
    if len(context.questions) > 0:
        for question in context.questions:
            assert isinstance(question, dict), "question is not a dictionary"


@bdd_then("each question has id as integer")
def step_question_id_integer(context: ViewScoreContext) -> None:
    """Verify each question has integer ID."""
    assert context.questions is not None
    for question in context.questions:
        assert "id" in question, "question missing id field"
        assert isinstance(question["id"], int), "question id is not integer"


@bdd_then("each question has question_text as string")
def step_question_text_string(context: ViewScoreContext) -> None:
    """Verify each question has string text."""
    assert context.questions is not None
    for question in context.questions:
        assert "question_text" in question, "question missing question_text field"
        assert isinstance(question["question_text"], str), "question_text is not string"


@bdd_then("each question has question_type in valid types")
def step_question_type_valid(context: ViewScoreContext) -> None:
    """Verify each question has valid type."""
    assert context.questions is not None
    valid_types = ["mcq", "essay"]
    for question in context.questions:
        assert "question_type" in question, "question missing question_type field"
        assert question["question_type"] in valid_types, f"Invalid question_type: {question['question_type']}"


@bdd_then("each question has marks as number")
def step_question_marks_number(context: ViewScoreContext) -> None:
    """Verify each question has numeric marks."""
    assert context.questions is not None
    for question in context.questions:
        assert "marks" in question, "question missing marks field"
        assert isinstance(question["marks"], (int, float)), "marks is not a number"


@bdd_then("each question has student_answer field")
def step_question_student_answer(context: ViewScoreContext) -> None:
    """Verify each question has student_answer field."""
    assert context.questions is not None
    for question in context.questions:
        assert "student_answer" in question, "question missing student_answer field"


@bdd_then("all question types are either mcq or essay")
def step_all_question_types_valid(context: ViewScoreContext) -> None:
    """Verify all question types are valid."""
    assert context.questions is not None
    valid_types = ["mcq", "essay"]
    for question in context.questions:
        assert question.get("question_type") in valid_types, (
            f"Invalid question_type: {question.get('question_type')}"
        )


@bdd_then(parsers.parse("all question types are valid mcq or essay types"))
def step_all_question_types_valid_new(context: ViewScoreContext) -> None:
    """Verify all question types are valid."""
    assert context.questions is not None
    valid_types = ["mcq", "essay"]
    for question in context.questions:
        assert question.get("question_type") in valid_types, (
            f"Invalid question_type: {question.get('question_type')}"
        )


@bdd_then("the response contains error detail")
def step_response_contains_error(context: ViewScoreContext) -> None:
    """Verify error response has detail field."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert "detail" in data, "detail field not found in error response"


@bdd_then(parsers.parse('the error message is "{expected_message}"'))
def step_error_message_exact(context: ViewScoreContext, expected_message: str) -> None:
    """Verify error message matches exactly."""
    assert context.last_response is not None
    data = context.last_response.json()
    error_detail = data.get("detail", "")
    assert str(error_detail) == expected_message, f"Expected '{expected_message}', got '{error_detail}'"


@bdd_then(parsers.parse('the error message contains "{expected_text}"'))
def step_error_message_contains(context: ViewScoreContext, expected_text: str) -> None:
    """Verify error message contains text."""
    assert context.last_response is not None
    data = context.last_response.json()
    error_detail = data.get("detail", "")
    # Handle both string and list error formats
    if isinstance(error_detail, list):
        error_text = str(error_detail).lower()
    else:
        error_text = str(error_detail).lower()
    assert expected_text.lower() in error_text, f"Expected '{expected_text}' in error: {error_text}"


@bdd_then("the student_name is a non-empty string")
def step_student_name_valid(context: ViewScoreContext) -> None:
    """Verify student_name is non-empty string."""
    assert context.submission is not None
    name = context.submission.get("student_name")
    assert isinstance(name, str) and len(name) > 0, "student_name is empty or not string"


@bdd_then(parsers.parse('the exam has {field_name} field'))
def step_exam_has_field(context: ViewScoreContext, field_name: str) -> None:
    """Verify exam has specific field."""
    assert context.exam is not None
    assert field_name in context.exam, f"Exam missing field: {field_name}"


@bdd_then("the questions list is not empty")
def step_questions_not_empty(context: ViewScoreContext) -> None:
    """Verify questions list is not empty."""
    assert context.questions is not None
    assert len(context.questions) > 0, "questions list is empty"


@bdd_then("each question has non-empty question_text")
def step_question_text_not_empty(context: ViewScoreContext) -> None:
    """Verify each question has non-empty text."""
    assert context.questions is not None
    for question in context.questions:
        text = question.get("question_text", "")
        assert isinstance(text, str) and len(text) > 0, "question_text is empty"


@bdd_then("each question has marks greater than 0")
def step_question_marks_positive(context: ViewScoreContext) -> None:
    """Verify each question has positive marks."""
    assert context.questions is not None
    for question in context.questions:
        marks = question.get("marks", 0)
        assert marks > 0, f"marks should be > 0, got {marks}"


# ============================================================================
# WHEN STEPS: RETRIEVE SUBMISSION
# ============================================================================


@bdd_when(parsers.parse("I retrieve submission with ID {submission_id:d}"))
def step_retrieve_submission_int(
    client: TestClient, context: ViewScoreContext, submission_id: int
) -> None:
    """Retrieve submission by integer ID."""
    response = client.get(f"/grading/submission/{submission_id}")
    context.last_response = response
    if response.status_code == 200:
        data = response.json()
        context.retrieved_data = data
        context.submission = data.get("submission")
        context.exam = data.get("exam")
        context.questions = data.get("questions")


@bdd_when(parsers.parse('I retrieve submission with ID "{submission_id}"'))
def step_retrieve_submission_str(
    client: TestClient, context: ViewScoreContext, submission_id: str
) -> None:
    """Retrieve submission by string ID (for invalid input testing)."""
    response = client.get(f"/grading/submission/{submission_id}")
    context.last_response = response
    if response.status_code == 200:
        data = response.json()
        context.retrieved_data = data
        context.submission = data.get("submission")
        context.exam = data.get("exam")
        context.questions = data.get("questions")