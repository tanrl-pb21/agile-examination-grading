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
# CONTEXT FIXTURE (required!)
# ---------------------------------------
class Context:
    def __init__(self):
        self.last_response = None


@pytest.fixture
def context():
    return Context()


# Load scenarios
scenarios("../feature/lateSubmission.feature")


# ---------------------------------------
# GIVEN
# ---------------------------------------


@bdd_given("the API is running")
def api_running():
    return True


@bdd_given(parsers.parse("exam {eid:d} exists"))
def exam_exists(eid):
    res = client.get(f"/exams/{eid}")
    assert res.status_code == 200, f"Exam {eid} must exist for the test"


# ---------------------------------------
# WHEN
# ---------------------------------------


@bdd_when(parsers.parse("I fetch the student list for exam {eid:d}"))
def fetch_student_list(context, eid):
    context.last_response = client.get(f"/submissions/exam/{eid}/students")


# ---------------------------------------
# THEN
# ---------------------------------------


@bdd_then("missed students have no submission fields")
def missed_has_no_submission(context):
    assert context.last_response.status_code == 200
    data = context.last_response.json()

    for s in data:
        if s["submission_id"] is None:
            assert s["submission_date"] is None
            assert s["submission_time"] is None
            assert s["score"] is None


@bdd_then("submitted students have submission fields")
def submitted_have_fields(context):
    assert context.last_response.status_code == 200
    data = context.last_response.json()

    for s in data:
        if s["submission_id"] is not None:
            assert s["submission_date"] is not None
            assert s["submission_time"] is not None


@bdd_then("submitted + missed equals total students")
def count_consistent(context):
    assert context.last_response.status_code == 200
    data = context.last_response.json()

    total = len(data)
    submitted = len([s for s in data if s["submission_id"] is not None])
    missed = len([s for s in data if s["submission_id"] is None])

    assert total == submitted + missed


@bdd_then(parsers.parse('I receive the error "{msg}"'))
def error_received(context, msg):
    assert context.last_response.status_code == 404
    assert msg.lower() in context.last_response.json()["detail"].lower()
