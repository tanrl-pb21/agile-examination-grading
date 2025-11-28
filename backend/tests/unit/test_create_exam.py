import pytest
from fastapi.testclient import TestClient
from main import app   # adjust import to your project structure

client = TestClient(app)


def test_create_exam_success():
    """Test creating an exam successfully."""
    payload = {
        "title": "Software Engineering Midterm",
        "exam_code": "SE123",
        "course": "1",              
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }

    response = client.post("/exams", json=payload)

    print(response.json())  # (optional debug)

    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Software Engineering Midterm"
    assert data["exam_code"] == "SE123"
    assert data["course"] == 1
    assert data["start_time"] == "09:00"
    assert data["end_time"] == "11:00"


def test_create_exam_missing_title():
    """Test exam creation fails when title is missing."""
    payload = {
        "exam_code": "SE123",
        "date": "2025-01-14",
        "start_time": "09:00",
        "end_time": "11:00"
    }

    response = client.post("/exams", json=payload)

    # FastAPI should reject it because title is required
    assert response.status_code == 422


def test_create_exam_invalid_date_format():
    """Test invalid date format (should fail validation)."""
    payload = {
        "title": "Test Exam",
        "exam_code": "TEST01",
        "date": "14-01-2025",  
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }

    response = client.post("/exams", json=payload)

    assert response.status_code == 400 or response.status_code == 422

def test_get_all_exams():
    response = client.get("/exams")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  

def test_get_exam_by_id_success():
    # Assuming an exam with ID 1 exists in your test DB or mock
    response = client.get("/exams/1")
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "exam_code" in data

def test_get_exam_by_id_not_found():
    response = client.get("/exams/99999")  # non-existent ID
    assert response.status_code == 404

def test_create_exam_invalid_time_format():
    payload = {
        "title": "Test Invalid Time",
        "exam_code": "SE124",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "9am",  # invalid format
        "end_time": "11:00",
        "status": "scheduled"
    }
    response = client.post("/exams", json=payload)
    assert response.status_code == 400 or response.status_code == 422
    
def test_create_exam_past_date():
    payload = {
        "title": "Past Date Exam",
        "exam_code": "SE125",
        "course": "1",
        "date": "2020-01-01",  # past date
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    response = client.post("/exams", json=payload)
    assert response.status_code == 422

def test_create_exam_end_before_start():
    payload = {
        "title": "End Before Start Exam",
        "exam_code": "SE126",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "11:00",
        "end_time": "09:00",  # end before start
        "status": "scheduled"
    }
    response = client.post("/exams", json=payload)
    assert response.status_code == 422
    assert any("End time must be after start time" in err.get("msg", "") for err in response.json()["detail"])


def test_create_exam_scheduling_conflict():
    # First, create an exam at 2026-01-14 09:00-11:00 (should succeed)
    payload1 = {
        "title": "Existing Exam",
        "exam_code": "EXIST001",
        "course": "1",
        "date": "2026-02-14",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    response1 = client.post("/exams", json=payload1)
    assert response1.status_code == 201

    # Now try to create another exam overlapping the same date/time range (should fail)
    payload2 = {
        "title": "Conflicting Exam",
        "exam_code": "CONF001",
        "course": "1",
        "date": "2026-02-14",
        "start_time": "10:00",  # Overlaps with 09:00-11:00
        "end_time": "12:00",
        "status": "scheduled"
    }
    response2 = client.post("/exams", json=payload2)
    assert response2.status_code == 400 or response2.status_code == 422

    # The error detail should mention scheduling conflict
    assert "conflict" in response2.json().get("detail", "").lower()
    
def test_create_exam_missing_exam_code():
    payload = {
        "title": "Missing Exam Code",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00"
    }
    response = client.post("/exams", json=payload)
    assert response.status_code == 422


def test_create_exam_duplicate_exam_code():
    payload1 = {
        "title": "Exam One",
        "exam_code": "DUPLICATE",
        "course": "1",
        "date": "2026-03-10",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    payload2 = {
        "title": "Exam Two",
        "exam_code": "DUPLICATE",
        "course": "1",
        "date": "2026-03-11",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    response1 = client.post("/exams", json=payload1)
    assert response1.status_code == 201

    response2 = client.post("/exams", json=payload2)
    assert response2.status_code == 400 or response2.status_code == 422
    assert "duplicate" in response2.json().get("detail", "").lower()