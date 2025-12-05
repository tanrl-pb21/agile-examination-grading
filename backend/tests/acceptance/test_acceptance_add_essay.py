import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then, parsers
from main import app

client = TestClient(app)

# Load feature file
scenarios("../feature/addEssay.feature")


@pytest.fixture
def context():
    return {"response": None}


# =======================
# GIVEN STEPS (mocked)
# =======================

@given(parsers.parse("exam {eid:d} exists"))
def exam_exists(eid, monkeypatch):

    def fake_get_exam(self, exam_id):
        if exam_id == eid:
            return {"id": eid, "title": "Mock Exam"}
        return None

    monkeypatch.setattr(
        "src.services.exams_service.ExamService.get_exam",
        fake_get_exam
    )

@given(parsers.parse('exam {eid:d} already has a question "{question}"'))
def exam_has_question(eid, question, monkeypatch):

    def fake_add(*args, **kwargs):
        raise ValueError("A question with the same text already exists")

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_add
    )


# =======================
# WHEN STEPS
# =======================

@when(parsers.parse(
    'the instructor submits a new essay question "{text}" with {marks:d} marks'
), target_fixture="context")
def submit_success(text, marks, context, monkeypatch):

    def fake_add(exam_id, question_text, marks, rubric, word_limit, reference_answer):
        return {
            "id": 123,
            "question_text": question_text,
            "question_type": "essay",
            "marks": marks,
            "rubric": rubric,
            "exam_id": exam_id
        }

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_add
    )

    payload = {
        "exam_id": 1,
        "question_text": text,
        "marks": marks,
        "rubric": "Default"
    }
    context["response"] = client.post("/questions/essay", json=payload)
    return context


@when("the instructor submits an essay question with empty text",
      target_fixture="context")
def submit_empty_text(context, monkeypatch):

    def fake_add(*args, **kwargs):
        raise ValueError("Should not be called")

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_add
    )

    payload = {
        "exam_id": 1,
        "question_text": "",
        "marks": 10,
        "rubric": "Default"
    }
    context["response"] = client.post("/questions/essay", json=payload)
    return context


@when(parsers.parse("the instructor submits an essay question to exam {eid:d}"),
      target_fixture="context")
def submit_invalid_exam(eid, context, monkeypatch):

    def fake_raise(*args, **kwargs):
        raise ValueError(f"Exam with id {eid} not found")

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_raise
    )

    payload = {
        "exam_id": eid,
        "question_text": "Valid",
        "marks": 10,
        "rubric": "Default"
    }
    context["response"] = client.post("/questions/essay", json=payload)
    return context


@when(parsers.parse('the instructor submits another essay question "{question}"'),
      target_fixture="context")
def submit_duplicate(question, context, monkeypatch):

    def fake_raise(*args, **kwargs):
        raise ValueError("already exists")

    monkeypatch.setattr(
        "src.routers.question.service.add_essay_question",
        fake_raise
    )

    payload = {
        "exam_id": 1,
        "question_text": question,
        "marks": 10,
        "rubric": "Default"
    }
    context["response"] = client.post("/questions/essay", json=payload)
    return context


# =======================
# THEN STEPS
# =======================

@then(parsers.parse("the system should return {code:d}"))
def status_code(context, code):
    assert context["response"].status_code == code


@then(parsers.parse('the response should contain "{text}"'))
def response_contains(context, text):
    assert text in context["response"].text


@then(parsers.parse('the error should contain "{msg}"'))
def error_contains(context, msg):
    detail = context["response"].json().get("detail", "")
    assert msg.lower() in detail.lower()
