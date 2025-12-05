import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ---------------------------------------------------------
# 1. SUCCESS
# ---------------------------------------------------------
def test_add_essay_question_success(monkeypatch):

    def fake_add_essay_question(exam_id, question_text, marks, rubric, word_limit, reference_answer):
        return {
            "id": 99,
            "question_text": question_text,
            "question_type": "essay",
            "marks": marks,
            "rubric": rubric,
            "exam_id": exam_id,
            "reference_answer": reference_answer,
            "word_limit": word_limit,
        }

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_add_essay_question
    )

    payload = {
        "exam_id": 1,
        "question_text": "Explain gravity",
        "marks": 10,
        "rubric": "Clarity",
        "reference_answer": "Objects attract"
    }

    res = client.post("/questions/essay", json=payload)

    assert res.status_code == 201
    assert res.json()["question_type"] == "essay"
    assert res.json()["question_text"] == "Explain gravity"


# ---------------------------------------------------------
# 2. EMPTY QUESTION
# ---------------------------------------------------------
def test_add_essay_question_empty_text(monkeypatch):
    def fake_raise(*args, **kwargs):
        raise ValueError("Question text is required")

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_raise
    )

    payload = {
        "exam_id": 1,
        "question_text": "   ",
        "marks": 10,
        "rubric": "x"
    }

    res = client.post("/questions/essay", json=payload)

    # Because Pydantic rejects blank question_text BEFORE service runs
    assert res.status_code == 422

# ---------------------------------------------------------
# 3. EXAM NOT FOUND
# ---------------------------------------------------------
def test_add_essay_question_exam_not_found(monkeypatch):

    def fake_raise(*args, **kwargs):
        raise ValueError("Exam with id 99 not found")

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_raise
    )

    payload = {
        "exam_id": 99,
        "question_text": "Valid",
        "marks": 10,
        "rubric": "x"
    }

    res = client.post("/questions/essay", json=payload)

    assert res.status_code == 400
    assert "Exam with id 99 not found" in res.json()["detail"]


# ---------------------------------------------------------
# 4. DUPLICATE QUESTION
# ---------------------------------------------------------
def test_add_essay_question_duplicate(monkeypatch):

    def fake_raise(*args, **kwargs):
        raise ValueError("A question with the same text already exists")

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_raise
    )

    payload = {
        "exam_id": 1,
        "question_text": "What is AI?",
        "marks": 10,
        "rubric": "x"
    }

    res = client.post("/questions/essay", json=payload)

    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]
