import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ---------------------------------------------------------
# 1. SUCCESS — ADD MCQ QUESTION
# ---------------------------------------------------------
def test_add_mcq_success(monkeypatch):

    def fake_add_mcq_question(
        self, exam_id, question_text, marks, options, correct_option_index
    ):
        return {
            "id": 100,
            "exam_id": exam_id,
            "question_text": question_text,
            "marks": marks,
            "question_type": "mcq",
            "options": [
                {"text": opt, "is_correct": i == correct_option_index}
                for i, opt in enumerate(options)
            ],
        }

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.add_mcq_question",
        fake_add_mcq_question,
    )

    payload = {
        "exam_id": 1,
        "question_text": "What is 2 + 2?",
        "marks": 5,
        "options": ["3", "4"],
        "correct_option_index": 1,
    }

    res = client.post("/questions/mcq", json=payload)

    assert res.status_code == 201
    assert res.json()["question_type"] == "mcq"
    assert res.json()["options"][1]["is_correct"] is True


# ---------------------------------------------------------
# 2. VALIDATION — EMPTY QUESTION TEXT
# ---------------------------------------------------------
def test_add_mcq_empty_question():

    payload = {
        "exam_id": 1,
        "question_text": "  ",
        "marks": 5,
        "options": ["A", "B"],
        "correct_option_index": 0,
    }

    res = client.post("/questions/mcq", json=payload)
    assert res.status_code == 422  # Pydantic validation triggers 422


# ---------------------------------------------------------
# 3. VALIDATION — LESS THAN 2 OPTIONS
# ---------------------------------------------------------
def test_add_mcq_not_enough_options():

    payload = {
        "exam_id": 1,
        "question_text": "Test?",
        "marks": 5,
        "options": ["Only one"],
        "correct_option_index": 0,
    }

    res = client.post("/questions/mcq", json=payload)
    assert res.status_code == 422  # Pydantic validation


# ---------------------------------------------------------
# 4. VALIDATION — INVALID CORRECT OPTION INDEX
# ---------------------------------------------------------
def test_add_mcq_invalid_correct_index():

    payload = {
        "exam_id": 1,
        "question_text": "Test?",
        "marks": 5,
        "options": ["A", "B"],
        "correct_option_index": 5,  # invalid
    }

    res = client.post("/questions/mcq", json=payload)
    assert res.status_code == 422  # Pydantic validation


# ---------------------------------------------------------
# 5. GET MCQ QUESTION BY ID
# ---------------------------------------------------------
def test_get_mcq_question(monkeypatch):

    def fake_get(self, question_id):
        return {
            "id": question_id,
            "exam_id": 1,
            "question_text": "Sample?",
            "question_type": "mcq",
            "marks": 2,
            "options": [{"text": "Yes", "is_correct": True}],
        }

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.get_question", fake_get
    )

    res = client.get("/questions/100")
    assert res.status_code == 200
    assert res.json()["question_type"] == "mcq"


# ---------------------------------------------------------
# 6. GET EXAM QUESTIONS
# ---------------------------------------------------------
def test_get_all_questions_for_exam(monkeypatch):

    def fake_get(self, exam_id):
        return [
            {
                "id": 1,
                "exam_id": exam_id,
                "question_text": "Q1",
                "question_type": "mcq",
            },
            {
                "id": 2,
                "exam_id": exam_id,
                "question_text": "Q2",
                "question_type": "essay",
            },
        ]

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.get_exam_questions", fake_get
    )

    res = client.get("/questions/exam/1")
    assert res.status_code == 200
    assert len(res.json()) == 2


# ---------------------------------------------------------
# 7. DELETE MCQ QUESTION
# ---------------------------------------------------------
def test_delete_mcq_question(monkeypatch):

    def fake_delete(self, question_id):
        return True

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.delete_question", fake_delete
    )

    res = client.delete("/questions/100")
    assert res.status_code == 200
    assert "deleted" in res.json()["message"].lower()


# ---------------------------------------------------------
# 8. UPDATE MCQ QUESTION
# ---------------------------------------------------------
def test_update_mcq_question(monkeypatch):

    def fake_update(
        self, question_id, question_text, marks, options, correct_option_index
    ):
        return {
            "id": question_id,
            "question_text": question_text,
            "marks": marks,
            "question_type": "mcq",
        }

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.update_mcq_question", fake_update
    )

    payload = {
        "question_text": "Updated question?",
        "marks": 10,
        "options": ["Yes", "No"],
        "correct_option_index": 0,
    }

    res = client.put("/questions/mcq/100", json=payload)
    assert res.status_code == 200
    assert res.json()["question_text"] == "Updated question?"


# ---------------------------------------------------------
# 9. DUPLICATE OPTIONS NOT ALLOWED
# ---------------------------------------------------------
def test_add_mcq_duplicate_options():

    payload = {
        "exam_id": 1,
        "question_text": "Is water wet?",
        "marks": 5,
        "options": ["Yes", "Yes"],  # Duplicate option text
        "correct_option_index": 0,
    }

    res = client.post("/questions/mcq", json=payload)
    assert res.status_code == 400
    assert "duplicate" in res.json()["detail"].lower()


# ---------------------------------------------------------
# 10. MINIMUM OPTIONS (BOUNDARY TEST)
# ---------------------------------------------------------
def test_add_mcq_min_options(monkeypatch):

    def fake_add_mcq_question(
        self, exam_id, question_text, marks, options, correct_option_index
    ):
        return {
            "id": 101,
            "exam_id": exam_id,
            "question_text": question_text,
            "marks": marks,
            "options": options,
        }

    monkeypatch.setattr(
        "src.services.question_service.QuestionService.add_mcq_question",
        fake_add_mcq_question,
    )

    payload = {
        "exam_id": 1,
        "question_text": "Boundary test?",
        "marks": 3,
        "options": ["Yes", "No"],
        "correct_option_index": 1,
    }

    res = client.post("/questions/mcq", json=payload)
    assert res.status_code == 201
    assert len(res.json()["options"]) == 2


# ---------------------------------------------------------
# 11. CORRECT OPTION AT FIRST AND LAST POSITIONS
# ---------------------------------------------------------
@pytest.mark.parametrize("correct_index", [0, 3])
def test_add_mcq_correct_option_boundaries(monkeypatch, correct_index):

    def fake_add_mcq_question(
        self, exam_id, question_text, marks, options, correct_option_index
    ):
        return {
            "id": 102,
            "exam_id": exam_id,
            "question_text": question_text,
            "marks": marks,
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
        "exam_id": 1,
        "question_text": "Boundary index test?",
        "marks": 4,
        "options": ["A", "B", "C", "D"],
        "correct_option_index": correct_index,
    }

    res = client.post("/questions/mcq", json=payload)
    assert res.status_code == 201
    assert res.json()["options"][correct_index]["is_correct"] is True

