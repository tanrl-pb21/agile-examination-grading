import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)

# Load scenarios from feature file
scenarios('../feature/searchExam.feature')


@pytest.fixture
def context():
    """Context to store test state between steps"""
    return {
        "response": None,
        "student_id": None,
    }


# Mock exam data - Match feature file exactly
MOCK_EXAMS = [
    {
        "id": 1,
        "title": "Midterm Exam",  # Only exam with "Midterm" in title
        "exam_code": "CS101-MID",
        "course": 1,
        "date": "2025-12-15",
        "start_time": "09:00",
        "end_time": "11:00",
        "duration": 120,
        "status": "scheduled",
    },
    {
        "id": 2,
        "title": "Final Exam",  # Only other exam with "Exam" in title
        "exam_code": "CS101-FIN",
        "course": 1,
        "date": "2025-12-20",
        "start_time": "14:00",
        "end_time": "16:00",
        "duration": 120,
        "status": "completed",
    },
    {
        "id": 3,
        "title": "Mathematics Quiz",  # No "Exam" in title
        "exam_code": "MATH101-QZ",
        "course": 2,
        "date": "2025-12-18",
        "start_time": "10:30",
        "end_time": "11:30",
        "duration": 60,
        "status": "scheduled",
    },
    {
        "id": 4,
        "title": "Python Test",  # No "Exam" in title
        "exam_code": "CS102-TST",
        "course": 3,
        "date": "2025-12-22",
        "start_time": "15:00",
        "end_time": "17:00",
        "duration": 120,
        "status": "cancelled",
    },
    {
        "id": 5,
        "title": "Data Structures Test",  # Changed from "Exam" to "Test" - now no "Exam" in title
        "exam_code": "CS201-DSA",
        "course": 4,
        "date": "2025-12-25",
        "start_time": "13:00",
        "end_time": "15:00",
        "duration": 120,
        "status": "scheduled",
    },
]

# Mock student exams (student 1 enrolled in courses 1 only - has 1 scheduled, 1 completed)
MOCK_STUDENT_EXAMS = [
    {**MOCK_EXAMS[0], "course_name": "Computer Science", "course_code": "CS101"},  # scheduled
    {**MOCK_EXAMS[1], "course_name": "Computer Science", "course_code": "CS101"},  # completed
]


# Mock service functions
def mock_search_exams_by_title(search_term):
    if not search_term or not search_term.strip():
        raise ValueError("Search term is required")
    return [e for e in MOCK_EXAMS if search_term.lower() in e["title"].lower()]


def mock_search_exams_by_code(exam_code):
    if not exam_code or not exam_code.strip():
        raise ValueError("Search term is required")
    return [e for e in MOCK_EXAMS if e["exam_code"].lower() == exam_code.lower()]


def mock_search_student_exams_by_course(student_id, course_name):
    if not course_name or not course_name.strip():
        raise ValueError("Course name is required")
    if student_id <= 0:
        raise ValueError("Valid student ID is required")
    return [e for e in MOCK_STUDENT_EXAMS if course_name.lower() in e["course_name"].lower()]


def mock_filter_exams_by_status(status):
    valid_statuses = ["scheduled", "completed", "cancelled"]
    if not status or status.strip().lower() not in valid_statuses:
        raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
    return [e for e in MOCK_EXAMS if e["status"].lower() == status.lower()]


def mock_filter_student_exams_by_status(student_id, status):
    valid_statuses = ["scheduled", "completed", "cancelled"]
    if student_id <= 0:
        raise ValueError("Valid student ID is required")
    if not status or status.strip() not in valid_statuses:
        raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
    return [e for e in MOCK_STUDENT_EXAMS if e["status"].lower() == status.lower()]


# Apply mocks to all tests
@pytest.fixture(autouse=True)
def mock_exam_service():
    """Mock the ExamService methods"""
    with patch('src.services.exams_service.ExamService.search_exams_by_title', side_effect=mock_search_exams_by_title), \
         patch('src.services.exams_service.ExamService.search_exams_by_code', side_effect=mock_search_exams_by_code), \
         patch('src.services.exams_service.ExamService.search_student_exams_by_course', side_effect=mock_search_student_exams_by_course), \
         patch('src.services.exams_service.ExamService.filter_exams_by_status', side_effect=mock_filter_exams_by_status), \
         patch('src.services.exams_service.ExamService.filter_student_exams_by_status', side_effect=mock_filter_student_exams_by_status):
        yield


# ===================== GIVEN STEPS =====================
@given("the following exams exist")
def exams_exist_in_system(context):
    pass  # Already mocked


@given("I am viewing the exam list")
def viewing_exam_list(context):
    pass


@given(parsers.parse("I am a student with ID {student_id:d}"))
def student_with_id(context, student_id):
    context["student_id"] = student_id


@given("I am an instructor")
def user_is_instructor(context):
    pass


# ===================== WHEN STEPS =====================
@when(parsers.parse('I search for exams by title "{title}"'))
def search_exams_by_title(context, title):
    context["response"] = client.get(f"/exams/search/title?title={title}")


