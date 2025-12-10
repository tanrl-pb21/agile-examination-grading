import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from pytest_bdd import (
    scenarios,
    given as bdd_given,
    when as bdd_when,
    then as bdd_then,
    parsers,
)

client = TestClient(app)


# -------------------------------
# CONTEXT FIXTURE
# -------------------------------
class Context:
    def __init__(self):
        self.last_response = None
        self.mock_cursor = None
        self.enrolled_students = []
        self.submissions = []
        self.exam_id = None
        self.mock_exam_service_patcher = None
        self.mock_conn_patcher = None


@pytest.fixture
def context():
    ctx = Context()
    yield ctx
    # Cleanup patchers if they exist
    if ctx.mock_exam_service_patcher:
        ctx.mock_exam_service_patcher.stop()
    if ctx.mock_conn_patcher:
        ctx.mock_conn_patcher.stop()


# -------------------------------
# LOAD FEATURE
# -------------------------------
scenarios("../feature/examSubmissionList.feature")


# -------------------------------
# MOCK DATA HELPERS
# -------------------------------
def setup_mock_database(context, exam_id, submitted_count=0, exam_exists=True):
    """
    Setup mock database connection with enrolled students and submissions
    
    Args:
        context: Test context object
        exam_id: Exam ID to mock
        submitted_count: Number of students who have submitted (default: 0)
        exam_exists: Whether the exam exists in the database (default: True)
    """
    
    # Sample enrolled students
    context.enrolled_students = [
        {
            "student_id": 101,
            "student_name": "Alice",
            "student_email": "alice@test.com",
        },
        {"student_id": 102, "student_name": "Bob", "student_email": "bob@test.com"},
        {
            "student_id": 103,
            "student_name": "Charlie",
            "student_email": "charlie@test.com",
        },
    ]

    # Create submissions for the first `submitted_count` students
    context.submissions = []
    for i in range(submitted_count):
        student = context.enrolled_students[i]
        context.submissions.append(
            {
                "submission_id": i + 1,
                "student_id": student["student_id"],
                "student_name": student["student_name"],
                "student_email": student["student_email"],
                "status": "submitted",
                "submission_date": "2025-12-01",
                "submission_time": "10:00:00",
                "score": 90 + i,
            }
        )

    # Start patching the database connection if not already patched
    if context.mock_conn_patcher is None:
        context.mock_conn_patcher = patch("src.routers.submission.get_conn")
        mock_conn = context.mock_conn_patcher.start()
        
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            mock_cursor
        )
        context.mock_cursor = mock_cursor
    else:
        mock_cursor = context.mock_cursor

    if exam_exists:
        # Mock fetchone for exam info (returns course_id)
        mock_cursor.fetchone.return_value = {"course": 1}
        
        # Use a lambda to return fresh lists each time (not consumed by side_effect)
        def get_enrolled_students():
            return context.enrolled_students.copy()
        
        def get_submissions():
            return context.submissions.copy()
        
        # Mock fetchall for enrolled students and submissions
        mock_cursor.fetchall.side_effect = [
            get_enrolled_students(),
            get_submissions(),
        ]
    else:
        # Exam doesn't exist - fetchone returns None
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.side_effect = [[], []]

    context.exam_id = exam_id


def setup_mock_exam_service(context, exam_id, exists=True):
    """Setup mock for ExamService.get_exam"""
    context.mock_exam_service_patcher = patch("src.routers.exams.ExamService.get_exam")
    mock_get_exam = context.mock_exam_service_patcher.start()
    
    if exists:
        mock_exam = {
            "exam_id": exam_id,
            "title": f"Sample Exam {exam_id}",
            "exam_code": f"EX{exam_id:03d}",
            "course": "CS101",
            "date": "2025-12-01",
            "start_time": "10:00",
            "end_time": "12:00",
            "status": "scheduled",
        }
        mock_get_exam.return_value = mock_exam
    else:
        mock_get_exam.return_value = None


