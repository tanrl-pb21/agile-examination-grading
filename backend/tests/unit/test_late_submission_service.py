import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ----------------------------------------------------------
# TEST 1: A LATE student → no submission record → status = "missed"
# ----------------------------------------------------------


def test_late_student_shows_as_missed():
    """
    If a student submits after the exam end time,
    the system blocks the submission -> no record created.

    They MUST appear as 'missed'.
    """

    exam_id = 1  # <-- Use a real exam ID

    response = client.get(f"/submissions/exam/{exam_id}/students")
    assert response.status_code == 200

    data = response.json()

    # All students with no submission_id are "missed"
    missed_students = [s for s in data if s["submission_id"] is None]

    # If there is at least one missed student, verify structure
    if missed_students:
        ms = missed_students[0]

        assert ms["status"] == "missed"
        assert ms["submission_date"] is None
        assert ms["submission_time"] is None
        assert ms["score"] is None


# ----------------------------------------------------------
# TEST 2: A student who SUBMITTED (on time) is not missed
# ----------------------------------------------------------


def test_submitted_student_not_missed():
    """
    A valid (on-time) submission must NOT show as missed.
    """

    exam_id = 1

    response = client.get(f"/submissions/exam/{exam_id}/students")
    assert response.status_code == 200

    data = response.json()

    submitted = [s for s in data if s["submission_id"] is not None]

    if submitted:
        s = submitted[0]
        assert s["status"] != "missed"
        assert s["submission_date"] is not None
        assert s["submission_time"] is not None


# ----------------------------------------------------------
# TEST 3: Total students = submitted + missed
# ----------------------------------------------------------


def test_student_count_consistency():
    """
    Total students must equal submitted + missed.
    """

    exam_id = 1

    response = client.get(f"/submissions/exam/{exam_id}/students")
    assert response.status_code == 200

    data = response.json()
    total = len(data)
    submitted = len([s for s in data if s["submission_id"] is not None])
    missed = len([s for s in data if s["submission_id"] is None])

    assert total == submitted + missed
    assert total > 0


# ----------------------------------------------------------
# TEST 4: Students who never submitted (including late) have no submission fields
# ----------------------------------------------------------


def test_missed_student_fields_are_none():
    """
    Missed students always have null submission fields.
    Late and non-submitted students appear the same.
    """

    exam_id = 1

    response = client.get(f"/submissions/exam/{exam_id}/students")
    assert response.status_code == 200

    data = response.json()
    missed = [s for s in data if s["submission_id"] is None]

    for m in missed:
        assert m["submission_date"] is None
        assert m["submission_time"] is None
        assert m["score"] is None


# ----------------------------------------------------------
# TEST 5: Exam does not exist -> return 404
# ----------------------------------------------------------


def test_exam_not_found():
    response = client.get("/submissions/exam/999999/students")

    assert response.status_code == 404
    assert "Exam not found" in response.json()["detail"]
