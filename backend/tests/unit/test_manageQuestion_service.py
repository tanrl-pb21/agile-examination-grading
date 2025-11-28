import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

# CHANGE THIS based on your DB
VALID_EXAM_ID = 1
INVALID_EXAM_ID = 99999


# ----------------------------------------------------------
# 1. SUCCESS CASE — Add MCQ question (valid input)
# ----------------------------------------------------------
def test_add_mcq_question_success():
    unique_text = f"What is 2 + 2? {uuid.uuid4()}"

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

    # Verify stored data
    assert data["question_text"] == unique_text
    assert data["marks"] == 5
    assert data["question_type"] == "mcq"

    # Options
    assert len(data["options"]) == 2
    assert data["options"][1]["is_correct"] is True


# ----------------------------------------------------------
# 2. INVALID EXAM ID
# ----------------------------------------------------------
def test_add_mcq_invalid_exam_id():
    payload = {
        "exam_id": INVALID_EXAM_ID,
        "question_text": f"Invalid exam test {uuid.uuid4()}",
        "marks": 5,
        "options": ["A", "B"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


# ----------------------------------------------------------
# 3. REQUIRE AT LEAST 2 OPTIONS
# ----------------------------------------------------------
def test_add_mcq_requires_minimum_two_options():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": f"Test minimum options {uuid.uuid4()}",
        "marks": 5,
        "options": ["Only one option"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 422  # Pydantic validation
    assert "At least 2 options" in response.text


# ----------------------------------------------------------
# 4. INVALID CORRECT OPTION INDEX
# ----------------------------------------------------------
def test_add_mcq_invalid_correct_option_index():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": f"Invalid index test {uuid.uuid4()}",
        "marks": 5,
        "options": ["A", "B", "C"],
        "correct_option_index": 10,  # out of range
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 422
    assert "Correct option index" in response.text


# ----------------------------------------------------------
# 5. EMPTY QUESTION TEXT
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# 6. INVALID MARK (zero or negative)
# ----------------------------------------------------------
def test_add_mcq_invalid_marks():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": f"Invalid marks test {uuid.uuid4()}",
        "marks": 0,  # invalid
        "options": ["A", "B"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)

    assert response.status_code == 422
    assert "Marks must be at least 1" in response.text


# ----------------------------------------------------------
# 7. CHECK QUESTION STORED CORRECTLY IN EXAM
# ----------------------------------------------------------
def test_mcq_question_retrievable_in_exam_details():
    unique_text = f"Retrieval check question {uuid.uuid4()}"

    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": unique_text,
        "marks": 3,
        "options": ["Yes", "No"],
        "correct_option_index": 0,
    }

    # Add question
    post_res = client.post("/questions/mcq", json=payload)
    assert post_res.status_code == 201
    created = post_res.json()
    question_id = created["id"]

    # Retrieve exam questions
    get_res = client.get(f"/questions/exam/{VALID_EXAM_ID}")
    assert get_res.status_code == 200

    questions = get_res.json()
    found = None
    for q in questions:
        if q["id"] == question_id:
            found = q
            break

    assert found is not None
    assert found["question_text"] == unique_text
    assert found["marks"] == 3
    assert found["question_type"] == "mcq"


# ----------------------------------------------------------
# 8. SYSTEM PREVENTS ADDING QUESTION WHEN ANY REQUIRED FIELD IS EMPTY
# ----------------------------------------------------------
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
            "question_text": f"Missing options {uuid.uuid4()}",
            "marks": 3,
            "options": [],
            "correct_option_index": 0,
        },
        {
            "exam_id": VALID_EXAM_ID,
            "question_text": f"Missing index {uuid.uuid4()}",
            "marks": 3,
            "options": ["A", "B"],
            "correct_option_index": -1,
        },
    ],
)
def test_add_mcq_missing_required_fields(payload):
    response = client.post("/questions/mcq", json=payload)
    assert response.status_code in (400, 422)


# ----------------------------------------------------------
# ESSAY QUESTION TESTS
# ----------------------------------------------------------
def test_add_essay_question_success():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": f"Explain Newton's First Law {uuid.uuid4()}",
        "marks": 10,
        "rubric": "Clarity, accuracy, depth",
        "reference_answer": "An object remains...",
    }

    response = client.post("/questions/essay", json=payload)
    assert response.status_code == 201

    data = response.json()

    assert data["exam_id"] == VALID_EXAM_ID
    assert "Explain Newton's First Law" in data["question_text"]
    assert data["question_type"] == "essay"
    assert data["marks"] == 10

    global last_essay_id
    last_essay_id = data["id"]


def test_get_essay_question():
    response = client.get(f"/questions/{last_essay_id}")
    assert response.status_code == 200


def test_delete_essay_question():
    response = client.delete(f"/questions/{last_essay_id}")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()

    # Verify deletion
    response2 = client.get(f"/questions/{last_essay_id}")
    assert response2.status_code == 404


# ----------------------------------------------------------
# NEGATIVE TESTS
# ----------------------------------------------------------
def test_mcq_invalid_exam_id():
    payload = {
        "exam_id": 999999,
        "question_text": f"Test? {uuid.uuid4()}",
        "marks": 1,
        "options": ["A", "B"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_mcq_less_than_two_options():
    payload = {
        "exam_id": VALID_EXAM_ID,
        "question_text": f"Invalid? {uuid.uuid4()}",
        "marks": 1,
        "options": ["Only one"],
        "correct_option_index": 0,
    }

    response = client.post("/questions/mcq", json=payload)
    assert response.status_code == 422


def test_essay_missing_question_text():
    payload = {"exam_id": VALID_EXAM_ID, "question_text": "", "marks": 5}

    response = client.post("/questions/essay", json=payload)
    assert response.status_code == 422
