import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

# CHANGE THIS based on your DB
VALID_EXAM_ID = 1
INVALID_EXAM_ID = 99999


# =====================================================================
# 1. SUCCESS CASE — Add MCQ question (valid input)
# =====================================================================
def test_add_mcq_question_success():
    unique_text = f"What is 2 + 2? {uuid.uuid4()}"  # prevent duplicate

    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": unique_text,
        "marks": 5,
        "options": ["1", "4"],
        "correct_option_index": 1,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["question_text"] == unique_text
    assert data["marks"] == 5
    assert data["question_type"] == "mcq"
    assert len(data["options"]) == 2
    assert data["options"][1]["is_correct"] is True

    global last_mcq_id
    last_mcq_id = data["id"]


# =====================================================================
# 2. MCQ UPDATE TEST
# =====================================================================
def test_update_mcq_question_success():
    updated_text = f"Updated MCQ {uuid.uuid4()}"

    payload = {
        "question_text": updated_text,
        "marks": 10,
        "options": ["AAA", "BBB", "CCC"],
        "correct_option_index": 2,
    }

    response = client.put(f"/questions/mcq/{last_mcq_id}", json=payload)
    assert response.status_code == 200

    data = response.json()

    assert data["question_text"] == updated_text
    assert data["marks"] == 10
    assert data["options"][2]["is_correct"] is True


# =====================================================================
# 3. MCQ DELETE TEST
# =====================================================================
def test_delete_mcq_question():
    response = client.delete(f"/questions/{last_mcq_id}")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()

    # Verify gone
    response2 = client.get(f"/questions/{last_mcq_id}")
    assert response2.status_code == 404


# =====================================================================
# 4. INVALID EXAM ID
# =====================================================================
def test_add_mcq_invalid_exam_id():
    payload = {
        "exam_id": INVALID_EXAM_ID,
        "question_text": "Invalid exam test",
        "marks": 5,
        "options": ["A", "B"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


# =====================================================================
# 5. REQUIRE AT LEAST 2 OPTIONS
# =====================================================================
def test_add_mcq_requires_minimum_two_options():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": "Test minimum options",
        "marks": 5,
        "options": ["Only one option"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 422
    assert "At least 2 options" in response.text


# =====================================================================
# 6. INVALID CORRECT OPTION INDEX
# =====================================================================
def test_add_mcq_invalid_correct_option_index():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": "Invalid index test",
        "marks": 5,
        "options": ["A", "B", "C"],
        "correct_option_index": 10,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 422
    assert "Correct option index" in response.text


# =====================================================================
# 7. EMPTY QUESTION TEXT
# =====================================================================
def test_add_mcq_empty_question_text():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": "  ",
        "marks": 5,
        "options": ["A", "B"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 422
    assert "Question text cannot be empty" in response.text


# =====================================================================
# 8. INVALID MARK (zero or negative)
# =====================================================================
def test_add_mcq_invalid_marks():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": "Invalid marks test",
        "marks": 0,
        "options": ["A", "B"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 422
    assert "Marks must be at least 1" in response.text


# =====================================================================
# 9. CHECK QUESTION STORED CORRECTLY (GET /questions/exam/{id})
# =====================================================================
def test_mcq_question_retrievable_in_exam_details():
    unique_text = f"Retrieval check {uuid.uuid4()}"

    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": unique_text,
        "marks": 3,
        "options": ["Yes", "No"],
        "correct_option_index": 0,
    }

    post_res = client.post("/questions/mcq", json=payload)
    assert post_res.status_code == 201
    created = post_res.json()
    question_id = created["id"]

    get_res = client.get(f"/questions/exam/{VALID_EXAM_ID}")
    assert get_res.status_code == 200

    questions = get_res.json()
    found = next((q for q in questions if q["id"] == question_id), None)

    assert found is not None
    assert found["question_text"] == unique_text
    assert found["marks"] == 3
    assert found["question_type"] == "mcq"


# =====================================================================
# 10. SYSTEM PREVENTS ADDING QUESTION WHEN REQUIRED FIELDS ARE EMPTY
# =====================================================================
@pytest.mark.parametrize(
    "payload",
    [
        {
            "exam_id": VALID_EXAM_ID,
            "question_text": "",
            "marks": 3,
            "options": ["A", "B"],
            "correct_option_index": 0,
        },
        {
            "exam_id": VALID_EXAM_ID,
            "question_text": "Missing options",
            "marks": 3,
            "options": [],
            "correct_option_index": 0,
        },
        {
            "exam_id": VALID_EXAM_ID,
            "question_text": "Missing index",
            "marks": 3,
            "options": ["A", "B"],
            "correct_option_index": -1,
        },
    ],
)
def test_add_mcq_missing_required_fields(payload):
    response = client.post("/questions/mcq", json=payload)
    assert response.status_code in (400, 422)


# =====================================================================
# 11. ESSAY QUESTION – ADD SUCCESS
# =====================================================================
def test_add_essay_question_success():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": "Explain Newton's First Law.",
        "marks": 10,
        "rubric": "Clarity, accuracy, depth",
        "reference_answer": "An object remains...",
    }

    response = client.post("/questions/essay", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["exam_id"] == VALID_EXAM_ID
    assert data["question_text"] == "Explain Newton's First Law."
    assert data["question_type"] == "essay"

    global last_essay_id
    last_essay_id = data["id"]


# =====================================================================
# 12. ESSAY — UPDATE
# =====================================================================
def test_update_essay_question_success():
    updated_text = f"Updated Essay {uuid.uuid4()}"

    payload = {
        "question_text": updated_text,
        "marks": 15,
        "rubric": "Updated rubric",
        "reference_answer": "Updated answer",
    }

    response = client.put(f"/questions/essay/{last_essay_id}", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["question_text"] == updated_text
    assert data["marks"] == 15


# =====================================================================
# 13. ESSAY — GET
# =====================================================================
def test_get_essay_question():
    response = client.get(f"/questions/{last_essay_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == last_essay_id
    assert data["question_type"] == "essay"


# =====================================================================
# 14. ESSAY — DELETE
# =====================================================================
def test_delete_essay_question():
    response = client.delete(f"/questions/{last_essay_id}")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()

    # verify removed
    response2 = client.get(f"/questions/{last_essay_id}")
    assert response2.status_code == 404


# =====================================================================
# 15. ESSAY NEGATIVE TEST — EMPTY TEXT
# =====================================================================
def test_essay_missing_question_text():
    payload = {"exam_id": VALID_EXAM_ID, "question_text": "", "marks": 5}

    response = client.post("/questions/essay", json=payload)
    assert response.status_code == 422
