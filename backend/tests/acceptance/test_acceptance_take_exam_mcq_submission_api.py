from __future__ import annotations

from typing import Dict

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when

from src.main import app
from tests.conftest import FakeTakeExamService

scenarios("../feature/take_exam_mcq_submission.feature")


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
    res = client.get(f"/take-exam/availability/{exam_code}")
    assert res.status_code == 200
    context["client"] = client


@bdd_when(parsers.parse("I submit a multiple-choice answer for that exam as user {user_id:d}"))
def submit_mcq(context, user_id: int):
    client: TestClient = context["client"]
    exam_code = context["exam_code"]
    payload = {
        "exam_code": exam_code,
        "user_id": user_id,
        "answers": [{"question_id": 101, "answer": 201}],
    }
    context["response"] = client.post("/take-exam/submit", json=payload)


@bdd_when(parsers.parse("I submit multiple answers for that exam as user {user_id:d}"))
def submit_multiple(context, user_id: int):
    client: TestClient = context["client"]
    exam_code = context["exam_code"]
    payload = {
        "exam_code": exam_code,
        "user_id": user_id,
        "answers": [
            {"question_id": 101, "answer": 202},
            {"question_id": 102, "answer": "Essay body"},
        ],
    }
    context["response"] = client.post("/take-exam/submit", json=payload)


@bdd_then("the submission is recorded with MCQ grading info")
def mcq_submission_recorded(context):
    res = context["response"]
    assert res.status_code == 200
    body = res.json()
    assert body["total_mcq"] == 1
    assert body["auto_score"] in (0, 1)
    assert any(ans["question_id"] == 101 for ans in body["submitted_answers"])


@bdd_then("all answers are echoed back in the submission response")
def all_answers_echoed(context):
    res = context["response"]
    assert res.status_code == 200
    body = res.json()
    returned_ids = {ans["question_id"] for ans in body["submitted_answers"]}
    assert {101, 102}.issubset(returned_ids)