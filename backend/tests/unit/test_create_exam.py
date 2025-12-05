import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from datetime import date, datetime, timedelta

client = TestClient(app)


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
        "course": "Mathematics",
        "date": "2026-06-15",
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    }

@pytest.fixture
def future_date():
    """Get a date in the future"""
    return (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")






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
        

def test_validate_time_format_empty_string():
    """Test line 25: Time is required validation"""
    from src.routers.exams import ExamCreate
    
    future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    with pytest.raises(ValueError, match="Time is required"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=future,
            start_time="",  # Empty string
            end_time="10:00",
            status="scheduled"
        )


def test_validate_time_format_invalid_format():
    """Test line 44: Invalid time format validation"""
    from src.routers.exams import ExamCreate
    
    future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    with pytest.raises(ValueError, match="Time must be in HH:MM format"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=future,
            start_time="25:99",  # Invalid time
            end_time="10:00",
            status="scheduled"
        )


def test_validate_date_none_or_invalid():
    """Test line 56: Invalid date format validation"""
    from src.routers.exams import ExamCreate
    
    with pytest.raises(ValueError, match="Date must be in"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date="invalid-date",  # Invalid format
            start_time="10:00",
            end_time="12:00",
            status="scheduled"
        )


def test_validate_date_in_past():
    """Test line 65: Date cannot be in the past"""
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


def test_validate_date_invalid_year():
    """Test lines 79-80: Year validation"""
    from src.routers.exams import ExamCreate
    
    future_year = date.today().year + 5  # Too far in future
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


def test_model_validator_end_before_start():
    """Test line 88: End time must be after start time"""
    from src.routers.exams import ExamCreate
    
    future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    with pytest.raises(ValueError, match="End time must be after start time"):
        ExamCreate(
            title="Test",
            exam_code="TEST",
            course="CS",
            date=future,
            start_time="12:00",
            end_time="10:00",  # Before start
            status="scheduled"
        )



# ============================================================================
# TEST: Convert Time Helper Functions (Lines 103, 110)
# ============================================================================

def test_convert_time_to_string_none_dict():
    """Test line 103: Handle None dict"""
    from src.routers.exams import convert_time_to_string
    
    result = convert_time_to_string(None)
    assert result is None


def test_convert_time_to_string_with_time_objects():
    """Test lines 110: Convert time objects to strings"""
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


# ============================================================================
# TEST: GET /exams - Error Handling (Lines 132-137)
# ============================================================================

def test_get_all_exams_exception_handling(mock_exam_service):
    """Test lines 132-137: Exception handling in get_all_exams"""
    mock_exam_service.get_all_exams.side_effect = Exception("Database connection error")
    
    response = client.get("/exams")
    
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


# ============================================================================
# TEST: GET /exams/student/{student_id} - Error Handling (Lines 163-164)
# ============================================================================

def test_get_student_exams_value_error(mock_exam_service):
    """Test lines 163-164: ValueError handling in get_student_exams"""
    mock_exam_service.get_student_exams.side_effect = ValueError("Invalid student ID")
    
    response = client.get("/exams/student/999")
    
    assert response.status_code == 400
    assert "Invalid student ID" in response.json()["detail"]


# ============================================================================
# TEST: GET /exams/available - Error Handling (Lines 177-178)
# ============================================================================

def test_get_available_exams_exception(mock_exam_service):
    """Test lines 177-178: Exception handling in get_available_exams"""
    mock_exam_service.get_available_exams_for_student.side_effect = Exception("Query failed")
    
    response = client.get("/exams/available?student_id=1")
    
    assert response.status_code == 500
    assert "Query failed" in response.json()["detail"]


# ============================================================================
# TEST: GET /exams/upcoming - No exams scenario (Lines 194-195)
# ============================================================================

def test_get_upcoming_exams_empty_result(mock_exam_service):
    """Test lines 194-195: Return empty list when no upcoming exams"""
    mock_exam_service.get_upcoming_exams_for_student.return_value = None
    
    response = client.get("/exams/upcoming?student_id=1")
    
    assert response.status_code == 200
    assert response.json() == []


# ============================================================================
# TEST: GET /exams/{exam_id} - Error Cases (Lines 200, 202-203)
# ============================================================================

def test_get_exam_not_found(mock_exam_service):
    """Test line 200: Exam not found"""
    mock_exam_service.get_exam.return_value = None
    
    response = client.get("/exams/999")
    
    assert response.status_code == 404
    assert "Exam not found" in response.json()["detail"]


def test_get_exam_exception(mock_exam_service):
    """Test lines 202-203: Exception handling in get_exam"""
    mock_exam_service.get_exam.side_effect = Exception("Database error")
    
    response = client.get("/exams/1")
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]


