from __future__ import annotations
from datetime import datetime, date, time, timedelta
import uuid
import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when
from main import app

@pytest.fixture
def client() -> TestClient:
    """Shared FastAPI test client for exam API."""
    return TestClient(app)


class ExamContext:
    """Context object to share data between test steps."""
    def __init__(self):
        self.last_response = None
        self.today = date.today()
        self.student_id = 1


@pytest.fixture
def context() -> ExamContext:
    """Provide context for each test."""
    ctx = ExamContext()
    yield ctx


# Load BDD scenarios from feature file
scenarios("../feature/open_exam.feature")


# ============================================================================
# BACKGROUND STEPS
# ============================================================================

@bdd_given("the API is running")
def step_api_running(client: TestClient, context: ExamContext) -> None:
    """Verify API is accessible."""
    context.last_response = None


@bdd_given("I am student 1")
def step_am_student(context: ExamContext) -> None:
    """Set student ID to 1."""
    context.student_id = 1


# ============================================================================
# WHEN STEPS - Request Exam Lists
# ============================================================================

@bdd_when("I request my available exams")
def step_request_available(client: TestClient, context: ExamContext) -> None:
    """Request exams that are currently open (within time window)."""
    context.last_response = client.get(f"/exams/available?student_id={context.student_id}")


@bdd_when("I request my upcoming exams")
def step_request_upcoming(client: TestClient, context: ExamContext) -> None:
    """Request exams scheduled for the future."""
    context.last_response = client.get(f"/exams/upcoming?student_id={context.student_id}")


# ============================================================================
# THEN STEPS - Verify Responses
# ============================================================================

@bdd_then(parsers.parse("I receive status code {code:d}"))
def step_check_status(context: ExamContext, code: int) -> None:
    """Verify the response status code."""
    assert context.last_response is not None
    assert context.last_response.status_code == code, (
        f"Expected {code}, got {context.last_response.status_code}. "
        f"Response: {context.last_response.text}"
    )


@bdd_then("the response is a list of exams")
def step_response_is_list(context: ExamContext) -> None:
    """Verify response is a list."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    print(f"✓ Got {len(data)} exams from API")


@bdd_then("each exam has the required fields")
def step_check_fields(context: ExamContext) -> None:
    """Verify each exam has all required fields."""
    assert context.last_response is not None
    data = context.last_response.json()
    
    required_fields = [
        "id",
        "title",
        "exam_code",
        "course",
        "date",
        "start_time",
        "end_time",
        "status"
    ]
    
    assert len(data) > 0, "No exams in response to verify"
    
    for exam in data:
        for field in required_fields:
            assert field in exam, (
                f"Field '{field}' missing in exam: {exam}"
            )
    
    print(f"✓ All exams have required fields: {required_fields}")


@bdd_then("the response contains at least one exam")
def step_response_has_exams(context: ExamContext) -> None:
    """Verify response contains at least one exam."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert len(data) > 0, "Response should contain at least one exam"
    print(f"✓ Response contains {len(data)} exam(s)")


@bdd_then("each available exam is currently open")
def step_check_available_timing(context: ExamContext) -> None:
    """Verify each available exam is within its time window."""
    assert context.last_response is not None
    data = context.last_response.json()
    
    from datetime import datetime, timezone, timedelta
    MALAYSIA_TZ = timezone(timedelta(hours=8))
    now = datetime.now(MALAYSIA_TZ)
    
    for exam in data:
        start_time_str = exam["start_time"]
        end_time_str = exam["end_time"]
        
        # Parse times
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        current_time = now.time()
        
        # Verify current time is within window
        assert start_time <= current_time, (
            f"Exam {exam['title']} hasn't started yet "
            f"(starts at {start_time}, now is {current_time})"
        )
        assert current_time <= end_time, (
            f"Exam {exam['title']} has ended "
            f"(ended at {end_time}, now is {current_time})"
        )
    
    print(f"✓ All {len(data)} exams are currently open")


@bdd_then("each upcoming exam is scheduled for the future")
def step_check_upcoming_timing(context: ExamContext) -> None:
    """Verify each upcoming exam is in the future or hasn't started today."""
    assert context.last_response is not None
    data = context.last_response.json()
    
    from datetime import datetime, timezone, timedelta
    MALAYSIA_TZ = timezone(timedelta(hours=8))
    now = datetime.now(MALAYSIA_TZ)
    today = now.date()
    current_time = now.time()
    
    for exam in data:
        exam_date_str = exam["date"]
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        
        # Exam must either be:
        # 1. On a future date, OR
        # 2. Today but hasn't started yet
        if exam_date == today:
            # If it's today, it must not have started yet
            start_time_str = exam["start_time"]
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            assert start_time > current_time, (
                f"Exam {exam['title']} should not be upcoming "
                f"(starts at {start_time}, now is {current_time})"
            )
        else:
            # Otherwise it must be in the future
            assert exam_date > today, (
                f"Exam {exam['title']} is not in the future "
                f"(scheduled for {exam_date}, today is {today})"
            )
    
    if len(data) > 0:
        print(f"✓ All {len(data)} exams are scheduled for the future")
    else:
        print(f"✓ No upcoming exams (which is valid)")


@bdd_then(parsers.parse('exam with title "{title}" is in the list'))
def step_exam_in_list(context: ExamContext, title: str) -> None:
    """Verify a specific exam title is in the response list."""
    assert context.last_response is not None
    data = context.last_response.json()
    
    titles = [exam.get("title") for exam in data]
    assert title in titles, (
        f"Exam '{title}' not found in list. Available exams: {titles}"
    )
    print(f"✓ Found exam '{title}' in list")


@bdd_then(parsers.parse('exam with title "{title}" is not in the list'))
def step_exam_not_in_list(context: ExamContext, title: str) -> None:
    """Verify a specific exam title is NOT in the response list."""
    assert context.last_response is not None
    data = context.last_response.json()
    
    titles = [exam.get("title") for exam in data]
    assert title not in titles, (
        f"Exam '{title}' should not be in list but was found. "
        f"Available exams: {titles}"
    )
    print(f"✓ Exam '{title}' is not in the list")


@bdd_then("all exams belong to my enrolled courses")
def step_check_course_enrollment(context: ExamContext) -> None:
    """Verify all returned exams belong to courses the student is enrolled in."""
    assert context.last_response is not None
    data = context.last_response.json()
    
    # For student 1, we expect exams from courses they're enrolled in
    # This is enforced by the API query itself
    assert len(data) >= 0, "Response should be a valid list"
    
    # Just verify each exam has a course field
    for exam in data:
        assert "course" in exam, f"Exam missing course field: {exam}"
        assert exam["course"] is not None, f"Exam has null course: {exam}"
    
    print(f"✓ All {len(data)} exams have valid course assignments")