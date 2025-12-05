import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import date, time as dt_time
from src.main import app  # Adjust import based on your main app location

# Load all scenarios from the feature file
scenarios('../feature/search_studentside_submission.feature')


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_cursor():
    """Create a mock cursor"""
    cursor = MagicMock()
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    """Create a mock connection"""
    conn = MagicMock()
    conn.__enter__ = Mock(return_value=conn)
    conn.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = mock_cursor
    return conn


@pytest.fixture
def context():
    """Shared context for BDD scenarios"""
    return {
        "user_id": None,
        "submissions": {},
        "search_query": {},
        "response": None,
        "status_code": None,
        "filtered_results": []
    }


@pytest.fixture
def sample_submissions():
    """Sample submission data for all tests - ordered by date DESC"""
    return {
        1: {
            "id": 1,
            "exam_code": 100,
            "submission_date": date(2024, 1, 15),
            "submission_time": dt_time(10, 30, 0),
            "score": 85,
            "score_grade": None,
            "status": "graded",
            "exam_title": "Python Basics",
            "exam_id": "EXAM-100"
        },
        2: {
            "id": 2,
            "exam_code": 101,
            "submission_date": date(2024, 1, 20),
            "submission_time": dt_time(14, 15, 0),
            "score": 90,
            "score_grade": None,
            "status": "graded",
            "exam_title": "Data Structures",
            "exam_id": "EXAM-101"
        },
        3: {
            "id": 3,
            "exam_code": 102,
            "submission_date": date(2024, 2, 1),
            "submission_time": dt_time(9, 0, 0),
            "score": 78,
            "score_grade": None,
            "status": "graded",
            "exam_title": "Algorithms Final",
            "exam_id": "EXAM-102"
        },
        4: {
            "id": 4,
            "exam_code": 103,
            "submission_date": date(2024, 2, 10),
            "submission_time": dt_time(11, 45, 0),
            "score": None,
            "score_grade": None,
            "status": "pending",
            "exam_title": "Machine Learning",
            "exam_id": "EXAM-103"
        },
        5: {
            "id": 5,
            "exam_code": 104,
            "submission_date": date(2024, 2, 15),
            "submission_time": dt_time(16, 20, 0),
            "score": 95,
            "score_grade": None,
            "status": "graded",
            "exam_title": "Python Advanced",
            "exam_id": "EXAM-104"
        }
    }


def get_submission_list_sorted(submissions_dict):
    """Convert dict to list and sort by date DESC (newest first)"""
    submissions = list(submissions_dict.values())
    submissions.sort(key=lambda x: (x["submission_date"], x["submission_time"]), reverse=True)
    return submissions


@pytest.fixture
def total_marks_map():
    """Total marks mapping for exams"""
    return {
        100: 100,
        101: 100,
        102: 100,
        103: 100,
        104: 100
    }


# ===== BACKGROUND STEPS =====

@given("the submission service is available")
def submission_service_available():
    """Submission service is available"""
    pass


@given(parsers.parse('user {user_id:d} has submission with id {submission_id:d} for exam "{exam_title}"'))
def user_has_submission(context, sample_submissions, user_id, submission_id, exam_title):
    """Store submission data for user"""
    context["user_id"] = user_id
    if submission_id in sample_submissions:
        submission = sample_submissions[submission_id].copy()
        submission["exam_title"] = exam_title
        context["submissions"][submission_id] = submission


# ===== GIVEN STEPS =====

@given(parsers.parse('user {user_id:d} has submissions'))
def user_has_submissions(context, user_id):
    """User has submissions"""
    context["user_id"] = user_id


@given(parsers.parse('user {user_id:d} has no submissions'))
def user_has_no_submissions(context, user_id):
    """User has no submissions"""
    context["user_id"] = user_id
    context["submissions"] = {}


# ===== WHEN STEPS =====

@when(parsers.parse('I search for submission ID "{search_id}"'))
def search_by_submission_id(client, context, mock_conn, mock_cursor, sample_submissions, total_marks_map, search_id):
    """Search submissions by submission ID"""
    context["search_query"]["type"] = "submission_id"
    context["search_query"]["value"] = search_id
    
    user_id = context.get("user_id", 1)
    
    # Get submissions for user - sorted by date DESC
    # Check if user has no submissions (empty dict)
    if context.get("submissions") is not None and len(context["submissions"]) == 0:
        submission_list = []
    elif context.get("submissions"):
        submission_list = get_submission_list_sorted(context["submissions"])
    else:
        submission_list = get_submission_list_sorted(sample_submissions)
    
    mock_cursor.fetchall.side_effect = [
        submission_list,
        [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()] if submission_list else []
    ]
    
    with patch("src.services.submission_service.get_conn", return_value=mock_conn):
        response = client.get(f"/submissions/student/{user_id}")
    
    context["response"] = response.json()
    context["status_code"] = response.status_code
    
    # Filter by submission ID
    search_id_lower = search_id.lower()
    context["filtered_results"] = [
        s for s in context["response"]
        if search_id_lower in s["submission_id"].lower()
    ]