# ============================================================================
# TEST: GET /exams/exams/{exam_id}/open - All scenarios (Lines 205-217)
# ============================================================================

def test_open_exam_not_found(mock_exam_service):
    """Test line 205-206: Exam not found"""
    mock_exam_service.get_exam_by_id.return_value = None
    
    response = client.get("/exams/exams/999/open")
    
    assert response.status_code == 404
    assert "Exam not found" in response.json()["detail"]


def test_open_exam_not_started_yet(mock_exam_service):
    """Test lines 208-211: Exam not started yet"""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    mock_exam_service.get_exam_by_id.return_value = {
        "id": 1,
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00"
    }
    
    response = client.get("/exams/exams/1/open")
    
    assert response.status_code == 403
    assert "Exam not started yet" in response.json()["detail"]


def test_open_exam_has_ended(mock_exam_service):
    """Test lines 214-215: Exam has ended"""
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    mock_exam_service.get_exam_by_id.return_value = {
        "id": 1,
        "date": past_date,
        "start_time": "10:00",
        "end_time": "12:00"
    }
    
    response = client.get("/exams/exams/1/open")
    
    assert response.status_code == 403
    assert "Exam has ended" in response.json()["detail"]



# ============================================================================
# TEST: POST /exams - Error Handling (Line 254)
# ============================================================================

def test_add_exam_value_error(mock_exam_service):
    """Test line 254: ValueError handling in add_exam"""
    mock_exam_service.add_exam.side_effect = ValueError("Duplicate exam code")
    
    future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = client.post("/exams", json={
        "title": "Test",
        "exam_code": "DUP",
        "course": "CS",
        "date": future,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    })
    
    assert response.status_code == 400
    assert "Duplicate exam code" in response.json()["detail"]


# ============================================================================
# TEST: PUT /exams/{exam_id} - Error Cases (Lines 146-152)
# ============================================================================

def test_update_exam_not_found(mock_exam_service):
    """Test lines 146-152: Exam not found on update"""
    mock_exam_service.update_exam.return_value = None
    
    future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = client.put("/exams/999", json={
        "title": "Updated",
        "exam_code": "UPD",
        "course": "CS",
        "date": future,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    })
    
    assert response.status_code == 404
    assert "Exam not found" in response.json()["detail"]


def test_update_exam_value_error(mock_exam_service):
    """Test line 154: ValueError handling in update_exam"""
    mock_exam_service.update_exam.side_effect = ValueError("Invalid exam data")
    
    future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = client.put("/exams/1", json={
        "title": "Test",
        "exam_code": "TEST",
        "course": "CS",
        "date": future,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    })
    
    assert response.status_code == 400
    assert "Invalid exam data" in response.json()["detail"]


# ============================================================================
# TEST: Successful Operations (Coverage for happy paths)
# ============================================================================

def test_get_all_exams_success(mock_exam_service, sample_exam):
    """Test successful get all exams"""
    mock_exam_service.get_all_exams.return_value = [sample_exam]
    
    response = client.get("/exams")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Math Final"


