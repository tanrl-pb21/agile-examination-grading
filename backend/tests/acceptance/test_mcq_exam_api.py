import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then, parsers
from main import app

client = TestClient(app)

# Load feature file
scenarios("../feature/addMCQ.feature")


# -----------------------------
# Shared context fixture
# -----------------------------
@pytest.fixture
def context():
    return {
        "response": None,
        "question_id": None,
        "exam_id": None,
        "existing_question_text": None,
    }


# -----------------------------
# Error keyword mapping
# -----------------------------
ERROR_KEYWORDS = {
    "value_error, at least 2 options required": "at least 2 options",
    "value_error, correct option index out of range": "correct option index",
    "value_error, question text cannot be empty": "question text cannot be empty",
    "value_error, duplicate options not allowed": "duplicate options not allowed",
    "exam not found": "exam not found",
    "question already exists": "question already exists",
}


# -----------------------------
# GIVEN STEPS
# -----------------------------
@given(parsers.parse("exam {exam_id:d} exists"))
def exam_exists(exam_id, context):
    context["exam_id"] = exam_id


@given(parsers.parse("no exam exists with ID {exam_id:d}"))
def exam_not_exists(exam_id, context):
    context["exam_id"] = exam_id


@given(parsers.parse('exam {exam_id:d} already has a question "{question_text}"'))
def exam_has_question(exam_id, question_text, context):
    context["exam_id"] = exam_id
    context["existing_question_text"] = question_text


# -----------------------------
# WHEN STEPS
# -----------------------------
@when(
    parsers.parse(
        'the instructor adds an MCQ with text "{text}", marks {marks:d}, options "{options}", correct index {correct_index:d}'
    )
)
def add_mcq(text, marks, options, correct_index, context, monkeypatch):
    from fastapi import HTTPException

    option_list = [o.strip() for o in options.split(",")]

    def fake_add_mcq_question(
        self, exam_id, question_text, marks, options, correct_option_index
    ):
        # Validation errors (422)
        if not question_text.strip():
            raise HTTPException(
                status_code=422, detail=[{"msg": "Question text cannot be empty"}]
            )
        if len(options) < 2:
            raise HTTPException(
                status_code=422, detail=[{"msg": "At least 2 options are required"}]
            )
        if len(set([o.strip().lower() for o in options])) != len(options):
            raise HTTPException(
                status_code=422, detail=[{"msg": "Duplicate options not allowed"}]
            )
        if correct_option_index < 0 or correct_option_index >= len(options):
            raise HTTPException(
                status_code=422,
                detail=[
                    {
                        "msg": f"Correct option index must be between 0 and {len(options)-1}"
                    }
                ],
            )
        # Business logic errors (400)
        if exam_id == 99999:
            raise HTTPException(status_code=400, detail="Exam not found")
        if context.get("existing_question_text") == question_text:
            raise HTTPException(status_code=400, detail="Question already exists")
        # Success
        return {
            "id": 100,
            "exam_id": exam_id,
            "question_text": question_text,
            "marks": marks,
            "question_type": "mcq",
            "options": [
                {"text": o, "is_correct": i == correct_option_index}
                for i, o in enumerate(options)
            ],
        }

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.add_mcq_question",
        fake_add_mcq_question,
    )

    payload = {
        "exam_id": context["exam_id"],
        "question_text": text,
        "marks": marks,
        "options": option_list,
        "correct_option_index": correct_index,
    }

    try:
        response = client.post("/questions/mcq", json=payload)
    except HTTPException as e:
        context["response"] = {"status_code": e.status_code, "error": e.detail}
    else:
        context["response"] = response
        if response.status_code == 201:
            context["question_id"] = response.json()["id"]

    return context


@when(
    parsers.parse(
        'the instructor updates the MCQ {question_id:d} with text "{text}", marks {marks:d}, options "{options}", correct index {correct_index:d}'
    )
)
def update_mcq(question_id, text, marks, options, correct_index, context, monkeypatch):
    option_list = [o.strip() for o in options.split(",")]

    def fake_update_mcq(
        self, question_id, question_text, marks, options, correct_option_index
    ):
        return {
            "id": question_id,
            "question_text": question_text,
            "marks": marks,
            "question_type": "mcq",
            "options": [
                {"text": o, "is_correct": i == correct_option_index}
                for i, o in enumerate(options)
            ],
        }

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.update_mcq_question",
        fake_update_mcq,
    )

    payload = {
        "question_text": text,
        "marks": marks,
        "options": option_list,
        "correct_option_index": correct_index,
    }

    context["response"] = client.put(f"/questions/mcq/{question_id}", json=payload)
    return context


@when(parsers.parse("the instructor deletes the MCQ with ID {question_id:d}"))
def delete_mcq(question_id, context, monkeypatch):
    def fake_delete(self, question_id):
        return {"id": question_id, "deleted": True}

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.delete_question", fake_delete
    )
    context["response"] = client.delete(f"/questions/{question_id}")
    return context


# -----------------------------
# THEN STEPS
# -----------------------------
@then(parsers.parse("the MCQ has correct option at index {index:d}"))
def check_correct_option(context, index):
    resp = context["response"]
    data = resp.json()
    options = data.get("options", [])
    assert options[index]["is_correct"] is True


@then(parsers.parse("the system returns status code {code:d}"))
def check_status_code(context, code):
    resp = context["response"]
    if isinstance(resp, dict) and "status_code" in resp:
        assert resp["status_code"] == code
    else:
        assert resp.status_code == code


@then(parsers.parse('the response contains error "{text}"'))
def check_error_message(context, text):
    resp = context["response"]

    # Determine keyword to check
    keyword = ERROR_KEYWORDS.get(text, text).lower()

    # Case 1: If the response is a dict (from monkeypatch / exception)
    if isinstance(resp, dict) and "error" in resp:
        assert keyword in str(resp["error"]).lower()
        return

    # Case 2: FastAPI / Pydantic validation errors (422)
    data = resp.json()
    if resp.status_code == 422:
        details = data.get("detail", [])
        if isinstance(details, list):
            messages = [str(e.get("msg", e.get("error", ""))).lower() for e in details]
            assert any(
                keyword in m for m in messages
            ), f"Expected '{keyword}' in {messages}"
        else:
            assert keyword in str(details).lower()
        return

    # Case 3: Other HTTP errors (400, etc.)
    detail_msg = str(data.get("detail", "")).lower()
    assert keyword in detail_msg, f"Expected '{keyword}' in '{detail_msg}'"

