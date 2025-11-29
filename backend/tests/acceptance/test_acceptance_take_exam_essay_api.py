from __future__ import annotations

from typing import Dict

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when

from src.main import app
from tests.conftest import FakeTakeExamService

scenarios("../feature/take_exam_essay_submission.feature")


@pytest.fixture
def client(monkeypatch) -> TestClient:
    fake_service = FakeTakeExamService()
    monkeypatch.setattr("src.routers.take_exam.take_exam_service", fake_service)
    return TestClient(app)


@pytest.fixture
def context() -> Dict[str, object]:
    return {}


@bdd_given(parsers.parse('the exam code "{exam_code}" is available'))
def exam_available(client: TestClient, context, exam_code: str):
    context["exam_code"] = exam_code
    context["user_id"] = 7
    res = client.get(f"/take-exam/availability/{exam_code}")
    assert res.status_code == 200
    context["client"] = client


@bdd_when(parsers.parse("I submit an essay answer for that exam as user {user_id:d}"))
def submit_essay(context, user_id: int):
    client: TestClient = context["client"]
    exam_code = context["exam_code"]
    payload = {
        "exam_code": exam_code,
        "user_id": user_id,
        "answers": [
            {"question_id": 102, "answer": "The theorem relates sides of a right triangle."}
        ],
    }
    context["response"] = client.post("/take-exam/submit", json=payload)


@bdd_when(parsers.parse("I check if user {user_id:d} already submitted"))
def check_submission(context, user_id: int):
    client: TestClient = context["client"]
    exam_code = context["exam_code"]
    context["response"] = client.get(f"/take-exam/check-submission/{exam_code}/{user_id}")


@bdd_then("the submission is accepted and stored")
def essay_submission_ok(context):
    res = context["response"]
    assert res.status_code == 200
    body = res.json()
    assert body["message"].lower().startswith("exam submitted")
    assert any(ans["question_id"] == 102 for ans in body["submitted_answers"])


@bdd_then("the API reports the submission exists")
def submission_detected(context):
    res = context["response"]
    assert res.status_code == 200
    assert res.json()["submitted"] is True