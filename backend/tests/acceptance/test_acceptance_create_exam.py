from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when

from main import app


# --- Test client fixture -------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client for exam API."""
    return TestClient(app)


# --- Shared context for BDD steps ----------------------------------------


class ExamContext:
    def __init__(self) -> None:
        self.last_response = None  # type: ignore[assignment]
        self.last_exam_id = None
        self.created_exams = []  # type: ignore[assignment]
        self.mock_exams: Dict[str, Any] = {}  # Store mocked exams


@pytest.fixture
def context() -> ExamContext:
    return ExamContext()


# --- Load BDD scenarios from feature file --------------------------------


scenarios("../feature/create_exam.feature")


# ============================================================================
# BACKGROUND STEPS
# ============================================================================


@bdd_given("the API is running")
def api_is_running(client: TestClient, context: ExamContext) -> Dict[str, Any]:
    """Ensure API and test client are ready."""
    context.last_response = None
    context.mock_exams = {}
    return {"client": client}


@bdd_given("the exam database is empty")
def exam_database_is_empty(client: TestClient, context: ExamContext) -> None:
    """Clear the mock exam database."""
    context.mock_exams = {}


# ============================================================================
# HAPPY PATH: CREATE EXAM
# ============================================================================


@bdd_when(
    parsers.parse(
        'I create an exam with title "{title}" and code "{exam_code}" on "{date}" from "{start_time}" to "{end_time}"'
    )
)
def create_exam_with_details(
    client: TestClient,
    context: ExamContext,
    title: str,
    exam_code: str,
    date: str,
    start_time: str,
    end_time: str,
) -> None:
    """BDD When step: Create an exam with provided details."""
    payload = {
        "title": title,
        "exam_code": exam_code,
        "course": "1",
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "status": "scheduled",
    }
    
    # Mock ExamService.add_exam at the router level
    with patch("src.routers.exams.service.add_exam") as mock_add:
        exam_data = {
            "id": len(context.mock_exams) + 1,
            **payload
        }
        mock_add.return_value = exam_data
        
        response = client.post("/exams", json=payload)
        context.last_response = response

        # DEBUG: Print full response details on failure
        if response.status_code != 201:
            print(f"\n❌ FAILED TO CREATE EXAM")
            print(f"Status Code: {response.status_code}")
            print(f"Payload: {payload}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response Text: {response.text}")

        if response.status_code == 201:
            data = response.json()
            context.last_exam_id = data.get("id")
            context.created_exams.append(data)
            context.mock_exams[exam_code] = data


@bdd_then(parsers.parse("I receive status code {code:d}"))
def check_status_code(context: ExamContext, code: int) -> None:
    """Verify the response status code."""
    assert context.last_response is not None
    assert context.last_response.status_code == code


@bdd_then(parsers.parse("I receive status code {code1:d} or {code2:d}"))
def check_status_code_or(context: ExamContext, code1: int, code2: int) -> None:
    """Verify the response status code is one of two values."""
    assert context.last_response is not None
    assert context.last_response.status_code in (code1, code2)


@bdd_then(parsers.parse('the exam is created with title "{title}"'))
def check_exam_title(context: ExamContext, title: str) -> None:
    """Verify the created exam has the expected title."""
    assert context.last_response is not None
    assert context.last_response.status_code == 201
    data = context.last_response.json()
    assert data["title"] == title


@bdd_then(parsers.parse('the exam has exam_code "{exam_code}"'))
def check_exam_code(context: ExamContext, exam_code: str) -> None:
    """Verify the exam has the expected exam_code."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data["exam_code"] == exam_code


@bdd_then(parsers.parse('the exam is scheduled for "{date}"'))
def check_exam_date(context: ExamContext, date: str) -> None:
    """Verify the exam is scheduled for the expected date."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data["date"] == date