def test_get_student_exams_success(mock_exam_service, sample_exam):
    """Test successful get student exams"""
    mock_exam_service.get_student_exams.return_value = [sample_exam]
    
    response = client.get("/exams/student/1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_available_exams_success(mock_exam_service, sample_exam):
    """Test successful get available exams"""
    mock_exam_service.get_available_exams_for_student.return_value = [sample_exam]
    
    response = client.get("/exams/available?student_id=1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_upcoming_exams_success(mock_exam_service, sample_exam):
    """Test successful get upcoming exams"""
    mock_exam_service.get_upcoming_exams_for_student.return_value = [sample_exam]
    
    response = client.get("/exams/upcoming?student_id=1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_add_exam_success(mock_exam_service, sample_exam, future_date):
    """Test successful add exam"""
    mock_exam_service.add_exam.return_value = sample_exam
    
    response = client.post("/exams", json={
        "title": "Math Final",
        "exam_code": "MATH101",
        "course": "Mathematics",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    })
    
    assert response.status_code == 201
    assert response.json()["title"] == "Math Final"


def test_update_exam_success(mock_exam_service, sample_exam, future_date):
    """Test successful update exam"""
    updated_exam = sample_exam.copy()
    updated_exam["title"] = "Updated Title"
    mock_exam_service.update_exam.return_value = updated_exam
    
    response = client.put("/exams/1", json={
        "title": "Updated Title",
        "exam_code": "MATH101",
        "course": "Mathematics",
        "date": future_date,
        "start_time": "10:00",
        "end_time": "12:00",
        "status": "scheduled"
    })
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_delete_exam_success(mock_exam_service):
    """Test successful delete exam"""
    mock_exam_service.delete_exam.return_value = None
    
    response = client.delete("/exams/1")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Exam deleted successfully"


def test_delete_exam_not_found(mock_exam_service):
    """Test delete exam not found"""
    mock_exam_service.delete_exam.side_effect = ValueError("Exam not found")
    
    response = client.delete("/exams/999")
    
    assert response.status_code == 404
    assert "Exam not found" in response.json()["detail"]


# ============================================================================
# TEST: Edge Cases for convert_time_to_string
# ============================================================================

def test_convert_time_already_string():
    """Test convert_time when already string"""
    from src.routers.exams import convert_time_to_string
    
    exam_dict = {
        "id": 1,
        "start_time": "10:30",  # Already string
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
        "start_time": time(10, 30),  # time object
        "end_time": "12:00"  # already string
    }
    
    result = convert_time_to_string(exam_dict)
    
    assert result["start_time"] == "10:30"
    assert result["end_time"] == "12:00"
    

# ============================================================================
# SERVICE LAYER TESTS - Validation Functions
# ============================================================================


def test_validate_exam_code_empty():
    """Test validate_exam_code with empty string"""
    from services.exams_service import validate_exam_code
    
    with pytest.raises(ValueError, match="Exam code is required"):
        validate_exam_code("")
    
    with pytest.raises(ValueError, match="Exam code is required"):
        validate_exam_code("   ")


def test_validate_exam_code_too_long():
    """Test validate_exam_code with string over 50 chars"""
    from services.exams_service import validate_exam_code
    
    with pytest.raises(ValueError, match="50 characters or less"):
        validate_exam_code("A" * 51)


def test_validate_exam_code_invalid_characters():
    """Test validate_exam_code with invalid characters"""
    from services.exams_service import validate_exam_code
    
    with pytest.raises(ValueError, match="can only contain"):
        validate_exam_code("MATH@101")
    
    with pytest.raises(ValueError, match="can only contain"):
        validate_exam_code("CS 101")  # Space not allowed
    
    with pytest.raises(ValueError, match="can only contain"):
        validate_exam_code("EXAM#2024")


def test_validate_title_valid():
    """Test validate_title with valid input"""
    from services.exams_service import validate_title
    
    result = validate_title("Final Exam")
    assert result == "Final Exam"
    
    result = validate_title("  Midterm Test  ")  # Should strip
    assert result == "Midterm Test"


def test_validate_title_empty():
    """Test validate_title with empty string"""
    from services.exams_service import validate_title
    
    with pytest.raises(ValueError, match="Title is required"):
        validate_title("")
    
    with pytest.raises(ValueError, match="Title is required"):
        validate_title("   ")


def test_validate_title_too_long():
    """Test validate_title with string over 255 chars"""
    from services.exams_service import validate_title
    
    with pytest.raises(ValueError, match="255 characters or less"):
        validate_title("A" * 256)


def test_validate_date_obj_valid():
    """Test validate_date_obj with valid date"""
    from services.exams_service import validate_date_obj
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    result = validate_date_obj(future_date)
    assert result == future_date


def test_validate_date_obj_past_date():
    """Test validate_date_obj with past date"""
    from services.exams_service import validate_date_obj
    from datetime import date, timedelta
    
    past_date = date.today() - timedelta(days=1)
    
    with pytest.raises(ValueError, match="cannot be in the past"):
        validate_date_obj(past_date)


def test_validate_date_obj_invalid_year():
    """Test validate_date_obj with invalid year"""
    from services.exams_service import validate_date_obj
    from datetime import date
    
    with pytest.raises(ValueError, match="Year must be between 1900 and 2100"):
        validate_date_obj(date(1899, 1, 1))
    
    with pytest.raises(ValueError, match="Year must be between 1900 and 2100"):
        validate_date_obj(date(2101, 1, 1))


def test_calculate_duration_valid():
    """Test calculate_duration with valid times"""
    from services.exams_service import calculate_duration
    
    duration = calculate_duration("09:00", "11:00")
    assert duration == 120
    
    duration = calculate_duration("08:30", "10:45")
    assert duration == 135


def test_calculate_duration_end_before_start():
    """Test calculate_duration when end is before start"""
    from services.exams_service import calculate_duration
    
    with pytest.raises(ValueError, match="End time must be after start time"):
        calculate_duration("11:00", "09:00")


def test_calculate_duration_zero():
    """Test calculate_duration when start equals end"""
    from services.exams_service import calculate_duration
    
    with pytest.raises(ValueError, match="must be greater than 0 minutes"):
        calculate_duration("09:00", "09:00")


def test_time_overlap_overlapping():
    """Test time_overlap with overlapping times"""
    from services.exams_service import time_overlap
    
    # Complete overlap
    assert time_overlap("09:00", "11:00", "09:00", "11:00") == True
    
    # Partial overlap
    assert time_overlap("09:00", "11:00", "10:00", "12:00") == True
    assert time_overlap("10:00", "12:00", "09:00", "11:00") == True
    
    # One inside another
    assert time_overlap("09:00", "12:00", "10:00", "11:00") == True


def test_time_overlap_non_overlapping():
    """Test time_overlap with non-overlapping times"""
    from services.exams_service import time_overlap
    
    # Consecutive times
    assert time_overlap("09:00", "11:00", "11:00", "13:00") == False
    
    # Separated times
    assert time_overlap("09:00", "10:00", "11:00", "12:00") == False


def test_time_overlap_with_time_objects():
    """Test time_overlap with time objects instead of strings"""
    from services.exams_service import time_overlap
    from datetime import time
    
    result = time_overlap(
        time(9, 0), time(11, 0),
        time(10, 0), time(12, 0)
    )
    assert result == True


# ============================================================================
# SERVICE LAYER TESTS - ExamService Methods
# ============================================================================

def test_exam_code_exists_true():
    """Test exam_code_exists when code exists"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.exam_code_exists("MATH101")
        
        assert result is True


def test_exam_code_exists_false():
    """Test exam_code_exists when code doesn't exist"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.exam_code_exists("NONEXISTENT")
        
        assert result is False


def test_exam_code_exists_with_exclude():
    """Test exam_code_exists with exclude_exam_id"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.exam_code_exists("MATH101", exclude_exam_id=5)
        
        # Verify the SQL includes the exclusion
        call_args = mock_cursor.execute.call_args
        assert "id != %s" in call_args[0][0]
        assert 5 in call_args[0][1]


def test_add_exam_success():
    """Test add_exam with valid data"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Test Exam',
            'exam_code': 'TEST01',
            'course': 1,
            'date': future_date,
            'start_time': '09:00',
            'end_time': '11:00',
            'duration': 120,
            'status': 'scheduled'
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        
        # Mock exam_code_exists to return False
        with patch.object(service, 'exam_code_exists', return_value=False):
            # Mock check_exam_conflicts to do nothing
            with patch.object(service, 'check_exam_conflicts'):
                result = service.add_exam(
                    title="Test Exam",
                    exam_code="TEST01",
                    course=1,
                    date=future_date,
                    start_time="09:00",
                    end_time="11:00"
                )
        
        assert result['id'] == 1
        assert result['title'] == 'Test Exam'


def test_add_exam_missing_title():
    """Test add_exam with missing title"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with pytest.raises(ValueError, match="Title is required"):
        service.add_exam(
            title="",
            exam_code="TEST01",
            course=1,
            date=future_date,
            start_time="09:00",
            end_time="11:00"
        )


def test_add_exam_duplicate_code():
    """Test add_exam with duplicate exam code"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with patch.object(service, 'exam_code_exists', return_value=True):
        with pytest.raises(ValueError, match="already exists"):
            service.add_exam(
                title="Test Exam",
                exam_code="DUPLICATE",
                course=1,
                date=future_date,
                start_time="09:00",
                end_time="11:00"
            )


def test_add_exam_invalid_status():
    """Test add_exam with invalid status"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with pytest.raises(ValueError, match="Status must be one of"):
        service.add_exam(
            title="Test Exam",
            exam_code="TEST01",
            course=1,
            date=future_date,
            start_time="09:00",
            end_time="11:00",
            status="invalid_status"
        )


def test_update_exam_success():
    """Test update_exam with valid data"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Updated Exam',
            'exam_code': 'TEST01',
            'course': 1,
            'date': future_date,
            'start_time': '10:00',
            'end_time': '12:00',
            'duration': 120,
            'status': 'scheduled'
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts'):
                result = service.update_exam(
                    exam_id=1,
                    title="Updated Exam",
                    exam_code="TEST01",
                    course=1,
                    date=future_date,
                    start_time="10:00",
                    end_time="12:00"
                )
        
        assert result['title'] == 'Updated Exam'


def test_update_exam_not_found():
    """Test update_exam when exam doesn't exist"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No exam found
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts'):
                with pytest.raises(ValueError, match="not found"):
                    service.update_exam(
                        exam_id=999,
                        title="Updated Exam",
                        exam_code="TEST01",
                        course=1,
                        date=future_date,
                        start_time="10:00",
                        end_time="12:00"
                    )


def test_get_exam_success():
    """Test get_exam with valid ID"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Test Exam',
            'exam_code': 'TEST01'
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_exam(1)
        
        assert result['id'] == 1
        assert result['title'] == 'Test Exam'


def test_get_exam_invalid_id():
    """Test get_exam with invalid ID"""
    from services.exams_service import ExamService
    
    service = ExamService()
    
    with pytest.raises(ValueError, match="positive integer"):
        service.get_exam(0)
    
    with pytest.raises(ValueError, match="positive integer"):
        service.get_exam(-1)


def test_delete_exam_success():
    """Test delete_exam with valid ID"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.delete_exam(1)
        
        assert result['id'] == 1


def test_delete_exam_not_found():
    """Test delete_exam when exam doesn't exist"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        
        with pytest.raises(ValueError, match="not found"):
            service.delete_exam(999)


def test_get_all_exams_success():
    """Test get_all_exams returns list of exams"""
    from services.exams_service import ExamService
    from datetime import time
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'title': 'Exam 1',
                'start_time': time(9, 0),
                'end_time': time(11, 0)
            },
            {
                'id': 2,
                'title': 'Exam 2',
                'start_time': '10:00',  # Already string
                'end_time': '12:00'
            }
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_all_exams()
        
        assert len(result) == 2
        assert result[0]['start_time'] == '09:00'
        assert result[1]['start_time'] == '10:00'


def test_get_all_exams_empty():
    """Test get_all_exams when no exams exist"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_all_exams()
        
        assert result == []


def test_get_all_exams_exception():
    """Test get_all_exams handles exceptions"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_conn.return_value.__enter__.side_effect = Exception("Database error")
        
        service = ExamService()
        result = service.get_all_exams()
        
        # Should return empty list instead of raising
        assert result == []


def test_get_student_exams_success():
    """Test get_student_exams returns student's exams"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'title': 'Math Exam', 'start_time': '09:00', 'end_time': '11:00'}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_student_exams(1)
        
        assert len(result) == 1
        assert result[0]['title'] == 'Math Exam'


def test_get_student_exams_invalid_id():
    """Test get_student_exams with invalid student ID"""
    from services.exams_service import ExamService
    
    service = ExamService()
    
    with pytest.raises(ValueError, match="positive integer"):
        service.get_student_exams(0)


def test_check_exam_conflicts_no_conflict():
    """Test check_exam_conflicts when no conflicts exist"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        # First call for students
        mock_cursor.fetchall.return_value = [{'student_id': 1}]
        # Second call for conflicts
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        # Should not raise exception
        service.check_exam_conflicts(1, future_date, "09:00", "11:00")


def test_check_exam_conflicts_with_conflict():
    """Test check_exam_conflicts when conflict exists"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        
        # Mock for fetchall (students)
        fetchall_mock = MagicMock()
        fetchall_mock.return_value = [{'student_id': 1}]
        
        # Mock for fetchone (conflict check)
        fetchone_mock = MagicMock()
        fetchone_mock.return_value = {
            'id': 2,
            'course': 1,
            'start_time': '10:00',
            'end_time': '12:00',
            'course_code': 'MATH101',
            'course_name': 'Mathematics'
        }
        
        # Setup cursor to use different return values
        cursor_mock = MagicMock()
        cursor_mock.fetchall = fetchall_mock
        cursor_mock.fetchone = fetchone_mock
        
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = cursor_mock
        
        service = ExamService()
        
        with pytest.raises(ValueError, match="Scheduling conflict"):
            service.check_exam_conflicts(1, future_date, "09:00", "11:00")

def test_get_available_exams_for_student_success():
    """Test get_available_exams_for_student returns current exams"""
    from services.exams_service import ExamService
    from datetime import time
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'title': 'Math Exam',
                'exam_code': 'MATH101',
                'course': 1,
                'course_name': 'Mathematics',
                'course_code': 'MATH',
                'date': '2024-12-05',
                'start_time': time(10, 0),
                'end_time': time(12, 0),
                'duration': 120,
                'status': 'scheduled'
            }
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_available_exams_for_student(1)
        
        assert len(result) == 1
        assert result[0]['title'] == 'Math Exam'
        assert result[0]['start_time'] == '10:00'  # Converted to string
        assert result[0]['end_time'] == '12:00'


def test_get_available_exams_for_student_no_results():
    """Test get_available_exams_for_student when no exams available"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_available_exams_for_student(1)
        
        assert result == []


def test_get_available_exams_for_student_exception():
    """Test get_available_exams_for_student handles exceptions - Line 127"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_conn.return_value.__enter__.side_effect = Exception("Database connection failed")
        
        service = ExamService()
        result = service.get_available_exams_for_student(1)
        
        # Should return empty list on exception
        assert result == []


def test_get_available_exams_with_string_times():
    """Test get_available_exams when times are already strings"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'title': 'Test',
                'start_time': '10:00',  # Already string
                'end_time': '12:00'
            }
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_available_exams_for_student(1)
        
        assert result[0]['start_time'] == '10:00'


# ============================================================================
# MISSING COVERAGE: get_upcoming_exams_for_student (Lines 150-202)
# ============================================================================

def test_get_upcoming_exams_for_student_success():
    """Test get_upcoming_exams_for_student returns future exams"""
    from services.exams_service import ExamService
    from datetime import time
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'title': 'Future Exam',
                'exam_code': 'FUT001',
                'course': 1,
                'course_name': 'CS',
                'course_code': 'CS101',
                'date': '2025-01-15',
                'start_time': time(14, 0),
                'end_time': time(16, 0),
                'duration': 120,
                'status': 'scheduled'
            }
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_upcoming_exams_for_student(1)
        
        assert len(result) == 1
        assert result[0]['title'] == 'Future Exam'
        assert result[0]['start_time'] == '14:00'