@when(parsers.parse('I search for exam title "{exam_title}"'))
def search_by_exam_title(client, context, mock_conn, mock_cursor, sample_submissions, total_marks_map, exam_title):
    """Search submissions by exam title"""
    context["search_query"]["type"] = "exam_title"
    context["search_query"]["value"] = exam_title
    
    user_id = context.get("user_id", 1)
    
    # Get submissions for user - sorted by date DESC
    # Check if user has no submissions (empty dict)
    if context.get("submissions") is not None and len(context["submissions"]) == 0:
        submission_list = []
    elif context.get("submissions"):
        submission_list = get_submission_list_sorted(context["submissions"])
    else:
        submission_list = get_submission_list_sorted(sample_submissions)
    
    mock_cursor.fetchall.side_effect = [
        submission_list,
        [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()] if submission_list else []
    ]
    
    with patch("src.services.submission_service.get_conn", return_value=mock_conn):
        response = client.get(f"/submissions/student/{user_id}")
    
    context["response"] = response.json()
    context["status_code"] = response.status_code
    
    # Filter by exam title
    exam_title_lower = exam_title.lower()
    context["filtered_results"] = [
        s for s in context["response"]
        if exam_title_lower in s["exam_title"].lower()
    ]


@when("I get all submissions without search")
def get_all_submissions(client, context, mock_conn, mock_cursor, sample_submissions, total_marks_map):
    """Get all submissions without filtering"""
    user_id = context.get("user_id", 1)
    
    submission_list = get_submission_list_sorted(sample_submissions)
    
    mock_cursor.fetchall.side_effect = [
        submission_list,
        [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
    ]
    
    with patch("src.services.submission_service.get_conn", return_value=mock_conn):
        response = client.get(f"/submissions/student/{user_id}")
    
    context["response"] = response.json()
    context["status_code"] = response.status_code
    context["filtered_results"] = context["response"]


# ===== THEN STEPS =====

@then(parsers.parse('I should receive {count:d} submission'))
@then(parsers.parse('I should receive {count:d} submissions'))
def should_receive_submissions(context, count):
    """Verify number of submissions received"""
    assert context["status_code"] == 200
    assert len(context["filtered_results"]) == count


@then(parsers.parse('the submission should have id {submission_id:d}'))
def submission_has_id(context, submission_id):
    """Verify submission has specific id"""
    assert len(context["filtered_results"]) > 0
    assert context["filtered_results"][0]["id"] == submission_id


@then(parsers.parse('the submission should have exam title "{exam_title}"'))
def submission_has_exam_title(context, exam_title):
    """Verify submission has specific exam title"""
    assert len(context["filtered_results"]) > 0
    assert context["filtered_results"][0]["exam_title"] == exam_title


@then('all submissions should have submission IDs starting with "sub"')
def all_submissions_start_with_sub(context):
    """Verify all submissions have IDs starting with 'sub'"""
    for submission in context["filtered_results"]:
        assert submission["submission_id"].lower().startswith("sub")


@then(parsers.parse('one submission should have exam title "{exam_title}"'))
def one_submission_has_exam_title(context, exam_title):
    """Verify one submission has specific exam title"""
    titles = [s["exam_title"] for s in context["filtered_results"]]
    assert exam_title in titles


@then("the submission should have submission_id field")
def submission_has_submission_id_field(context):
    """Verify submission has submission_id field"""
    assert len(context["filtered_results"]) > 0
    assert "submission_id" in context["filtered_results"][0]


@then("the submission should have exam_title field")
def submission_has_exam_title_field(context):
    """Verify submission has exam_title field"""
    assert len(context["filtered_results"]) > 0
    assert "exam_title" in context["filtered_results"][0]


@then("the submission should have exam_id field")
def submission_has_exam_id_field(context):
    """Verify submission has exam_id field"""
    assert len(context["filtered_results"]) > 0
    assert "exam_id" in context["filtered_results"][0]


@then("the submission should have date field")
def submission_has_date_field(context):
    """Verify submission has date field"""
    assert len(context["filtered_results"]) > 0
    assert "date" in context["filtered_results"][0]


@then("the submission should have status field")
def submission_has_status_field(context):
    """Verify submission has status field"""
    assert len(context["filtered_results"]) > 0
    assert "status" in context["filtered_results"][0]


@then("submissions should be ordered by date descending")
def submissions_ordered_by_date(context):
    """Verify submissions are ordered by date descending"""
    assert len(context["filtered_results"]) > 1
    
    # Submissions come from the service already sorted by date descending
    # Just verify that dates are in descending order
    from datetime import datetime
    
    dates = []
    for submission in context["filtered_results"]:
        date_str = submission["date"]
        dates.append(datetime.strptime(date_str, "%m/%d/%Y"))
    
    # Check that each date is greater than or equal to the next
    for i in range(len(dates) - 1):
        assert dates[i] >= dates[i + 1], f"Submissions should be ordered from newest to oldest: {dates[i]} should be >= {dates[i+1]}"