import pytest
import jwt
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from datetime import date, datetime, timedelta
import os


# ============================================================================
# JWT CONFIGURATION - MUST MATCH main.py
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"


def create_test_token(user_id: int = 1) -> str:
    """Create a valid JWT token for testing"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_auth_headers(user_id: int = 1) -> dict:
    """Get Authorization headers with valid JWT token"""
    token = create_test_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get valid auth headers for test requests"""
    return get_auth_headers(user_id=1)


@pytest.fixture
def mock_exam_service():
    """Mock the ExamService to avoid database calls"""
    with patch('src.routers.exams.service') as mock_service:
        yield mock_service


@pytest.fixture
def sample_exam():
    """Sample exam data"""
    return {
        "id": 1,
        "title": "Math Final",
        "exam_code": "MATH101",
        "course": "1",
        "date": "2026-06-15",
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled",
        "created_by": 1
    }


@pytest.fixture
def future_date():
    """Get a date in the future"""
    return (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")


# ============================================================================
# CREATE EXAM TESTS
# ============================================================================

def test_create_exam_success(client, auth_headers, future_date):
    """Test creating an exam successfully."""
    payload = {
        "title": "Software Engineering Midterm",
        "exam_code": "SE123",
        "course": "1",
        "date": future_date,
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }

    with patch("src.routers.exams.service.add_exam") as mock_add:
        mock_add.return_value = {
            "id": 1,
            "created_by": 1,
            **payload
        }
        
        response = client.post("/exams", json=payload, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Software Engineering Midterm"
        assert data["exam_code"] == "SE123"
        assert data["start_time"] == "09:00"
        assert data["end_time"] == "11:00"


def test_create_exam_missing_title(client, auth_headers, future_date):
    """Test exam creation fails when title is missing."""
    payload = {
        "exam_code": "SE123",
        "course": "1",
        "date": future_date,
        "start_time": "09:00",
        "end_time": "11:00"
    }

    response = client.post("/exams", json=payload, headers=auth_headers)
    
    assert response.status_code == 422


def test_create_exam_invalid_date_format(client, auth_headers):
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

    response = client.post("/exams", json=payload, headers=auth_headers)
    
    assert response.status_code in (400, 422)


def test_create_exam_invalid_time_format(client, auth_headers, future_date):
    """Test invalid time format."""
    payload = {
        "title": "Test Invalid Time",
        "exam_code": "SE124",
        "course": "1",
        "date": future_date,
        "start_time": "9am",  # invalid format
        "end_time": "11:00",
        "status": "scheduled"
    }
    
    response = client.post("/exams", json=payload, headers=auth_headers)
    
    assert response.status_code in (400, 422)


def test_create_exam_past_date(client, auth_headers):
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
    
    response = client.post("/exams", json=payload, headers=auth_headers)
    
    assert response.status_code == 422


def test_create_exam_end_before_start(client, auth_headers, future_date):
    """Test creating exam where end time is before start time."""
    payload = {
        "title": "End Before Start Exam",
        "exam_code": "SE126",
        "course": "1",
        "date": future_date,
        "start_time": "11:00",
        "end_time": "09:00",  # end before start
        "status": "scheduled"
    }
    
    response = client.post("/exams", json=payload, headers=auth_headers)
    
    assert response.status_code == 422


def test_create_exam_missing_exam_code(client, auth_headers, future_date):
    """Test exam creation fails when exam_code is missing."""
    payload = {
        "title": "Missing Exam Code",
        "course": "1",
        "date": future_date,
        "start_time": "09:00",
        "end_time": "11:00"
    }
    
    response = client.post("/exams", json=payload, headers=auth_headers)
    
    assert response.status_code == 422


def test_create_exam_duplicate_exam_code(client, auth_headers, future_date):
    """Test creating exam with duplicate exam code."""
    payload = {
        "title": "Exam Two",
        "exam_code": "DUPLICATE",
        "course": "1",
        "date": future_date,
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    
    with patch("src.routers.exams.service.add_exam") as mock_add:
        mock_add.side_effect = ValueError("Exam code 'DUPLICATE' already exists")
        
        response = client.post("/exams", json=payload, headers=auth_headers)
        
        assert response.status_code == 400
        assert "duplicate" in response.json().get("detail", "").lower()


def test_create_exam_scheduling_conflict(client, auth_headers, future_date):
    """Test creating exam with scheduling conflict."""
    payload = {
        "title": "Conflicting Exam",
        "exam_code": "CONF001",
        "course": "1",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }
    
    with patch("src.routers.exams.service.add_exam") as mock_add:
        mock_add.side_effect = ValueError("Scheduling conflict detected")
        
        response = client.post("/exams", json=payload, headers=auth_headers)
        
        assert response.status_code == 400
        assert "conflict" in response.json().get("detail", "").lower()


# ============================================================================
# GET EXAM TESTS
# ============================================================================

def test_get_all_exams(client, auth_headers, mock_exam_service):
    """Test retrieving all exams."""
    mock_exam_service.get_teacher_exams.return_value = [
        {
            "id": 1,
            "title": "Exam 1",
            "exam_code": "E1",
            "course": 1,
            "date": "2026-01-14",
            "start_time": "09:00",
            "end_time": "11:00",
            "status": "scheduled",
            "created_by": 1
        },
        {
            "id": 2,
            "title": "Exam 2",
            "exam_code": "E2",
            "course": 2,
            "date": "2026-01-15",
            "start_time": "14:00",
            "end_time": "16:00",
            "status": "scheduled",
            "created_by": 1
        }
    ]
    
    response = client.get("/exams", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["title"] == "Exam 1"


def test_get_all_exams_empty(client, auth_headers, mock_exam_service):
    """Test retrieving exams when none exist."""
    mock_exam_service.get_teacher_exams.return_value = []
    
    response = client.get("/exams", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_exam_by_id_success(client, auth_headers, mock_exam_service):
    """Test retrieving a specific exam by ID."""
    mock_exam_service.get_exam.return_value = {
        "id": 1,
        "title": "Software Engineering Midterm",
        "exam_code": "SE123",
        "course": 1,
        "date": "2026-01-14",
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled",
        "created_by": 1
    }
    
    response = client.get("/exams/1", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Software Engineering Midterm"
    assert data["exam_code"] == "SE123"


def test_get_exam_by_id_not_found(client, auth_headers, mock_exam_service):
    """Test retrieving non-existent exam returns 404."""
    mock_exam_service.get_exam.return_value = None
    
    response = client.get("/exams/99999", headers=auth_headers)
    
    assert response.status_code == 404


def test_get_exam_by_invalid_id(client, auth_headers):
    """Test retrieving exam with invalid ID format."""
    response = client.get("/exams/invalid", headers=auth_headers)
    
    assert response.status_code == 422


# ============================================================================
# UPDATE EXAM TESTS
# ============================================================================

def test_update_exam_success(client, auth_headers, mock_exam_service, future_date):
    """Test updating an exam successfully."""
    payload = {
        "title": "Updated Title",
        "exam_code": "SE123",
        "course": "1",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }
    
    mock_exam_service.get_exam.return_value = {
        "id": 1,
        "created_by": 1,
        **payload
    }
    mock_exam_service.update_exam.return_value = {
        "id": 1,
        "created_by": 1,
        **payload
    }
    
    response = client.put("/exams/1", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


def test_update_exam_not_found(client, auth_headers, mock_exam_service, future_date):
    """Test updating non-existent exam returns 404."""
    payload = {
        "title": "Updated Title",
        "exam_code": "SE123",
        "course": "1",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }
    
    mock_exam_service.get_exam.return_value = None
    
    response = client.put("/exams/99999", json=payload, headers=auth_headers)
    
    assert response.status_code == 404


# ============================================================================
# DELETE EXAM TESTS
# ============================================================================

def test_delete_exam_success(client, auth_headers, mock_exam_service):
    """Test deleting an exam successfully."""
    # ✅ IMPORTANT: Mock get_exam first (for ownership check)
    mock_exam_service.get_exam.return_value = {
        "id": 1,
        "title": "Test Exam",
        "created_by": 1  # Same as auth user
    }
    # Then mock the actual delete
    mock_exam_service.delete_exam.return_value = {"id": 1}
    
    response = client.delete("/exams/1", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Exam deleted successfully"


def test_delete_exam_not_found(client, auth_headers, mock_exam_service):
    """Test deleting non-existent exam returns 404."""
    # ✅ Mock get_exam to return None (exam doesn't exist)
    mock_exam_service.get_exam.return_value = None
    
    response = client.delete("/exams/99999", headers=auth_headers)
    
    assert response.status_code == 404
    assert "Exam not found" in response.json()["detail"]


def test_delete_exam_wrong_owner(client, auth_headers, mock_exam_service):
    """Test deleting exam owned by another user returns 403."""
    # ✅ Mock get_exam to return exam owned by different user
    mock_exam_service.get_exam.return_value = {
        "id": 1,
        "title": "Test Exam",
        "created_by": 2  # Different from auth user (user_id=1)
    }
    
    response = client.delete("/exams/1", headers=auth_headers)
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_delete_exam_service_error(client, auth_headers, mock_exam_service):
    """Test delete when service raises ValueError."""
    # ✅ Mock get_exam for ownership check
    mock_exam_service.get_exam.return_value = {
        "id": 1,
        "title": "Test Exam",
        "created_by": 1
    }
    # Mock delete_exam to raise ValueError
    mock_exam_service.delete_exam.side_effect = ValueError("Exam not found")
    
    response = client.delete("/exams/1", headers=auth_headers)
    
    assert response.status_code == 404
    assert "Exam not found" in response.json()["detail"]


# ============================================================================
# PYDANTIC VALIDATION TESTS
# ============================================================================

def test_validate_time_format_empty_string(future_date):
    """Test time validation - empty string"""
    from src.routers.exams import ExamCreate
    
    with pytest.raises(ValueError, match="Time is required"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=future_date,
            start_time="",
            end_time="10:00",
            status="scheduled"
        )


def test_validate_time_format_invalid_format(future_date):
    """Test time validation - invalid format"""
    from src.routers.exams import ExamCreate
    
    with pytest.raises(ValueError, match="Time must be in HH:MM format"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=future_date,
            start_time="25:99",
            end_time="10:00",
            status="scheduled"
        )


def test_validate_date_invalid():
    """Test date validation - invalid format"""
    from src.routers.exams import ExamCreate
    
    with pytest.raises(ValueError, match="Date must be in"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date="invalid-date",
            start_time="10:00",
            end_time="12:00",
            status="scheduled"
        )


def test_validate_date_in_past():
    """Test date validation - past date"""
    from src.routers.exams import ExamCreate
    
    past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    with pytest.raises(ValueError, match="Exam date cannot be in the past"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=past_date,
            start_time="10:00",
            end_time="12:00",
            status="scheduled"
        )


def test_validate_date_invalid_year(future_date):
    """Test date validation - invalid year"""
    from src.routers.exams import ExamCreate
    
    future_year = date.today().year + 5
    invalid_date = f"{future_year}-06-15"
    
    with pytest.raises(ValueError, match="Exam year must be"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=invalid_date,
            start_time="10:00",
            end_time="12:00",
            status="scheduled"
        )


def test_model_validator_end_before_start(future_date):
    """Test end time must be after start time"""
    from src.routers.exams import ExamCreate
    
    with pytest.raises(ValueError, match="End time must be after start time"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=future_date,
            start_time="12:00",
            end_time="10:00",
            status="scheduled"
        )


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

def test_convert_time_to_string_none_dict():
    """Test convert_time_to_string with None"""
    from src.routers.exams import convert_time_to_string
    
    result = convert_time_to_string(None)
    assert result is None


def test_convert_time_to_string_with_time_objects(future_date):
    """Test convert_time_to_string with time objects"""
    from src.routers.exams import convert_time_to_string
    from datetime import time
    
    exam_dict = {
        "id": 1,
        "start_time": time(10, 30),
        "end_time": time(12, 0)
    }
    
    result = convert_time_to_string(exam_dict)
    
    assert result["start_time"] == "10:30"
    assert result["end_time"] == "12:00"


def test_convert_time_already_string(future_date):
    """Test convert_time when already string"""
    from src.routers.exams import convert_time_to_string
    
    exam_dict = {
        "id": 1,
        "start_time": "10:30",
        "end_time": "12:00"
    }
    
    result = convert_time_to_string(exam_dict)
    
    assert result["start_time"] == "10:30"
    assert result["end_time"] == "12:00"


def test_convert_time_mixed_types():
    """Test convert_time with mixed types"""
    from src.routers.exams import convert_time_to_string
    from datetime import time
    
    exam_dict = {
        "id": 1,
        "start_time": time(10, 30),
        "end_time": "12:00"
    }
    
    result = convert_time_to_string(exam_dict)
    
    assert result["start_time"] == "10:30"
    assert result["end_time"] == "12:00"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_get_all_exams_exception(client, auth_headers, mock_exam_service):
    """Test exception handling in get_all_exams"""
    mock_exam_service.get_teacher_exams.side_effect = Exception("Database connection error")
    
    response = client.get("/exams", headers=auth_headers)
    
    assert response.status_code == 500


def test_get_student_exams_value_error(client, mock_exam_service):
    """Test ValueError handling in get_student_exams"""
    mock_exam_service.get_student_exams.side_effect = ValueError("Invalid student ID")
    
    response = client.get("/exams/student/999")
    
    assert response.status_code == 400
    assert "Invalid student ID" in response.json()["detail"]


def test_get_available_exams_exception(client, mock_exam_service):
    """Test exception handling in get_available_exams"""
    mock_exam_service.get_available_exams_for_student.side_effect = Exception("Query failed")
    
    response = client.get("/exams/available?student_id=1")
    
    assert response.status_code == 500


def test_get_upcoming_exams_empty(client, mock_exam_service):
    """Test get_upcoming_exams returns empty list"""
    mock_exam_service.get_upcoming_exams_for_student.return_value = None
    
    response = client.get("/exams/upcoming?student_id=1")
    
    assert response.status_code == 200
    assert response.json() == []


def test_add_exam_value_error(client, auth_headers, mock_exam_service, future_date):
    """Test ValueError handling in add_exam"""
    mock_exam_service.add_exam.side_effect = ValueError("Duplicate exam code")
    
    response = client.post("/exams", json={
        "title": "Test",
        "exam_code": "DUP",
        "course": "CS",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }, headers=auth_headers)
    
    assert response.status_code == 400
    assert "Duplicate exam code" in response.json()["detail"]


def test_update_exam_value_error(client, auth_headers, mock_exam_service, future_date):
    """Test ValueError handling in update_exam"""
    mock_exam_service.get_exam.return_value = {"id": 1, "created_by": 1}
    mock_exam_service.update_exam.side_effect = ValueError("Invalid exam data")
    
    response = client.put("/exams/1", json={
        "title": "Test",
        "exam_code": "TEST",
        "course": "CS",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }, headers=auth_headers)
    
    assert response.status_code == 400
    assert "Invalid exam data" in response.json()["detail"]


# ============================================================================
# SUCCESSFUL OPERATIONS
# ============================================================================

def test_get_all_exams_success(client, auth_headers, mock_exam_service, sample_exam):
    """Test successful get all exams"""
    mock_exam_service.get_teacher_exams.return_value = [sample_exam]
    
    response = client.get("/exams", headers=auth_headers)
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Math Final"


def test_get_student_exams_success(client, mock_exam_service, sample_exam):
    """Test successful get student exams"""
    mock_exam_service.get_student_exams.return_value = [sample_exam]
    
    response = client.get("/exams/student/1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_available_exams_success(client, mock_exam_service, sample_exam):
    """Test successful get available exams"""
    mock_exam_service.get_available_exams_for_student.return_value = [sample_exam]
    
    response = client.get("/exams/available?student_id=1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_upcoming_exams_success(client, mock_exam_service, sample_exam):
    """Test successful get upcoming exams"""
    mock_exam_service.get_upcoming_exams_for_student.return_value = [sample_exam]
    
    response = client.get("/exams/upcoming?student_id=1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_add_exam_success(client, auth_headers, mock_exam_service, sample_exam, future_date):
    """Test successful add exam"""
    mock_exam_service.add_exam.return_value = sample_exam
    
    response = client.post("/exams", json={
        "title": "Math Final",
        "exam_code": "MATH101",
        "course": "1",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }, headers=auth_headers)
    
    assert response.status_code == 201
    assert response.json()["title"] == "Math Final"


def test_update_exam_success(client, auth_headers, mock_exam_service, sample_exam, future_date):
    """Test successful update exam"""
    updated_exam = sample_exam.copy()
    updated_exam["title"] = "Updated Title"
    
    mock_exam_service.get_exam.return_value = sample_exam
    mock_exam_service.update_exam.return_value = updated_exam
    
    response = client.put("/exams/1", json={
        "title": "Updated Title",
        "exam_code": "MATH101",
        "course": "1",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


# def test_delete_exam_success(client, auth_headers, mock_exam_service):
#     """Test successful delete exam"""
#     mock_exam_service.delete_exam.return_value = {"id": 1}
    
#     response = client.delete("/exams/1", headers=auth_headers)
    
#     assert response.status_code == 200
#     assert response.json()["message"] == "Exam deleted successfully"


# def test_delete_exam_not_found(client, auth_headers, mock_exam_service):
#     """Test delete exam not found"""
#     mock_exam_service.delete_exam.side_effect = ValueError("Exam not found")
    
#     response = client.delete("/exams/999", headers=auth_headers)
    
#     assert response.status_code == 404
#     assert "Exam not found" in response.json()["detail"]


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_create_exam_requires_authentication(client, future_date):
    """Test that creating exam requires authentication"""
    payload = {
        "title": "Test Exam",
        "exam_code": "TEST01",
        "course": "1",
        "date": future_date,
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    
    response = client.post("/exams", json=payload)
    
    assert response.status_code == 401
    assert "authenticated" in response.json().get("detail", "").lower()


def test_get_exam_requires_authentication(client):
    """Test that getting exam requires authentication"""
    response = client.get("/exams/1")
    
    assert response.status_code == 401


def test_update_exam_requires_authentication(client, future_date):
    """Test that updating exam requires authentication"""
    payload = {
        "title": "Test Exam",
        "exam_code": "TEST01",
        "course": "1",
        "date": future_date,
        "start_time": "09:00",
        "end_time": "11:00",
        "status": "scheduled"
    }
    
    response = client.put("/exams/1", json=payload)
    
    assert response.status_code == 401


def test_delete_exam_requires_authentication(client):
    """Test that deleting exam requires authentication"""
    response = client.delete("/exams/1")
    
    assert response.status_code == 401


def test_get_exam_wrong_owner(client, auth_headers, mock_exam_service):
    """Test that user can only access their own exams"""
    mock_exam_service.get_exam.return_value = {
        "id": 1,
        "title": "Test",
        "exam_code": "TEST",
        "created_by": 2  # Different owner
    }
    
    response = client.get("/exams/1", headers=auth_headers)
    
    assert response.status_code == 403
    assert "permission" in response.json().get("detail", "").lower()