def test_get_upcoming_exams_for_student_no_results():
    """Test get_upcoming_exams_for_student when no upcoming exams"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_upcoming_exams_for_student(1)
        
        assert result == []


def test_get_upcoming_exams_for_student_exception():
    """Test get_upcoming_exams_for_student handles exceptions - Lines 189-196"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_conn.return_value.__enter__.side_effect = Exception("Query failed")
        
        service = ExamService()
        result = service.get_upcoming_exams_for_student(1)
        
        # Should return empty list on exception
        assert result == []


# ============================================================================
# MISSING COVERAGE: check_exam_conflicts edge cases (Lines 245-246, 254, 257)
# ============================================================================

def test_check_exam_conflicts_no_students():
    """Test check_exam_conflicts when no students enrolled - Lines 245-246"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []  # No students
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        # Should return early without checking conflicts
        result = service.check_exam_conflicts(1, future_date, "09:00", "11:00")
        
        assert result is None


def test_check_exam_conflicts_with_exclude_id():
    """Test check_exam_conflicts with exclude_exam_id - Line 254"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'student_id': 1}]
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        # Should include exclude_exam_id in query
        service.check_exam_conflicts(1, future_date, "09:00", "11:00", exclude_exam_id=5)
        
        # Verify SQL was called with exclude parameter
        calls = mock_cursor.execute.call_args_list
        sql_with_exclude = calls[-1][0][0]
        assert "id != %s" in sql_with_exclude


