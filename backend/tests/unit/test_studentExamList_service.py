import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# -------------------------------
# Mock Data
# -------------------------------
mock_enrolled_students = [
    {"student_id": 101, "student_name": "Alice", "student_email": "alice@test.com"},
    {"student_id": 102, "student_name": "Bob", "student_email": "bob@test.com"},
]

mock_submissions_alice = [
    {
        "submission_id": 1,
        "student_id": 101,
        "student_name": "Alice",
        "student_email": "alice@test.com",
        "status": "submitted",
        "submission_date": "2025-12-01",
        "submission_time": "10:00:00",
        "score": 90,
    }
]

mock_submissions_all_submitted = [
    {
        "submission_id": 1,
        "student_id": 101,
        "student_name": "Alice",
        "student_email": "alice@test.com",
        "status": "submitted",
        "submission_date": "2025-12-01",
        "submission_time": "10:00:00",
        "score": 90,
    },
    {
        "submission_id": 2,
        "student_id": 102,
        "student_name": "Bob",
        "student_email": "bob@test.com",
        "status": "graded",
        "submission_date": "2025-12-01",
        "submission_time": "11:00:00",
        "score": 85,
    },
]

mock_submissions_all_missed = []

mock_mixed_status = [
    {
        "submission_id": 1,
        "student_id": 101,
        "student_name": "Alice",
        "student_email": "alice@test.com",
        "status": "submitted",
        "submission_date": "2025-12-01",
        "submission_time": "10:00:00",
        "score": 90,
    }
]

mock_empty = []


# -------------------------------
# Fixture to patch get_conn
# -------------------------------
@pytest.fixture
def mock_db():
    with patch("src.routers.submission.get_conn") as mock_conn:
        mock_cursor = MagicMock()
        # Make cursor a context manager
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            mock_cursor
        )
        yield mock_cursor


# -------------------------------
# Test Helpers
# -------------------------------
def setup_mock(mock_cursor, enrolled=None, submissions=None, exam=None):
    """Setup fetchall and fetchone side_effects for each test"""
    enrolled = enrolled or []
    submissions = submissions or []
    exam = exam or {"course": 1}

    # fetchone() returns exam info
    mock_cursor.fetchone.side_effect = [exam]
    # fetchall() returns enrolled students then submissions
    mock_cursor.fetchall.side_effect = [enrolled, submissions]


# -------------------------------
# TESTS
# -------------------------------
def test_basic_student_list(mock_db):
    setup_mock(mock_db, mock_enrolled_students, mock_submissions_alice)
    response = client.get("/submissions/exam/1/students")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Alice + Bob
    assert any(s["status"] == "submitted" for s in data)
    assert any(s["status"] == "missed" for s in data)


def test_all_students_submitted(mock_db):
    setup_mock(mock_db, mock_enrolled_students, mock_submissions_all_submitted)
    response = client.get("/submissions/exam/3/students")
    assert response.status_code == 200
    data = response.json()
    assert all(s["status"] in ("submitted", "graded") for s in data)


def test_all_students_missed(mock_db):
    setup_mock(mock_db, mock_enrolled_students, mock_submissions_all_missed)
    response = client.get("/submissions/exam/4/students")
    assert response.status_code == 200
    data = response.json()
    assert all(s["status"] == "missed" for s in data)


def test_mixed_submission_status(mock_db):
    setup_mock(mock_db, mock_enrolled_students, mock_mixed_status)
    response = client.get("/submissions/exam/5/students")
    assert response.status_code == 200
    data = response.json()
    statuses = [s["status"] for s in data]
    assert "submitted" in statuses
    assert "missed" in statuses


def test_score_field_present(mock_db):
    setup_mock(mock_db, mock_enrolled_students, mock_submissions_alice)
    response = client.get("/submissions/exam/1/students")
    data = response.json()
    submitted = [s for s in data if s["status"] != "missed"]
    for s in submitted:
        assert "score" in s


def test_empty_student_list(mock_db):
    setup_mock(mock_db, [], mock_empty)
    response = client.get("/submissions/exam/10/students")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_exam_not_found(mock_db):
    # fetchone returns None to simulate missing exam
    mock_db.fetchone.return_value = None
    response = client.get("/submissions/exam/999/students")
    assert response.status_code == 404
    assert response.json()["detail"] == "Exam not found"


def test_submission_date_time_format(mock_db):
    setup_mock(mock_db, mock_enrolled_students, mock_submissions_alice)
    response = client.get("/submissions/exam/1/students")
    data = response.json()
    submitted = [s for s in data if s["status"] != "missed"]
    for s in submitted:
        assert isinstance(s["submission_date"], str) or s["submission_date"] is None
        assert isinstance(s["submission_time"], str) or s["submission_time"] is None


def test_all_fields_present(mock_db):
    setup_mock(mock_db, mock_enrolled_students, mock_submissions_alice)
    response = client.get("/submissions/exam/1/students")
    data = response.json()
    expected_keys = [
        "submission_id",
        "student_id",
        "student_name",
        "student_email",
        "status",
        "submission_date",
        "submission_time",
        "score",
        "score_grade",
        "overall_feedback",
    ]
    for s in data:
        for key in expected_keys:
            assert key in s


def test_multiple_submitted_students(mock_db):
    submissions = [
        {
            "submission_id": 1,
            "student_id": 101,
            "student_name": "Alice",
            "student_email": "alice@test.com",
            "status": "submitted",
            "submission_date": "2025-12-01",
            "submission_time": "10:00:00",
            "score": 90,
        },
        {
            "submission_id": 2,
            "student_id": 103,
            "student_name": "Charlie",
            "student_email": "charlie@test.com",
            "status": "submitted",
            "submission_date": "2025-12-01",
            "submission_time": "10:30:00",
            "score": 95,
        },
    ]
    enrolled = mock_enrolled_students + [
        {
            "student_id": 103,
            "student_name": "Charlie",
            "student_email": "charlie@test.com",
        }
    ]
    setup_mock(mock_db, enrolled, submissions)
    response = client.get("/submissions/exam/1/students")
    data = response.json()
    assert sum(1 for s in data if s["status"] == "submitted") == 2


def test_mixed_students_with_scores(mock_db):
    submissions = [
        {
            "submission_id": 1,
            "student_id": 101,
            "student_name": "Alice",
            "student_email": "alice@test.com",
            "status": "submitted",
            "submission_date": "2025-12-01",
            "submission_time": "10:00:00",
            "score": 90,
        }
    ]
    enrolled = mock_enrolled_students + [
        {
            "student_id": 103,
            "student_name": "Charlie",
            "student_email": "charlie@test.com",
        }
    ]
    setup_mock(mock_db, enrolled, submissions)
    response = client.get("/submissions/exam/1/students")
    data = response.json()
    statuses = [s["status"] for s in data]
    assert "submitted" in statuses
    assert "missed" in statuses
    for s in data:
        assert "score" in s

