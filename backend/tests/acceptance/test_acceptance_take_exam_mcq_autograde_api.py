from __future__ import annotations

from typing import Dict

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when

from src.main import app
from tests.conftest import FakeTakeExamService

scenarios("../feature/take_exam_mcq_autograde.feature")


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


@bdd_when(parsers.parse("I submit the correct MCQ answer for that exam as user {user_id:d}"))
def submit_correct_mcq(context, user_id: int):
    client: TestClient = context["client"]
    exam_code = context["exam_code"]
    payload = {
        "exam_code": exam_code,
        "user_id": user_id,
        "answers": [{"question_id": 101, "answer": 202}],
    }
    context["response"] = client.post("/take-exam/submit", json=payload)


@bdd_when(parsers.parse("I submit a wrong MCQ answer for that exam as user {user_id:d}"))
def submit_wrong_mcq(context, user_id: int):
    client: TestClient = context["client"]
    exam_code = context["exam_code"]
    payload = {
        "exam_code": exam_code,
        "user_id": user_id,
        "answers": [{"question_id": 101, "answer": 201}],
    }
    context["response"] = client.post("/take-exam/submit", json=payload)


@bdd_then("the MCQ answer is auto-graded as correct")
def mcq_auto_graded(context):
    res = context["response"]
    assert res.status_code == 200
    body = res.json()
    assert body["auto_score"] == 1
    assert body["total_mcq"] == 1


@bdd_then("the MCQ answer is auto-graded as incorrect")
def mcq_auto_incorrect(context):
    res = context["response"]
    assert res.status_code == 200
    body = res.json()
    assert body["auto_score"] == 0
    assert body["total_mcq"] == 1