def test_check_exam_conflicts_general_exception():
    """Test check_exam_conflicts handles general exceptions - Line 257"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = Exception("Database error")
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        # Should catch exception and return (not raise)
        result = service.check_exam_conflicts(1, future_date, "09:00", "11:00")
        
        assert result is None  # Should not raise


# ============================================================================
# MISSING COVERAGE: add_exam edge cases (Lines 284-285, 305, 307-308, 310, 312)
# ============================================================================

def test_add_exam_missing_course():
    """Test add_exam with missing course - Lines 289-290"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with pytest.raises(ValueError, match="Course is required"):
        service.add_exam(
            title="Test",
            exam_code="TEST01",
            course=None,
            date=future_date,
            start_time="09:00",
            end_time="11:00"
        )


def test_add_exam_missing_times():
    """Test add_exam with missing times - Lines 293-294"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with pytest.raises(ValueError, match="Start time and end time are required"):
        service.add_exam(
            title="Test",
            exam_code="TEST01",
            course=1,
            date=future_date,
            start_time="",
            end_time="11:00"
        )


def test_add_exam_missing_date():
    """Test add_exam with missing date - Lines 295-296"""
    from services.exams_service import ExamService
    
    service = ExamService()
    
    with pytest.raises(ValueError, match="Date is required"):
        service.add_exam(
            title="Test",
            exam_code="TEST01",
            course=1,
            date=None,
            start_time="09:00",
            end_time="11:00"
        )



def test_add_exam_conflict_check_exception():
    """Test add_exam when conflict check raises non-ValueError - Lines 310-312"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Test',
            'exam_code': 'TEST01',
            'course': 1,
            'date': future_date,
            'start_time': '09:00',
            'end_time': '11:00',
            'duration': 120,
            'status': 'scheduled'
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts', side_effect=Exception("DB timeout")):
                # Should not raise, should proceed
                result = service.add_exam(
                    title="Test",
                    exam_code="TEST01",
                    course=1,
                    date=future_date,
                    start_time="09:00",
                    end_time="11:00"
                )
        
        assert result['id'] == 1


