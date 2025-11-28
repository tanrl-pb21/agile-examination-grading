from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when

from main import app


# --- Test client fixture -------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """
    Shared FastAPI test client for exam API.
    Reset DB before each test to keep tests independent.
    """
    return TestClient(app)


# --- Load BDD scenarios from feature file --------------------------------


scenarios("../feature/essay_submission.feature")


# --- Shared context for BDD steps ----------------------------------------


class EssayContext:
    def __init__(self) -> None:
        self.last_response = None  # type: ignore[assignment]
        self.last_submission_data = None  # type: ignore[assignment]
        self.submitted_answers = []  # type: ignore[assignment]


@pytest.fixture
def context() -> EssayContext:
    return EssayContext()


# ============================================================================
# BACKGROUND STEPS
# ============================================================================


@bdd_given("the API is running")
def step_api_is_running(client: TestClient, context: EssayContext) -> Dict[str, Any]:
    """Ensure API and test client are ready."""
    context.last_response = None
    return {"client": client}


@bdd_given("the exam database is empty")
def step_exam_database_is_empty(client: TestClient) -> None:
    """
    Clear the exam database before test.
    (Assumes your app has a reset mechanism or uses an in-memory DB)
    """
    pass


# ============================================================================
# THEN STEPS: STATUS CODES & ASSERTIONS (MUST BE DEFINED EARLY)
# ============================================================================


@bdd_then(parsers.parse("I receive status code {code:d}"))
def step_receive_status_code(context: EssayContext, code: int) -> None:
    """Verify the response status code."""
    assert context.last_response is not None
    assert context.last_response.status_code == code, (
        f"Expected {code}, got {context.last_response.status_code}. "
        f"Response: {context.last_response.text}"
    )


@bdd_then(parsers.parse("I receive status code {code1:d} or {code2:d}"))
def step_receive_status_code_or(context: EssayContext, code1: int, code2: int) -> None:
    """Verify the response status code is one of two values."""
    assert context.last_response is not None
    assert context.last_response.status_code in (
        code1,
        code2,
    ), f"Expected {code1} or {code2}, got {context.last_response.status_code}"


@bdd_then(parsers.parse('the grade is "{expected_grade}"'))
def step_check_grade(context: EssayContext, expected_grade: str) -> None:
    """Verify the grade status."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data.get("grade") == expected_grade, (
        f"Expected grade '{expected_grade}', got '{data.get('grade')}'"
    )


@bdd_then(parsers.parse('the response contains "{field_name}"'))
def step_response_contains_field(context: EssayContext, field_name: str) -> None:
    """Verify response contains a specific field."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert field_name in data, f"Field '{field_name}' not found in response. Keys: {list(data.keys())}"


@bdd_then(parsers.parse('the message contains "{expected_text}"'))
def step_message_contains(context: EssayContext, expected_text: str) -> None:
    """Verify message contains expected text."""
    assert context.last_response is not None
    data = context.last_response.json()
    message = data.get("message", "").lower()
    assert (
        expected_text.lower() in message
    ), f"Expected '{expected_text}' in message: '{message}'"


@bdd_then("the response is valid")
def step_response_is_valid(context: EssayContext) -> None:
    """Verify response is valid JSON."""
    assert context.last_response is not None
    assert context.last_response.status_code in (200, 201)
    data = context.last_response.json()
    assert isinstance(data, dict)


@bdd_then("the response contains an error detail")
def step_error_detail_exists(context: EssayContext) -> None:
    """Verify error detail is present."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert "detail" in data, f"'detail' field not found in error response: {data}"


@bdd_then(parsers.parse('the error message contains "{expected_text}"'))
def step_error_message_contains(context: EssayContext, expected_text: str) -> None:
    """Verify error message contains expected text."""
    assert context.last_response is not None
    data = context.last_response.json()

    error_detail = data.get("detail", "")
    if isinstance(error_detail, list):
        error_text = str(error_detail)
    else:
        error_text = str(error_detail)

    assert (
        expected_text.lower() in error_text.lower()
    ), f"Expected '{expected_text}' in error: {error_text}"


# ============================================================================
# WHEN STEPS: ESSAY SUBMISSION (single or sequential with And)
# ============================================================================


