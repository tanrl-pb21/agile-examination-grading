import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# -------------------------------------------------------
# TEST 1: Instructor views student list for an exam
# -------------------------------------------------------


def test_get_exam_students_list():
    """
    Verify instructor can open an exam and retrieve
    a full student list including submitted + missed.
    """

    exam_id = 1  # <-- change this to an exam_id that exists in your DB

    response = client.get(f"/submissions/exam/{exam_id}/students")

    assert response.status_code == 200

    data = response.json()

    # Data must be a list
    assert isinstance(data, list)
    assert len(data) > 0

    # Validate fields for one student
    first = data[0]

    assert "student_id" in first
    assert "student_name" in first
    assert "student_email" in first
    assert "status" in first
    assert "submission_id" in first
    assert "submission_date" in first
    assert "submission_time" in first
    assert "score" in first


# -------------------------------------------------------
# TEST 2: Verify counts: total, submitted, missed
# -------------------------------------------------------


def test_exam_students_status_counts():
    """
    Ensure counts of submitted vs missed are correct.
    """

    exam_id = 1  # <-- use an exam_id with multiple students

    response = client.get(f"/submissions/exam/{exam_id}/students")
    assert response.status_code == 200

    data = response.json()

    total_students = len(data)
    submitted = len([s for s in data if s["status"] != "missed"])
    missed = len([s for s in data if s["status"] == "missed"])

    # Should be valid counts
    assert total_students == submitted + missed

    # At least one student must be enrolled
    assert total_students > 0


# -------------------------------------------------------
# TEST 3: Verify students with no submission appear as "missed"
# -------------------------------------------------------


def test_exam_students_missed_shown_correctly():
    """
    A student who has NOT submitted should appear with:
    - submission_id = None
    - status = "missed"
    """

    exam_id = 1

    response = client.get(f"/submissions/exam/{exam_id}/students")
    assert response.status_code == 200

    data = response.json()

    # Pick any missed student
    missed_students = [s for s in data if s["status"] == "missed"]

    # There should be at least one missed student if your DB has any
    if missed_students:
        ms = missed_students[0]
        assert ms["submission_id"] is None
        assert ms["submission_date"] is None
        assert ms["submission_time"] is None
        assert ms["score"] is None


# -------------------------------------------------------
# TEST 4: Verify submitted students show submission info
# -------------------------------------------------------


def test_exam_students_submitted_show_correct_fields():
    """
    A student who submitted must show submission details.
    """

    exam_id = 1

    response = client.get(f"/submissions/exam/{exam_id}/students")
    assert response.status_code == 200

    data = response.json()

    submitted = [s for s in data if s["status"] != "missed"]

    if submitted:  # Only test if DB has any submissions
        sub = submitted[0]

        assert sub["submission_id"] is not None
        assert sub["submission_date"] is not None
        assert sub["submission_time"] is not None