# ============================================================================
# MISSING COVERAGE: update_exam edge cases (Lines 325, 328, 331, 342, 355-358)
# ============================================================================

def test_update_exam_missing_course():
    """Test update_exam with missing course - Line 328"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with pytest.raises(ValueError, match="Course is required"):
        service.update_exam(
            exam_id=1,
            title="Test",
            exam_code="TEST01",
            course=None,
            date=future_date,
            start_time="09:00",
            end_time="11:00"
        )


def test_update_exam_missing_times():
    """Test update_exam with missing times - Line 331"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with pytest.raises(ValueError, match="Start time and end time are required"):
        service.update_exam(
            exam_id=1,
            title="Test",
            exam_code="TEST01",
            course=1,
            date=future_date,
            start_time=None,
            end_time="11:00"
        )


def test_update_exam_missing_date():
    """Test update_exam with missing date - Line 334"""
    from services.exams_service import ExamService
    
    service = ExamService()
    
    with pytest.raises(ValueError, match="Date is required"):
        service.update_exam(
            exam_id=1,
            title="Test",
            exam_code="TEST01",
            course=1,
            date=None,
            start_time="09:00",
            end_time="11:00"
        )


def test_update_exam_duplicate_code():
    """Test update_exam with duplicate code - Line 342"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    service = ExamService()
    future_date = date.today() + timedelta(days=30)
    
    with patch.object(service, 'exam_code_exists', return_value=True):
        with pytest.raises(ValueError, match="already exists"):
            service.update_exam(
                exam_id=1,
                title="Test",
                exam_code="DUPLICATE",
                course=1,
                date=future_date,
                start_time="09:00",
                end_time="11:00"
            )


def test_update_exam_conflict_check_exception():
    """Test update_exam when conflict check raises exception - Lines 355-358"""
    from services.exams_service import ExamService
    from datetime import date, timedelta
    
    future_date = date.today() + timedelta(days=30)
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Updated',
            'exam_code': 'TEST01',
            'course': 1,
            'date': future_date,
            'start_time': '10:00',
            'end_time': '12:00',
            'duration': 120,
            'status': 'scheduled'
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts', side_effect=Exception("Timeout")):
                # Should proceed despite exception
                result = service.update_exam(
                    exam_id=1,
                    title="Updated",
                    exam_code="TEST01",
                    course=1,
                    date=future_date,
                    start_time="10:00",
                    end_time="12:00"
                )
        
        assert result['title'] == 'Updated'


# ============================================================================
# MISSING COVERAGE: get_exam edge cases (Lines 400, 407, 410, 413, 416, 420, 424)
# ============================================================================

def test_get_exam_none_id():
    """Test get_exam with None ID - Line 400"""
    from services.exams_service import ExamService
    
    service = ExamService()
    
    with pytest.raises(ValueError, match="positive integer"):
        service.get_exam(None)


def test_get_exam_returns_none():
    """Test get_exam when exam not found returns None"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_exam(999)
        
        assert result is None


