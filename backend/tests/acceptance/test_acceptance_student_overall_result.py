import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import MagicMock

from main import app

client = TestClient(app)
scenarios("../feature/student_overall_result.feature")

STATE = {}


# -------------------------------------------------------
# GIVEN
# -------------------------------------------------------

@given("the service returns two submissions for user 1")
def given_two(monkeypatch):
    mock_data = [
        {
            "id": 10,
            "submission_id": "sub10",
            "exam_title": "Math Exam",
            "exam_id": "MATH01",
            "date": "01/02/2025",
            "time": "09:30:00",
            "score": "45/50",
            "percentage": "90.0%",
            "status": "graded",
        },
        {
            "id": 11,
            "submission_id": "sub11",
            "exam_title": "Science Exam",
            "exam_id": "SCI01",
            "date": "01/03/2025",
            "time": "10:15:00",
            "score": None,
            "percentage": None,
            "status": "pending",
        },
    ]

    monkeypatch.setattr(
        "src.services.submission_service.SubmissionService.get_student_submissions",
        MagicMock(return_value=mock_data),
    )


@given("the service returns an empty result list for user 1")
def given_empty(monkeypatch):
    monkeypatch.setattr(
        "src.services.submission_service.SubmissionService.get_student_submissions",
        MagicMock(return_value=[]),
    )


@given(parsers.parse('the service raises ValueError("{msg}") for user 999'))
def given_error(monkeypatch, msg):
    monkeypatch.setattr(
        "src.services.submission_service.SubmissionService.get_student_submissions",
        MagicMock(side_effect=ValueError(msg)),
    )


@given("the service returns a pending submission for user 2")
def given_pending(monkeypatch):
    mock_data = [
        {
            "id": 21,
            "submission_id": "sub21",
            "exam_title": "Biology Exam",
            "exam_id": "BIO01",
            "date": "02/01/2025",
            "time": "14:00:00",
            "score": None,
            "percentage": None,
            "status": "pending",
        }
    ]

    monkeypatch.setattr(
        "src.services.submission_service.SubmissionService.get_student_submissions",
        MagicMock(return_value=mock_data),
    )


# -------------------------------------------------------
# WHEN
# -------------------------------------------------------

@when("the student requests their overall result")
def call_user1():
    STATE["response"] = client.get("/submissions/student/1")


@when(parsers.parse("the student requests their overall result for user {uid:d}"))
def call_user(uid):
    STATE["response"] = client.get(f"/submissions/student/{uid}")


# -------------------------------------------------------
# THEN
# -------------------------------------------------------

@then("the API should return 2 results")
def check_two():
    assert len(STATE["response"].json()) == 2


@then(parsers.parse('result 1 should have status "{status}"'))
def r1_status(status):
    assert STATE["response"].json()[0]["status"] == status


@then(parsers.parse('result 1 should have score "{score}"'))
def r1_score(score):
    assert STATE["response"].json()[0]["score"] == score


@then(parsers.parse('result 1 should have percentage "{pct}"'))
def r1_pct(pct):
    assert STATE["response"].json()[0]["percentage"] == pct


@then(parsers.parse('result 2 should have status "{status}"'))
def r2_status(status):
    assert STATE["response"].json()[1]["status"] == status


@then("result 2 should have no score and no percentage")
def r2_no_score():
    r2 = STATE["response"].json()[1]
    assert r2["score"] is None
    assert r2["percentage"] is None


@then("the API should return an empty list")
def empty_list():
    assert STATE["response"].json() == []


@then("the response status code should be 404")
def status_404():
    assert STATE["response"].status_code == 404


@then(parsers.parse('the response detail should be "{msg}"'))
def error_message(msg):
    assert STATE["response"].json()["detail"] == msg


@then("the API should return 1 result")
def one_result():
    assert len(STATE["response"].json()) == 1


@then('the result should have status "pending"')
def pending_status():
    assert STATE["response"].json()[0]["status"] == "pending"


@then("the result should have no score and no percentage")
def pending_no_score():
    r = STATE["response"].json()[0]
    assert r["score"] is None
    assert r["percentage"] is None
