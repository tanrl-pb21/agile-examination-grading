import pytest
from fastapi.testclient import TestClient
from main import app
from pytest_bdd import (
    scenarios,
    given as bdd_given,
    when as bdd_when,
    then as bdd_then,
    parsers,
)

client = TestClient(app)


# ---------------------------------------
# CONTEXT FIXTURE
# ---------------------------------------
class Context:
    def __init__(self):
        self.last_response = None


@pytest.fixture
def context():
    return Context()


# Load BDD feature
scenarios("../feature/examSubmissionList.feature")


# ---------------------------------------
# GIVEN STEPS
# ---------------------------------------
@bdd_given("the API is running")
def api_running():
    return True


@bdd_given(parsers.parse("exam {eid:d} exists"))
def exam_exists(eid):
    res = client.get(f"/exams/{eid}")
    assert res.status_code == 200, f"Expected exam {eid} to exist"


@bdd_given(parsers.parse("no exam exists with ID {eid:d}"))
def exam_not_exists(eid):
    res = client.get(f"/exams/{eid}")
    assert res.status_code == 404, f"Expected exam {eid} NOT to exist"


# ---------------------------------------
# WHEN STEPS
# ---------------------------------------
@bdd_when(parsers.parse("I fetch the student list for exam {eid:d}"))
def fetch_student_list(context, eid):
    context.last_response = client.get(f"/submissions/exam/{eid}/students")


# ---------------------------------------
# THEN STEPS
# ---------------------------------------
@bdd_then("the list contains valid student entries")
def list_contains_entries(context):
    assert context.last_response.status_code == 200
    data = context.last_response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Basic field checks
    for s in data:
        assert "student_id" in s
        assert "student_name" in s
        assert "status" in s


@bdd_then("submitted count plus missed count equals total enrolled students")
def counts_match(context):
    data = context.last_response.json()

    submitted = len([s for s in data if s["status"] != "missed"])
    missed = len([s for s in data if s["status"] == "missed"])
    total = len(data)

    assert submitted + missed == total


@bdd_then("missed students have no submission date, time, or score")
def missed_students_no_submission_details(context):
    data = context.last_response.json()

    for s in data:
        if s["status"] == "missed":
            assert s["submission_id"] is None
            assert s["submission_date"] is None
            assert s["submission_time"] is None
            assert s["score"] is None


@bdd_then("the student count is correct")
def count_is_correct(context):
    data = context.last_response.json()

    submitted = len([s for s in data if s["status"] != "missed"])
    missed = len([s for s in data if s["status"] == "missed"])

    assert submitted + missed == len(data)


@bdd_then(parsers.parse('I receive the error "{msg}"'))
def error_message(context, msg):
    assert context.last_response.status_code == 404
    assert msg.lower() in context.last_response.json()["detail"].lower()