# -------------------------------
# GIVEN STEPS
# -------------------------------
@bdd_given("the API is running")
def api_running():
    """Verify API is accessible"""
    return True


@bdd_given(parsers.parse("exam {eid:d} exists"))
def exam_exists(context, eid):
    """Mock exam existence and verify it can be fetched"""
    setup_mock_exam_service(context, eid, exists=True)
    
    # Setup default mock database with at least 1 submission for general scenarios
    # This will be overridden by specific "N students submitted" steps if present
    setup_mock_database(context, eid, submitted_count=1)
    
    # Verify exam can be fetched
    res = client.get(f"/exams/{eid}")
    print(f"📋 GET /exams/{eid} - Response status: {res.status_code}")
    assert res.status_code == 200
    
    context.exam_id = eid


@bdd_given(parsers.parse("no exam exists with ID {eid:d}"))
def exam_not_exists(context, eid):
    """Mock non-existent exam"""
    setup_mock_exam_service(context, eid, exists=False)
    
    # Mock the database to return exam not found
    setup_mock_database(context, eid, submitted_count=0, exam_exists=False)
    context.exam_id = eid


@bdd_given(parsers.parse("{n:d} student has submitted"))
def n_students_submitted(n, context):
    """Setup mock with specific number of submissions"""
    if context.exam_id is None:
        context.exam_id = 239  # Default exam ID
    setup_mock_database(context, context.exam_id, submitted_count=n)


@bdd_given(parsers.parse("the current time is after the exam end time"))
def time_after_exam_end(context):
    """Mock current time to be after exam end time"""
    # Patch datetime if your API uses it
    with patch("src.routers.submission.datetime") as mock_datetime:
        mock_datetime.now.return_value.time.return_value = "13:00:00"  # After 12:00 end time
        return True


# -------------------------------
# WHEN STEPS
# -------------------------------
@bdd_when(parsers.parse("I fetch the student list for exam {eid:d}"))
def fetch_student_list(context, eid):
    """Fetch student list using mocked data"""
    # Only setup mock database if not already set up
    # (some scenarios like "N students submitted" already set it up)
    if context.mock_cursor is None:
        setup_mock_database(context, eid, submitted_count=0)
    
    # Ensure exam service mock exists if not set up
    if context.mock_exam_service_patcher is None:
        setup_mock_exam_service(context, eid, exists=True)
    
    context.last_response = client.get(f"/submissions/exam/{eid}/students")
    print(f"📊 GET /submissions/exam/{eid}/students - Status: {context.last_response.status_code}")
    
    # Debug: print response for troubleshooting
    if context.last_response.status_code == 200:
        data = context.last_response.json()
        if isinstance(data, list):
            print(f"   Returned {len(data)} students, {len([s for s in data if s.get('status') == 'submitted'])} submitted")


@bdd_when("another student submits the exam")
def another_student_submits(context):
    """Simulate another student submission by updating mock data"""
    if len(context.enrolled_students) > len(context.submissions):
        next_student = context.enrolled_students[len(context.submissions)]
        new_submission = {
            "submission_id": len(context.submissions) + 1,
            "student_id": next_student["student_id"],
            "student_name": next_student["student_name"],
            "student_email": next_student["student_email"],
            "status": "submitted",
            "submission_date": "2025-12-01",
            "submission_time": "11:00:00",
            "score": 95,
        }
        context.submissions.append(new_submission)
        
        # Update mock to return new data - reset side_effect for next call
        context.mock_cursor.fetchone.return_value = {"course": 1}
        context.mock_cursor.fetchall.side_effect = [
            context.enrolled_students.copy(),
            context.submissions.copy(),
        ]
        print(f"✅ New submission added. Total submissions: {len(context.submissions)}")


