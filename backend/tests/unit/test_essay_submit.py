import pytest
from fastapi.testclient import TestClient
from main import app   # adjust import to your project structure
import json

client = TestClient(app)

def test_submit_single_essay():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {
                "question_id": 7,
                "answer": "This is my essay answer."
            }
        ]
    }

    response = client.post(
        "/exams/submit",
        json=payload
    )

    assert response.status_code == 200, f"Response body: {response.text}"

    data = response.json()
    assert data["grade"] == "Pending"
    assert "total_score" in data
    assert "max_score" in data
    assert "submitted" in data["message"].lower()

def test_submit_multiple_essays():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": "Essay answer 1."},
            {"question_id": 21, "answer": "Essay answer 2."},
        ]
    }

    response = client.post("/exams/submit", json=payload)

    assert response.status_code == 200, f"Response body: {response.text}"

    data = response.json()
    assert data["grade"].lower() == "pending"
    assert "total_score" in data
    assert "max_score" in data
    assert "submitted" in data["message"].lower()


def test_submit_empty_essay_answer():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": ""}
        ]
    }

    response = client.post("/exams/submit", json=payload)

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

    data = response.json()
    

def test_submit_very_long_essay():
    long_text = "Lorem ipsum " * 1000  # ~11000 chars

    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7, "answer": long_text}
        ]
    }

    response = client.post("/exams/submit", json=payload)

    assert response.status_code == 200, f"Response body: {response.text}"

    data = response.json()
    assert data["grade"].lower() == "pending"
    assert "submitted" in data["message"].lower()


def test_submit_missing_answer_field():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": [
            {"question_id": 7}  # no "answer" key
        ]
    }

    response = client.post("/exams/submit", json=payload)

    assert response.status_code == 422, f"Expected 422 Unprocessable Entity, got {response.status_code}"

    data = response.json()
    assert "detail" in data
    


def test_submit_no_answers():
    payload = {
        "exam_code": "666",
        "user_id": 1,
        "answers": []
    }

    response = client.post("/exams/submit", json=payload)

    assert response.status_code == 200, f"Expected 200 OK or adjust based on your API, got {response.status_code}"
    
    data = response.json()