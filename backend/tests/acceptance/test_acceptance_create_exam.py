import pytest
import jwt
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when
from datetime import date, datetime, timedelta
from main import app
import os


# ============================================================================
# JWT CONFIGURATION (MUST MATCH main.py)
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"


def create_test_token(user_id: int = 1) -> str:
    """Create a valid JWT token for testing"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_auth_headers(user_id: int = 1) -> dict:
    """Get Authorization headers with valid JWT token"""
    token = create_test_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# TEST CLIENT & CONTEXT FIXTURES
# ============================================================================

@pytest.fixture
def client() -> TestClient:
    """FastAPI test client for exam API."""
    return TestClient(app)


class ExamContext:
    """Shared context for BDD steps"""
    def __init__(self):
        self.last_response = None
        self.last_exam_id = None
        self.created_exams = []
        self.mock_exams = {}
        self.auth_headers = get_auth_headers(user_id=1)


@pytest.fixture
def context() -> ExamContext:
    return ExamContext()


@pytest.fixture
def auth_headers() -> dict:
    """Get valid auth headers for test requests"""
    return get_auth_headers(user_id=1)


@pytest.fixture
def mock_exam_service():
    """Mock the ExamService to avoid database calls"""
    with patch('src.routers.exams.service') as mock_service:
        yield mock_service


@pytest.fixture
def future_date():
    """Get a date 30 days in the future"""
    return (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")


@pytest.fixture
def sample_exam():
    """Sample exam data"""
    return {
        "id": 1,
        "title": "Math Final",
        "exam_code": "MATH101",
        "course": "1",
        "date": "2026-06-15",
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled",
        "created_by": 1
    }


# ============================================================================
# LOAD BDD SCENARIOS
# ============================================================================

scenarios("../feature/create_exam.feature")


# ============================================================================
# BACKGROUND STEPS (BDD)
# ============================================================================

@bdd_given("the API is running")
def api_is_running(client: TestClient, context: ExamContext):
    """Ensure API and test client are ready."""
    context.last_response = None
    context.mock_exams = {}
    context.auth_headers = get_auth_headers(user_id=1)
    return {"client": client}


@bdd_given("the exam database is empty")
def exam_database_is_empty(context: ExamContext):
    """Clear the mock exam database."""
    context.mock_exams = {}


# ============================================================================
# HAPPY PATH: CREATE EXAM (BDD)
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
):
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
            "created_by": 1,
            **payload
        }
        mock_add.return_value = exam_data
        
        # Use auth headers to bypass JWT validation
        response = client.post("/exams", json=payload, headers=context.auth_headers)
        context.last_response = response

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
def check_status_code(context: ExamContext, code: int):
    """Verify the response status code."""
    assert context.last_response is not None
    assert context.last_response.status_code == code, \
        f"Expected {code}, got {context.last_response.status_code}: {context.last_response.text}"


@bdd_then(parsers.parse("I receive status code {code1:d} or {code2:d}"))
def check_status_code_or(context: ExamContext, code1: int, code2: int):
    """Verify the response status code is one of two values."""
    assert context.last_response is not None
    assert context.last_response.status_code in (code1, code2), \
        f"Expected {code1} or {code2}, got {context.last_response.status_code}"


@bdd_then(parsers.parse('the exam is created with title "{title}"'))
def check_exam_title(context: ExamContext, title: str):
    """Verify the created exam has the expected title."""
    assert context.last_response is not None
    assert context.last_response.status_code == 201
    data = context.last_response.json()
    assert data["title"] == title


@bdd_then(parsers.parse('the exam has exam_code "{exam_code}"'))
def check_exam_code(context: ExamContext, exam_code: str):
    """Verify the exam has the expected exam_code."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data["exam_code"] == exam_code


@bdd_then(parsers.parse('the exam is scheduled for "{date}"'))
def check_exam_date(context: ExamContext, date: str):
    """Verify the exam is scheduled for the expected date."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data["date"] == date


@bdd_then(parsers.parse('the exam time is from "{start_time}" to "{end_time}"'))
def check_exam_time(context: ExamContext, start_time: str, end_time: str):
    """Verify the exam has the expected start and end times."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data["start_time"] == start_time
    assert data["end_time"] == end_time


# ============================================================================
# HAPPY PATH: GET EXAMS (BDD)
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
):
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
        "created_by": 1
    }
    context.mock_exams[exam_code] = exam_data
    context.created_exams.append(exam_data)
    context.last_exam_id = exam_data["id"]


@bdd_when("I request all exams")
def request_all_exams(client: TestClient, context: ExamContext):
    """Get all exams from the API."""
    with patch("src.routers.exams.service.get_teacher_exams") as mock_get_all:
        mock_get_all.return_value = list(context.mock_exams.values())
        
        response = client.get("/exams", headers=context.auth_headers)
        context.last_response = response


@bdd_then("the response is a list")
def check_response_is_list(context: ExamContext):
    """Verify the response is a list."""
    assert context.last_response is not None
    assert isinstance(context.last_response.json(), list)