@bdd_then(parsers.parse('the exam time is from "{start_time}" to "{end_time}"'))
def check_exam_time(context: ExamContext, start_time: str, end_time: str) -> None:
    """Verify the exam has the expected start and end times."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data["start_time"] == start_time
    assert data["end_time"] == end_time


# ============================================================================
# HAPPY PATH: GET EXAMS
# ============================================================================


@bdd_given(
    parsers.parse(
        'an exam "{title}" with code "{exam_code}" on "{date}" from "{start_time}" to "{end_time}" exists'
    )
)
def create_existing_exam(
    client: TestClient,
    context: ExamContext,
    title: str,
    exam_code: str,
    date: str,
    start_time: str,
    end_time: str,
) -> None:
    """Create a mock exam for test setup."""
    exam_data = {
        "id": len(context.mock_exams) + 1,
        "title": title,
        "exam_code": exam_code,
        "course": "1",
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "status": "scheduled",
    }
    context.mock_exams[exam_code] = exam_data
    context.created_exams.append(exam_data)
    context.last_exam_id = exam_data["id"]


@bdd_when("I request all exams")
def request_all_exams(client: TestClient, context: ExamContext) -> None:
    """Get all exams from the API."""
    with patch("src.routers.exams.service.get_all_exams") as mock_get_all:
        mock_get_all.return_value = list(context.mock_exams.values())
        response = client.get("/exams")
        context.last_response = response


@bdd_then("the response is a list")
def check_response_is_list(context: ExamContext) -> None:
    """Verify the response is a list."""
    assert context.last_response is not None
    assert isinstance(context.last_response.json(), list)


@bdd_then(parsers.parse('the list contains an exam with title "{title}"'))
def check_list_contains_title(context: ExamContext, title: str) -> None:
    """Verify the list contains an exam with the expected title."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert any(exam.get("title") == title for exam in data)


@bdd_when("I get the exam by ID")
def get_exam_by_id(client: TestClient, context: ExamContext) -> None:
    """Get a specific exam by ID."""
    if context.last_exam_id is None:
        pytest.skip("Exam was not created in setup phase")
    
    exam_to_return = next(
        (e for e in context.created_exams if e["id"] == context.last_exam_id),
        None
    )
    
    with patch("src.routers.exams.service.get_exam") as mock_get:
        mock_get.return_value = exam_to_return
        response = client.get(f"/exams/{context.last_exam_id}")
        context.last_response = response


@bdd_then(parsers.parse('the response contains title "{title}"'))
def check_response_title(context: ExamContext, title: str) -> None:
    """Verify response contains the expected title."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data.get("title") == title


@bdd_then(parsers.parse('the response contains exam_code "{exam_code}"'))
def check_response_exam_code(context: ExamContext, exam_code: str) -> None:
    """Verify response contains the expected exam_code."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data.get("exam_code") == exam_code


# ============================================================================
# VALIDATION FAILURES: MISSING FIELDS
# ============================================================================


@bdd_when("I create an exam with missing title")
def create_exam_missing_title(client: TestClient, context: ExamContext) -> None:
    """Try to create exam without title."""
    payload = {
        "exam_code": "SE123",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00",
    }
    
    response = client.post("/exams", json=payload)
    context.last_response = response


@bdd_when("I create an exam with missing exam_code")
def create_exam_missing_exam_code(client: TestClient, context: ExamContext) -> None:
    """Try to create exam without exam_code."""
    payload = {
        "title": "Test Exam",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00",
    }
    
    response = client.post("/exams", json=payload)
    context.last_response = response


# ============================================================================
# VALIDATION FAILURES: FORMAT ERRORS
# ============================================================================


@bdd_when(parsers.parse('I create an exam with invalid date format "{date_format}"'))
def create_exam_invalid_date(client: TestClient, context: ExamContext, date_format: str) -> None:
    """Try to create exam with invalid date format."""
    payload = {
        "title": "Test Exam",
        "exam_code": "TEST01",
        "course": "1",
        "date": date_format,
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled",
    }
    
    response = client.post("/exams", json=payload)
    context.last_response = response


