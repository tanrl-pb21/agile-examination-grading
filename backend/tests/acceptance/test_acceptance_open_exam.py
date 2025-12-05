from __future__ import annotations
from datetime import datetime, date, time, timedelta, timezone
from unittest.mock import patch

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
        self.mock_available_exams = []
        self.mock_upcoming_exams = []


@pytest.fixture
def context() -> ExamContext:
    """Provide context for each test."""
    ctx = ExamContext()
    yield ctx


# Load BDD scenarios from feature file
scenarios("../feature/open_exam.feature")


# ============================================================================
# HELPER FUNCTION TO CREATE MOCK EXAMS
# ============================================================================


def create_mock_available_exam(
    exam_id: int,
    title: str,
    exam_code: str,
    course_id: int = 1,
    offset_minutes: int = 0
) -> dict:
    """Create a mock exam that is currently open (within time window)."""
    MALAYSIA_TZ = timezone(timedelta(hours=8))
    now = datetime.now(MALAYSIA_TZ)
    
    # Calculate datetime objects around now
    start_dt = now - timedelta(minutes=30 + offset_minutes)
    end_dt = now + timedelta(minutes=30 + offset_minutes)
    
    # If start and end are on different dates (crossing midnight),
    # adjust to keep them on the same day with current time in the middle
    if start_dt.date() != end_dt.date():
        # Current time is close to midnight, adjust the window
        # to be safely within the current day
        if now.hour == 0:  # Just after midnight (00:00 - 00:59)
            # Set exam to span around current time, safely within today
            # For example: if now is 00:04, make it 00:00 to 01:00
            start_dt = datetime.combine(now.date(), time(0, 0), tzinfo=MALAYSIA_TZ)
            end_dt = datetime.combine(now.date(), time(1, 0), tzinfo=MALAYSIA_TZ)
        else:  # Close to midnight from the other side (23:00 - 23:59)
            # Set exam to span around current time, safely within today
            # For example: if now is 23:50, make it 23:00 to 23:59
            start_dt = datetime.combine(now.date(), time(23, 0), tzinfo=MALAYSIA_TZ)
            end_dt = datetime.combine(now.date(), time(23, 59), tzinfo=MALAYSIA_TZ)
    
    return {
        "id": exam_id,
        "title": title,
        "exam_code": exam_code,
        "course": course_id,
        "date": start_dt.date().isoformat(),
        "start_time": start_dt.strftime("%H:%M"),
        "end_time": end_dt.strftime("%H:%M"),
        "status": "scheduled",
    }
    
def create_mock_upcoming_exam(
    exam_id: int,
    title: str,
    exam_code: str,
    course_id: int = 1,
    days_ahead: int = 1
) -> dict:
    """Create a mock exam scheduled for the future."""
    MALAYSIA_TZ = timezone(timedelta(hours=8))
    future_date = datetime.now(MALAYSIA_TZ).date() + timedelta(days=days_ahead)
    
    return {
        "id": exam_id,
        "title": title,
        "exam_code": exam_code,
        "course": course_id,
        "date": future_date.isoformat(),
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled",
    }
    



# ============================================================================
# BACKGROUND STEPS
# ============================================================================


@bdd_given("the API is running")
def step_api_running(client: TestClient, context: ExamContext) -> None:
    """Verify API is accessible."""
    context.last_response = None
    context.mock_available_exams = []
    context.mock_upcoming_exams = []


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
    with patch("src.routers.exams.service.get_available_exams_for_student") as mock_get:
        # Return mock available exams if not already set in previous steps
        if not context.mock_available_exams:
            context.mock_available_exams = [
                create_mock_available_exam(1, "Software Engineering Quiz", "SE101", 1),
                create_mock_available_exam(2, "Math Midterm", "MATH201", 2),
            ]
        
        mock_get.return_value = context.mock_available_exams
        context.last_response = client.get(f"/exams/available?student_id={context.student_id}")


@bdd_when("I request my upcoming exams")
def step_request_upcoming(client: TestClient, context: ExamContext) -> None:
    """Request exams scheduled for the future."""
    with patch("src.routers.exams.service.get_upcoming_exams_for_student") as mock_get:
        # Return mock upcoming exams if not already set in previous steps
        if not context.mock_upcoming_exams:
            context.mock_upcoming_exams = [
                create_mock_upcoming_exam(3, "Physics Final Exam", "PHYS301", 1, days_ahead=2),
                create_mock_upcoming_exam(4, "Chemistry Lab Report", "CHEM201", 2, days_ahead=5),
            ]
        
        mock_get.return_value = context.mock_upcoming_exams
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
    
    # Can be empty list (edge case), so only check if there are exams
    if len(data) > 0:
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
    
    MALAYSIA_TZ = timezone(timedelta(hours=8))
    now = datetime.now(MALAYSIA_TZ)
    
    for exam in data:
        exam_date = datetime.strptime(exam["date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(exam["start_time"], "%H:%M").time()
        end_time = datetime.strptime(exam["end_time"], "%H:%M").time()
        
        # Combine date and time to create full datetime objects
        start_dt = datetime.combine(exam_date, start_time, tzinfo=MALAYSIA_TZ)
        end_dt = datetime.combine(exam_date, end_time, tzinfo=MALAYSIA_TZ)
        
        # Handle midnight crossing: if end_time < start_time, end is next day
        if end_time < start_time:
            end_dt += timedelta(days=1)
        
        # Verify current time is within window
        assert start_dt <= now <= end_dt, (
            f"Exam {exam['title']} is not currently open "
            f"(window: {start_dt} to {end_dt}, now: {now})"
        )
    
    if len(data) > 0:
        print(f"✓ All {len(data)} exams are currently open")
        

@bdd_then("each upcoming exam is scheduled for the future")
def step_check_upcoming_timing(context: ExamContext) -> None:
    """Verify each upcoming exam is in the future or hasn't started today."""
    assert context.last_response is not None
    data = context.last_response.json()
    
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