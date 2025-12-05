import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ============================================================================
# CREATE EXAM TESTS
# ============================================================================


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

    with patch("src.routers.exams.service.add_exam") as mock_add:
        mock_add.return_value = {
            "id": 1,
            **payload
        }
        
        response = client.post("/exams", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Software Engineering Midterm"
        assert data["exam_code"] == "SE123"
        assert data["start_time"] == "09:00"
        assert data["end_time"] == "11:00"


def test_create_exam_missing_title():
    """Test exam creation fails when title is missing."""
    payload = {
        "exam_code": "SE123",
        "course": "1",
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00"
    }

    # Pydantic validation happens before service is called
    response = client.post("/exams", json=payload)
    
    # FastAPI should reject it because title is required
    assert response.status_code == 422


def test_create_exam_invalid_date_format():
    """Test invalid date format (should fail validation)."""
    payload = {
        "title": "Test Exam",
        "exam_code": "TEST01",
        "course": "1",
        "date": "14-01-2025",  
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }

    # Pydantic validator will convert or reject
    response = client.post("/exams", json=payload)
    
    # Should fail validation
    assert response.status_code in (400, 422)


def test_create_exam_invalid_time_format():
    """Test invalid time format."""
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
    
    # Pydantic validation should reject
    assert response.status_code in (400, 422)


def test_create_exam_past_date():
    """Test creating exam with past date."""
    payload = {
        "title": "Past Date Exam",
        "exam_code": "SE125",
        "course": "1",
        "date": "2020-01-01",  # past date
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    
    # Pydantic validator checks for past dates
    response = client.post("/exams", json=payload)
    
    assert response.status_code == 422


def test_create_exam_end_before_start():
    """Test creating exam where end time is before start time."""
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
    
    # Pydantic model_validator checks this
    assert response.status_code == 422


def test_create_exam_missing_exam_code():
    """Test exam creation fails when exam_code is missing."""
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
    """Test creating exam with duplicate exam code."""
    payload = {
        "title": "Exam Two",
        "exam_code": "DUPLICATE",
        "course": "1",
        "date": "2026-03-11",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    
    with patch("src.routers.exams.service.add_exam") as mock_add:
        # Mock duplicate code error
        mock_add.side_effect = ValueError("Exam code 'DUPLICATE' already exists")
        
        response = client.post("/exams", json=payload)
        
        assert response.status_code == 400
        assert "duplicate" in response.json().get("detail", "").lower()


def test_create_exam_scheduling_conflict():
    """Test creating exam with scheduling conflict."""
    payload = {
        "title": "Conflicting Exam",
        "exam_code": "CONF001",
        "course": "1",
        "date": "2026-02-14",
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }
    
    with patch("src.routers.exams.service.add_exam") as mock_add:
        # Mock scheduling conflict error
        mock_add.side_effect = ValueError("Scheduling conflict detected")
        
        response = client.post("/exams", json=payload)
        
        assert response.status_code == 400
        assert "conflict" in response.json().get("detail", "").lower()


# ============================================================================
# GET EXAM TESTS
# ============================================================================


def test_get_all_exams():
    """Test retrieving all exams."""
    with patch("src.routers.exams.service.get_all_exams") as mock_get_all:
        mock_get_all.return_value = [
            {
                "id": 1,
                "title": "Exam 1",
                "exam_code": "E1",
                "course": 1,
                "date": "2026-01-14",
                "start_time": "09:00",
                "end_time": "11:00",
                "status": "scheduled"
            },
            {
                "id": 2,
                "title": "Exam 2",
                "exam_code": "E2",
                "course": 2,
                "date": "2026-01-15",
                "start_time": "14:00",
                "end_time": "16:00",
                "status": "scheduled"
            }
        ]
        
        response = client.get("/exams")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "Exam 1"


def test_get_all_exams_empty():
    """Test retrieving exams when none exist."""
    with patch("src.routers.exams.service.get_all_exams") as mock_get_all:
        mock_get_all.return_value = []
        
        response = client.get("/exams")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


def test_get_exam_by_id_success():
    """Test retrieving a specific exam by ID."""
    with patch("src.routers.exams.service.get_exam") as mock_get:
        mock_get.return_value = {
            "id": 1,
            "title": "Software Engineering Midterm",
            "exam_code": "SE123",
            "course": 1,
            "date": "2026-01-14",
            "start_time": "09:00",
            "end_time": "11:00",
            "status": "scheduled"
        }
        
        response = client.get("/exams/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Software Engineering Midterm"
        assert data["exam_code"] == "SE123"


def test_get_exam_by_id_not_found():
    """Test retrieving non-existent exam returns 404."""
    with patch("src.routers.exams.service.get_exam") as mock_get:
        mock_get.return_value = None
        
        response = client.get("/exams/99999")
        
        assert response.status_code == 404


def test_get_exam_by_invalid_id():
    """Test retrieving exam with invalid ID format."""
    response = client.get("/exams/invalid")
    
    # FastAPI validation should reject non-integer ID
    assert response.status_code == 422


# ============================================================================
# UPDATE EXAM TESTS
# ============================================================================


def test_update_exam_success():
    """Test updating an exam successfully."""
    payload = {
        "title": "Updated Title",
        "exam_code": "SE123",
        "course": "1",
        "date": "2026-01-15",
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }
    
    with patch("src.routers.exams.service.update_exam") as mock_update:
        mock_update.return_value = {
            "id": 1,
            **payload
        }
        
        response = client.put("/exams/1", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"


def test_update_exam_not_found():
    """Test updating non-existent exam returns 404."""
    payload = {
        "title": "Updated Title",
        "exam_code": "SE123",
        "course": "1",
        "date": "2026-01-15",
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }
    
    with patch("src.routers.exams.service.update_exam") as mock_update:
        mock_update.return_value = None
        
        response = client.put("/exams/99999", json=payload)
        
        assert response.status_code == 404


# ============================================================================
# DELETE EXAM TESTS
# ============================================================================


def test_delete_exam_success():
    """Test deleting an exam successfully."""
    with patch("src.routers.exams.service.delete_exam") as mock_delete:
        mock_delete.return_value = {"id": 1}
        
        response = client.delete("/exams/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


def test_delete_exam_not_found():
    """Test deleting non-existent exam returns 404."""
    with patch("src.routers.exams.service.delete_exam") as mock_delete:
        mock_delete.side_effect = ValueError("Exam with id 99999 not found")
        
        response = client.delete("/exams/99999")
        
        assert response.status_code == 404