@bdd_when(parsers.parse('I create an exam with invalid time format "{time_format}"'))
def create_exam_invalid_time(client: TestClient, context: ExamContext, time_format: str) -> None:
    """Try to create exam with invalid time format."""
    payload = {
        "title": "Test Invalid Time",
        "exam_code": "SE124",
        "course": "1",
        "date": "2026-01-14",
        "start_time": time_format,
        "end_time": "11:00",
        "status": "scheduled",
    }
    
    response = client.post("/exams", json=payload)
    context.last_response = response


# ============================================================================
# VALIDATION FAILURES: BUSINESS LOGIC
# ============================================================================


@bdd_when(parsers.parse('I create an exam with past date "{date}"'))
def create_exam_past_date(client: TestClient, context: ExamContext, date: str) -> None:
    """Try to create exam with a past date."""
    payload = {
        "title": "Past Date Exam",
        "exam_code": "SE125",
        "course": "1",
        "date": date,
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled",
    }
    
    response = client.post("/exams", json=payload)
    context.last_response = response


@bdd_when(parsers.parse('I create an exam with start_time "{start_time}" and end_time "{end_time}"'))
def create_exam_end_before_start(
    client: TestClient, context: ExamContext, start_time: str, end_time: str
) -> None:
    """Try to create exam where end time is before start time."""
    payload = {
        "title": "End Before Start Exam",
        "exam_code": "SE126",
        "course": "1",
        "date": "2026-01-14",
        "start_time": start_time,
        "end_time": end_time,
        "status": "scheduled",
    }
    
    response = client.post("/exams", json=payload)
    context.last_response = response


@bdd_then(parsers.parse('the error message contains "{expected_message}"'))
def check_error_message(context: ExamContext, expected_message: str) -> None:
    """Verify error message contains expected text."""
    assert context.last_response is not None
    response_data = context.last_response.json()

    error_detail = response_data.get("detail", "")
    if isinstance(error_detail, list):
        error_text = str(error_detail)
    else:
        error_text = str(error_detail)

    assert expected_message.lower() in error_text.lower(), f"Expected '{expected_message}' in error: {error_text}"


# ============================================================================
# CONFLICTS & UNIQUENESS
# ============================================================================


@bdd_when(parsers.parse('I try to create an exam with duplicate code "{exam_code}"'))
def create_exam_duplicate_code(client: TestClient, context: ExamContext, exam_code: str) -> None:
    """Try to create exam with a code that already exists."""
    payload = {
        "title": "Exam Two",
        "exam_code": exam_code,
        "course": "1",
        "date": "2026-03-11",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled",
    }
    
    with patch("src.routers.exams.service.add_exam") as mock_add:
        mock_add.side_effect = ValueError(f"Exam code '{exam_code}' already exists")
        response = client.post("/exams", json=payload)
        context.last_response = response


@bdd_when(
    parsers.parse('I create an exam with overlapping time on "{date}" from "{start_time}" to "{end_time}"')
)
def create_exam_scheduling_conflict(
    client: TestClient, context: ExamContext, date: str, start_time: str, end_time: str
) -> None:
    """Try to create exam that conflicts with existing exam."""
    payload = {
        "title": "Conflicting Exam",
        "exam_code": "CONF001",
        "course": "1",
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "status": "scheduled",
    }
    
    with patch("src.routers.exams.service.add_exam") as mock_add:
        mock_add.side_effect = ValueError("Scheduling conflict detected")
        response = client.post("/exams", json=payload)
        context.last_response = response


# ============================================================================
# NOT FOUND SCENARIOS
# ============================================================================


@bdd_when(parsers.parse('I request an exam with ID "{exam_id}"'))
def request_exam_by_nonexistent_id(client: TestClient, context: ExamContext, exam_id: str) -> None:
    """Request an exam with a non-existent ID."""
    with patch("src.routers.exams.service.get_exam") as mock_get:
        mock_get.return_value = None
        response = client.get(f"/exams/{exam_id}")
        context.last_response = response