# -------------------------------
# THEN STEPS
# -------------------------------
@bdd_then("the list contains valid student entries")
def list_contains_entries(context):
    """Verify response contains valid student data"""
    assert context.last_response.status_code == 200
    data = context.last_response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) > 0, "List should not be empty"
    
    for s in data:
        assert "student_id" in s, "Each entry should have student_id"
        assert "student_name" in s, "Each entry should have student_name"
        assert "status" in s, "Each entry should have status"


@bdd_then("submitted count plus missed count equals total enrolled students")
def counts_match(context):
    """Verify total count matches enrolled students"""
    data = context.last_response.json()
    submitted = len([s for s in data if s["status"] == "submitted"])
    missed = len([s for s in data if s["status"] == "missed"])
    total = submitted + missed
    
    assert total == len(context.enrolled_students), \
        f"Total ({total}) should equal enrolled students ({len(context.enrolled_students)})"


@bdd_then("missed students have no submission date, time, or score")
def missed_students_no_submission_details(context):
    """Verify missed students have null submission fields"""
    data = context.last_response.json()
    missed_students = [s for s in data if s["status"] == "missed"]
    
    for s in missed_students:
        assert s.get("submission_id") is None, "Missed students should have no submission_id"
        assert s.get("submission_date") is None, "Missed students should have no submission_date"
        assert s.get("submission_time") is None, "Missed students should have no submission_time"
        assert s.get("score") is None, "Missed students should have no score"


@bdd_then("the summary shows total students, submitted, and missed counts correctly")
def summary_counts_correct(context):
    """Verify summary counts are accurate"""
    data = context.last_response.json()
    total = len(data)
    submitted = len([s for s in data if s["status"] == "submitted"])
    missed = len([s for s in data if s["status"] == "missed"])
    
    assert total == len(context.enrolled_students), "Total should match enrolled count"
    assert submitted == len(context.submissions), "Submitted should match submission count"
    assert missed == len(context.enrolled_students) - len(context.submissions), "Missed count should be correct"
    assert total == submitted + missed, "Total should equal submitted + missed"


@bdd_then('all students who have not submitted are marked as "missed"')
def missed_after_exam_end(context):
    """Verify non-submitted students are marked as missed"""
    data = context.last_response.json()
    
    for s in data:
        if s["status"] != "submitted":
            assert s["status"] == "missed", f"Student {s['student_id']} should be marked as missed"


@bdd_then("submitted count increases and missed count decreases")
def counts_update_correctly(context):
    """Verify counts update correctly after new submission"""
    data = context.last_response.json()

    if not isinstance(data, list):
        pytest.fail("API should return a list")
    
    submitted = len([s for s in data if s.get("status") == "submitted"])
    missed = len([s for s in data if s.get("status") == "missed"])

    # Verify counts are correct
    assert submitted == len(context.submissions), \
        f"Submitted count ({submitted}) should match submissions ({len(context.submissions)})"
    assert missed == len(context.enrolled_students) - len(context.submissions), \
        f"Missed count ({missed}) should be enrolled - submitted"
    assert submitted + missed == len(context.enrolled_students), \
        "Total should equal enrolled students"


@bdd_then("submitted students show correct score, submission date, and submission time")
def submissions_have_details(context):
    """Verify submitted students have all required fields"""
    data = context.last_response.json()
    submitted_students = [s for s in data if s["status"] == "submitted"]
    
    assert len(submitted_students) > 0, "Should have at least one submitted student"
    
    for s in submitted_students:
        assert "score" in s, f"Student {s['student_id']} should include score field"
        assert s.get("submission_date") is not None, f"Student {s['student_id']} should have submission_date"
        assert s.get("submission_time") is not None, f"Student {s['student_id']} should have submission_time"


@bdd_then(parsers.parse('I receive the error "{msg}"'))
def error_message(context, msg):
    """Verify error response"""
    assert context.last_response.status_code == 404, \
        f"Expected 404, got {context.last_response.status_code}"
    
    response_data = context.last_response.json()
    assert "detail" in response_data, "Error response should have 'detail' field"
    assert msg.lower() in response_data["detail"].lower(), \
        f"Error message should contain '{msg}'"