# ============================================================================
# MISSING COVERAGE: get_all_exams edge cases (Lines 439-442, 515-516)
# ============================================================================

def test_get_all_exams_with_null_times():
    """Test get_all_exams with None time values - Lines 439-442"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'title': 'Test',
                'start_time': None,  # None time
                'end_time': None
            }
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_all_exams()
        
        # Should not crash, times remain None
        assert result[0]['start_time'] is None



# ============================================================================
# MISSING COVERAGE: get_student_exams edge cases (Lines 580, 582, 586-591)
# ============================================================================

def test_get_student_exams_with_time_conversion():
    """Test get_student_exams converts time objects - Lines 580-591"""
    from services.exams_service import ExamService
    from datetime import time
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'title': 'Test',
                'start_time': time(14, 30),
                'end_time': time(16, 0)
            }
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_student_exams(1)
        
        assert result[0]['start_time'] == '14:30'
        assert result[0]['end_time'] == '16:00'


def test_get_student_exams_none_result():
    """Test get_student_exams when no results - Line 582"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        service = ExamService()
        result = service.get_student_exams(1)
        
        assert result == []


def test_get_student_exams_exception():
    """Test get_student_exams handles exceptions - Lines 586-591"""
    from services.exams_service import ExamService
    
    with patch('services.exams_service.get_conn') as mock_conn:
        mock_conn.return_value.__enter__.side_effect = Exception("Database error")
        
        service = ExamService()
        result = service.get_student_exams(1)
        
        # Should return empty list
        assert result == []


# ============================================================================
# MISSING COVERAGE: delete_exam edge case (Line 596)
# ============================================================================

def test_delete_exam_invalid_id():
    """Test delete_exam with invalid ID - Line 596"""
    from services.exams_service import ExamService
    
    service = ExamService()
    
    with pytest.raises(ValueError, match="positive integer"):
        service.delete_exam(0)
    
    with pytest.raises(ValueError, match="positive integer"):
        service.delete_exam(-5)