@bdd_when(
    parsers.parse(
        'I submit an essay answer for exam code "{exam_code}" with question ID {question_id:d} and answer "{answer}"'
    )
)
def step_submit_essay_answer(
    client: TestClient,
    context: EssayContext,
    exam_code: str,
    question_id: int,
    answer: str,
) -> None:
    """Submit a single essay answer (can be used multiple times with And)."""
    payload = {
        "exam_code": exam_code,
        "user_id": 1,
        "answers": [
            {
                "question_id": question_id,
                "answer": answer,
            }
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response
    context.last_submission_data = payload

    if response.status_code == 200:
        data = response.json()
        context.submitted_answers.append(data)


# ============================================================================
# WHEN STEPS: EDGE CASES - EMPTY ANSWER
# ============================================================================


@bdd_when(
    parsers.parse(
        'I submit an essay answer for exam code "{exam_code}" with question ID {question_id:d} and answer ""'
    )
)
def step_submit_empty_essay_answer(
    client: TestClient,
    context: EssayContext,
    exam_code: str,
    question_id: int,
) -> None:
    """Submit an empty essay answer."""
    payload = {
        "exam_code": exam_code,
        "user_id": 1,
        "answers": [
            {
                "question_id": question_id,
                "answer": "",
            }
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response
    context.last_submission_data = payload


# ============================================================================
# WHEN STEPS: EDGE CASES - VERY LONG ESSAY
# ============================================================================


@bdd_when(
    parsers.parse(
        'I submit a very long essay answer for exam code "{exam_code}" with question ID {question_id:d}'
    )
)
def step_submit_very_long_essay(
    client: TestClient, context: EssayContext, exam_code: str, question_id: int
) -> None:
    """Submit a very long essay answer (~11000 characters)."""
    long_text = "Lorem ipsum " * 1000  # ~11000 chars

    payload = {
        "exam_code": exam_code,
        "user_id": 1,
        "answers": [
            {
                "question_id": question_id,
                "answer": long_text,
            }
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response
    context.last_submission_data = payload


# ============================================================================
# WHEN STEPS: EDGE CASES - NO ANSWERS
# ============================================================================


@bdd_when(
    parsers.parse(
        'I submit an exam with code "{exam_code}" and user ID {user_id:d} but with no answers'
    )
)
def step_submit_no_answers(
    client: TestClient, context: EssayContext, exam_code: str, user_id: int
) -> None:
    """Submit an exam with no answers."""
    payload = {
        "exam_code": exam_code,
        "user_id": user_id,
        "answers": [],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response
    context.last_submission_data = payload


# ============================================================================
# WHEN STEPS: VALIDATION FAILURES - MISSING FIELDS
# ============================================================================


@bdd_when(
    parsers.parse(
        'I submit an exam answer for exam code "{exam_code}" with question ID {question_id:d} but without the answer field'
    )
)
def step_submit_missing_answer_field(
    client: TestClient, context: EssayContext, exam_code: str, question_id: int
) -> None:
    """Try to submit without 'answer' field."""
    payload = {
        "exam_code": exam_code,
        "user_id": 1,
        "answers": [
            {"question_id": question_id}  # missing answer field
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I submit an exam answer for exam code "{exam_code}" with answer "{answer}" but without question_id field'
    )
)
def step_submit_missing_question_id_field(
    client: TestClient, context: EssayContext, exam_code: str, answer: str
) -> None:
    """Try to submit without 'question_id' field."""
    payload = {
        "exam_code": exam_code,
        "user_id": 1,
        "answers": [
            {"answer": answer}  # missing question_id field
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I submit an exam answer with user ID {user_id:d} but without exam_code'
    )
)
def step_submit_missing_exam_code(client: TestClient, context: EssayContext, user_id: int) -> None:
    """Try to submit without 'exam_code' field."""
    payload = {
        "user_id": user_id,
        "answers": [
            {"question_id": 7, "answer": "Some answer"}
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I submit an exam answer for exam code "{exam_code}" but without user_id'
    )
)
def step_submit_missing_user_id(client: TestClient, context: EssayContext, exam_code: str) -> None:
    """Try to submit without 'user_id' field."""
    payload = {
        "exam_code": exam_code,
        "answers": [
            {"question_id": 7, "answer": "Some answer"}
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response


# ============================================================================
# WHEN STEPS: VALIDATION FAILURES - INVALID DATA TYPES
# ============================================================================


@bdd_when("I submit an exam answer with exam_code of type number")
def step_submit_invalid_exam_code_type(client: TestClient, context: EssayContext) -> None:
    """Try to submit with exam_code as number instead of string."""
    payload = {
        "exam_code": 666,  # number instead of string
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": "Some answer"}
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response


@bdd_when("I submit an exam answer with user_id of type string")
def step_submit_invalid_user_id_type(client: TestClient, context: EssayContext) -> None:
    """Try to submit with user_id as string instead of number."""
    payload = {
        "exam_code": "666",
        "user_id": "invalid_id",  # string instead of number
        "answers": [
            {"question_id": 7, "answer": "Some answer"}
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response


@bdd_when("I submit an exam answer with question_id of type string")
def step_submit_invalid_question_id_type(client: TestClient, context: EssayContext) -> None:
    """Try to submit with question_id as string instead of number."""
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": "not_a_number", "answer": "Some answer"}
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response


# ============================================================================
# WHEN STEPS: BUSINESS LOGIC VALIDATION - NON-EXISTENT RESOURCES
# ============================================================================


@bdd_when(
    parsers.parse(
        'I submit an essay answer for exam code "{exam_code}" with question ID {question_id:d} and answer "{answer}"'
    )
)
def step_submit_for_nonexistent_resource(
    client: TestClient,
    context: EssayContext,
    exam_code: str,
    question_id: int,
    answer: str,
) -> None:
    """Submit answer for non-existent exam or question."""
    payload = {
        "exam_code": exam_code,
        "user_id": 1,
        "answers": [
            {"question_id": question_id, "answer": answer}
        ],
    }
    response = client.post("/exams/submit", json=payload)
    context.last_response = response