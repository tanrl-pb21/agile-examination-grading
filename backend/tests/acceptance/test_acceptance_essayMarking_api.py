import pytest
from fastapi.testclient import TestClient
from main import app
from pytest_bdd import scenarios, given, when, then

client = TestClient(app)

# Use YOUR ACTUAL IDs here
EXISTING_SUBMISSION_ID = 22
ESSAY_SUBMISSION_ANSWER_ID = 45

scenarios("../feature/essayMarking.feature")


class Context:
    def __init__(self):
        self.last_response = None


@pytest.fixture
def context():
    return Context()


# ---------------------------
# GIVEN
# ---------------------------
@given("the grading API is running")
def api_running():
    return True


@given("a submission with an essay answer exists")
def essay_answer_exists():
    # Check submission exists
    res = client.get(f"/submissions/{EXISTING_SUBMISSION_ID}")
    assert res.status_code == 200


# ---------------------------
# WHEN
# ---------------------------
@when("I submit marks for the essay answer")
def submit_marks(context):
    payload = {
        "submission_id": EXISTING_SUBMISSION_ID,
        "essay_grades": [
            {"submission_answer_id": ESSAY_SUBMISSION_ANSWER_ID, "score": 8.0}
        ],
        "total_score": 8.0,
        "score_grade": "B",
        "overall_feedback": "Good",
    }

    context.last_response = client.post("/grading/save", json=payload)


# ---------------------------
# THEN
# ---------------------------
@then("the mark is saved successfully")
def mark_saved(context):
    assert context.last_response.status_code == 200
    data = context.last_response.json()
    assert data.get("success") is True