@bdd_then(parsers.parse('the list contains an exam with title "{title}"'))
def check_list_contains_title(context: ExamContext, title: str):
    """Verify the list contains an exam with the expected title."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert any(exam.get("title") == title for exam in data)


@bdd_when("I get the exam by ID")
def get_exam_by_id(client: TestClient, context: ExamContext):
    """Get a specific exam by ID."""
    if context.last_exam_id is None:
        pytest.skip("Exam was not created in setup phase")
    
    exam_to_return = next(
        (e for e in context.created_exams if e["id"] == context.last_exam_id),
        None
    )
    
    with patch("src.routers.exams.service.get_exam") as mock_get:
        mock_get.return_value = exam_to_return
        response = client.get(f"/exams/{context.last_exam_id}", headers=context.auth_headers)
        context.last_response = response


@bdd_then(parsers.parse('the response contains title "{title}"'))
def check_response_title(context: ExamContext, title: str):
    """Verify response contains the expected title."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data.get("title") == title


@bdd_then(parsers.parse('the response contains exam_code "{exam_code}"'))
def check_response_exam_code(context: ExamContext, exam_code: str):
    """Verify response contains the expected exam_code."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data.get("exam_code") == exam_code


# ============================================================================
# VALIDATION FAILURES: MISSING FIELDS (BDD)
# ============================================================================

@bdd_when("I create an exam with missing title")
def create_exam_missing_title(client: TestClient, context: ExamContext):
    """Try to create exam without title."""
    payload = {
        "exam_code": "SE123",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00",
    }
    
    response = client.post("/exams", json=payload, headers=context.auth_headers)
    context.last_response = response


@bdd_when("I create an exam with missing exam_code")
def create_exam_missing_exam_code(client: TestClient, context: ExamContext):
    """Try to create exam without exam_code."""
    payload = {
        "title": "Test Exam",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00",
    }
    
    response = client.post("/exams", json=payload, headers=context.auth_headers)
    context.last_response = response


# ============================================================================
# VALIDATION FAILURES: FORMAT ERRORS (BDD)
# ============================================================================

@bdd_when(parsers.parse('I create an exam with invalid date format "{date_format}"'))
def create_exam_invalid_date(client: TestClient, context: ExamContext, date_format: str):
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
    
    response = client.post("/exams", json=payload, headers=context.auth_headers)
    context.last_response = response


@bdd_when(parsers.parse('I create an exam with invalid time format "{time_format}"'))
def create_exam_invalid_time(client: TestClient, context: ExamContext, time_format: str):
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
    
    response = client.post("/exams", json=payload, headers=context.auth_headers)
    context.last_response = response


# ============================================================================
# VALIDATION FAILURES: BUSINESS LOGIC (BDD)
# ============================================================================

@bdd_when(parsers.parse('I create an exam with past date "{date}"'))
def create_exam_past_date(client: TestClient, context: ExamContext, date: str):
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
    
    response = client.post("/exams", json=payload, headers=context.auth_headers)
    context.last_response = response


@bdd_when(parsers.parse('I create an exam with start_time "{start_time}" and end_time "{end_time}"'))
def create_exam_end_before_start(
    client: TestClient, context: ExamContext, start_time: str, end_time: str
):
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
    
    response = client.post("/exams", json=payload, headers=context.auth_headers)
    context.last_response = response


@bdd_then(parsers.parse('the error message contains "{expected_message}"'))
def check_error_message(context: ExamContext, expected_message: str):
    """Verify error message contains expected text."""
    assert context.last_response is not None
    response_data = context.last_response.json()
    
    error_detail = response_data.get("detail", "")
    if isinstance(error_detail, list):
        error_text = str(error_detail)
    else:
        error_text = str(error_detail)
    
    assert expected_message.lower() in error_text.lower(), \
        f"Expected '{expected_message}' in error: {error_text}"


# ============================================================================
# CONFLICTS & UNIQUENESS (BDD)
# ============================================================================

@bdd_when(parsers.parse('I try to create an exam with duplicate code "{exam_code}"'))
def create_exam_duplicate_code(client: TestClient, context: ExamContext, exam_code: str):
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
        response = client.post("/exams", json=payload, headers=context.auth_headers)
        context.last_response = response


@bdd_when(
    parsers.parse('I create an exam with overlapping time on "{date}" from "{start_time}" to "{end_time}"')
)
def create_exam_scheduling_conflict(
    client: TestClient, context: ExamContext, date: str, start_time: str, end_time: str
):
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
        response = client.post("/exams", json=payload, headers=context.auth_headers)
        context.last_response = response


# ============================================================================
# NOT FOUND SCENARIOS (BDD)
# ============================================================================

@bdd_when(parsers.parse('I request an exam with ID "{exam_id}"'))
def request_exam_by_nonexistent_id(client: TestClient, context: ExamContext, exam_id: str):
    """Request an exam with a non-existent ID."""
    with patch("src.routers.exams.service.get_exam") as mock_get:
        mock_get.return_value = None
        response = client.get(f"/exams/{exam_id}", headers=context.auth_headers)
        context.last_response = response
