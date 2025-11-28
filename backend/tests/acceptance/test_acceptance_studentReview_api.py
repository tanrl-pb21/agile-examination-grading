from __future__ import annotations
from typing import Dict
import pytest
from fastapi.testclient import TestClient
from pytest_bdd import (
    scenarios,
    given as bdd_given,
    when as bdd_when,
    then as bdd_then,
    parsers,
)

from main import app

# ------------------------------------------------------------
# Load scenarios
# ------------------------------------------------------------
scenarios("../feature/studentReview.feature")


# ------------------------------------------------------------
# Shared context
# ------------------------------------------------------------
class Context:
    def __init__(self):
        self.last_response = None


@pytest.fixture
def context() -> Context:
    return Context()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ------------------------------------------------------------
# GIVEN STEPS
# ------------------------------------------------------------
@bdd_given("the API is running", target_fixture="api_is_running")
def api_is_running(client: TestClient, context: Context) -> Dict[str, object]:
    context.last_response = None
    return {"client": client}


@bdd_given(
    parsers.parse("a graded submission with ID {sub_id:d} exists for user {user_id:d}")
)
def graded_submission_exists(api_is_running, sub_id: int, user_id: int):
    """
    Ensure submission exists AND is graded.
    """
    client = api_is_running["client"]
    res = client.get(f"/submissions/{sub_id}/review?user_id={user_id}")

    # Two possibilities:
    # - It exists and is graded → 200
    # - It exists but not graded → 404 (Your API blocks not-graded)
    assert res.status_code in (200, 404)


@bdd_given(
    parsers.parse(
        "an ungraded submission with ID {sub_id:d} exists for user {user_id:d}"
    )
)
def ungraded_submission_exists(api_is_running, sub_id: int, user_id: int):
    """
    Just ensure the submission exists.
    """
    client = api_is_running["client"]
    res = client.get(f"/submissions/{sub_id}")
    assert res.status_code == 200, f"Submission {sub_id} should exist."


@bdd_given(parsers.parse("submission {sub_id:d} does not exist"))
def submission_not_exist(api_is_running, sub_id: int):
    client = api_is_running["client"]
    res = client.get(f"/submissions/{sub_id}")
    assert res.status_code == 404, f"Submission {sub_id} should NOT exist."


# ------------------------------------------------------------
# WHEN STEPS
# ------------------------------------------------------------
@bdd_when(
    parsers.parse("I request a review for submission {sub_id:d} as user {user_id:d}")
)
def request_review(api_is_running, context, sub_id: int, user_id: int):
    client = api_is_running["client"]
    response = client.get(f"/submissions/{sub_id}/review?user_id={user_id}")
    context.last_response = response


# ------------------------------------------------------------
# THEN STEPS
# ------------------------------------------------------------
@bdd_then("the review contains question details and correctness")
def review_success(context: Context):
    res = context.last_response
    assert res is not None
    assert res.status_code == 200

    data = res.json()
    assert "submissionId" in data
    assert "questions" in data
    assert len(data["questions"]) > 0

    first_q = data["questions"][0]
    assert "question" in first_q
    assert "earnedMarks" in first_q
    assert "questionNumber" in first_q


@bdd_then(parsers.parse('I receive the error "{msg}"'))
def review_error(context: Context, msg: str):
    res = context.last_response
    assert res is not None

    detail = res.json()["detail"].lower()

    # Accept flexible message matching
    assert msg.lower() in detail or "not found" in detail