@when("I search for exams by title with empty string")
def search_exams_by_title_empty(context):
    context["response"] = client.get("/exams/search/title?title=")


@when(parsers.parse('I search for exams by code "{exam_code}"'))
def search_exams_by_code(context, exam_code):
    context["response"] = client.get(f"/exams/search/code?exam_code={exam_code}")


@when(parsers.parse('I search for exams by code "{exam_code}" case insensitive'))
def search_exams_by_code_case_insensitive(context, exam_code):
    context["response"] = client.get(f"/exams/search/code?exam_code={exam_code}")


@when('I search for exams by code ""')
def search_exams_by_code_empty_string(context):
    context["response"] = client.get("/exams/search/code?exam_code=")


@when(parsers.parse('I search my exams by course "{course_name}"'))
def search_student_exams_by_course(context, course_name):
    student_id = context.get("student_id", 1)
    context["response"] = client.get(
        f"/exams/search/course?student_id={student_id}&course_name={course_name}"
    )


@when('I search my exams by course ""')
def search_student_exams_by_course_empty_string(context):
    student_id = context.get("student_id", 1)
    context["response"] = client.get(
        f"/exams/search/course?student_id={student_id}&course_name="
    )


@when(parsers.parse('I filter exams by status "{status}"'))
def filter_exams_by_status(context, status):
    context["response"] = client.get(f"/exams/filter/status?status={status}")


@when('I filter exams by status ""')
def filter_exams_by_status_empty_string(context):
    context["response"] = client.get("/exams/filter/status?status=")


@when(parsers.parse('I filter exams by invalid status "{status}"'))
def filter_exams_by_invalid_status(context, status):
    context["response"] = client.get(f"/exams/filter/status?status={status}")


@when(parsers.parse('I filter my exams by status "{status}"'))
def filter_student_exams_by_status(context, status):
    student_id = context.get("student_id", 1)
    context["response"] = client.get(
        f"/exams/filter/status/student?student_id={student_id}&status={status}"
    )


# ===================== THEN STEPS =====================
@then(parsers.parse("the API should return status code {status_code:d}"))
def verify_status_code(context, status_code):
    actual_code = context["response"].status_code
    assert actual_code == status_code, \
        f"Expected {status_code}, got {actual_code}. Response: {context['response'].text}"


@then(parsers.parse("I should see {count:d} exam in the results"))
def verify_exam_count_singular(context, count):
    response_data = context["response"].json()
    results = response_data if isinstance(response_data, list) else []
    assert len(results) == count, \
        f"Expected {count} exam, got {len(results)}. Results: {results}"


@then(parsers.parse("I should see {count:d} exams in the results"))
def verify_exam_count_plural(context, count):
    response_data = context["response"].json()
    results = response_data if isinstance(response_data, list) else []
    assert len(results) == count, \
        f"Expected {count} exams, got {len(results)}. Results: {results}"


@then(parsers.parse('the first exam should have title "{title}"'))
def verify_first_exam_title(context, title):
    response_data = context["response"].json()
    results = response_data if isinstance(response_data, list) else []
    assert len(results) > 0, "No results found"
    assert results[0]["title"] == title, \
        f"Expected title '{title}', got '{results[0]['title']}'"


@then(parsers.parse('the first exam should have code "{exam_code}"'))
def verify_first_exam_code(context, exam_code):
    response_data = context["response"].json()
    results = response_data if isinstance(response_data, list) else []
    assert len(results) > 0, "No results found"
    assert results[0]["exam_code"] == exam_code, \
        f"Expected code '{exam_code}', got '{results[0]['exam_code']}'"


@then(parsers.parse('the first exam should have status "{status}"'))
def verify_first_exam_status(context, status):
    response_data = context["response"].json()
    results = response_data if isinstance(response_data, list) else []
    assert len(results) > 0, "No results found"
    assert results[0]["status"] == status, \
        f"Expected status '{status}', got '{results[0]['status']}'"


@then(parsers.parse("all exams should have status {status}"))
def verify_all_exams_status(context, status):
    response_data = context["response"].json()
    results = response_data if isinstance(response_data, list) else []
    
    for exam in results:
        assert exam["status"].lower() == status.lower(), \
            f"Expected all exams to have status '{status}', but found '{exam['status']}'"


@then(parsers.parse("the error message should contain {error_text}"))
def verify_error_message(context, error_text):
    response_data = context["response"].json()
    error_detail = response_data.get("detail", "")
    
    # Remove quotes from error_text
    error_text_clean = error_text.strip('"')
    
    assert error_text_clean.lower() in error_detail.lower(), \
        f"Expected '{error_text_clean}' in error message, got '{error_detail}'"


@then("I should get an empty list")
def verify_empty_results(context):
    response_data = context["response"].json()
    results = response_data if isinstance(response_data, list) else []
    assert len(results) == 0, \
        f"Expected empty list, got {len(results)} items: {results}"


@then("the response should be a valid JSON array")
def verify_json_array(context):
    response_data = context["response"].json()
    assert isinstance(response_data, list), \
        f"Expected JSON array (list), got {type(response_data)}"