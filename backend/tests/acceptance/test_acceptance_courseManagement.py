# conftest.py - Shared fixtures and mock data
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    return mock_conn, mock_cursor

@pytest.fixture
def sample_course():
    """Sample course data"""
    return {
        'id': 1,
        'course_name': 'Introduction to Python',
        'course_code': 'CS101',
        'description': 'Learn Python basics',
        'status': 'active',
        'number_student': 25,
        'instructor': 'teacher@example.com'
    }

@pytest.fixture
def sample_courses():
    """Multiple sample courses"""
    return [
        {
            'id': 1,
            'course_name': 'Introduction to Python',
            'course_code': 'CS101',
            'description': 'Learn Python basics',
            'status': 'active',
            'number_student': 25,
            'instructor': 'teacher1@example.com'
        },
        {
            'id': 2,
            'course_name': 'Advanced JavaScript',
            'course_code': 'CS202',
            'description': 'Advanced JS concepts',
            'status': 'active',
            'number_student': 15,
            'instructor': 'teacher2@example.com'
        },
        {
            'id': 3,
            'course_name': 'Database Design',
            'course_code': 'CS303',
            'description': 'Database fundamentals',
            'status': 'inactive',
            'number_student': 0,
            'instructor': 'No instructor assigned'
        }
    ]


# ============================================================================
# STORY 1: CREATE COURSE
# ============================================================================

# test_create_course_unit.py
"""Unit Tests for Create Course"""

from src.services.course_service import CourseService
import pytest
from unittest.mock import patch, MagicMock

class TestCreateCourseUnit:
    """Unit tests for create course functionality"""
    
    @patch('src.services.course_service.get_conn')
    def test_create_course_success_positive(self, mock_get_conn, mock_db_connection, sample_course):
        """Positive: Successfully create a new course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        # Mock: course code doesn't exist
        mock_cursor.fetchone.side_effect = [
            None,  # No existing course
            sample_course  # Newly created course
        ]
        
        service = CourseService()
        new_course_data = {
            'course_name': 'Introduction to Python',
            'course_code': 'CS101',
            'description': 'Learn Python basics',
            'status': 'active'
        }
        
        result = service.create_course(new_course_data)
        
        assert result['course_code'] == 'CS101'
        assert result['course_name'] == 'Introduction to Python'
        assert result['status'] == 'active'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_create_course_duplicate_code_negative(self, mock_get_conn, mock_db_connection):
        """Negative: Fail to create course with duplicate course code"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        # Mock: course code already exists
        mock_cursor.fetchone.return_value = {'id': 1}
        
        service = CourseService()
        duplicate_course = {
            'course_name': 'Another Course',
            'course_code': 'CS101',
            'description': 'Test',
            'status': 'active'
        }
        
        with pytest.raises(ValueError, match="Course code 'CS101' already exists"):
            service.create_course(duplicate_course)
        
        mock_conn.commit.assert_not_called()
    
    @patch('src.services.course_service.get_conn')
    def test_create_course_default_status_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Create course with default status when not provided"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.side_effect = [
            None,
            {'id': 1, 'course_name': 'Test', 'course_code': 'TEST', 'description': None, 'status': 'active'}
        ]
        
        service = CourseService()
        course_data = {
            'course_name': 'Test Course',
            'course_code': 'TEST'
        }
        
        result = service.create_course(course_data)
        
        assert result['status'] == 'active'


# test_create_course_acceptance.py
"""Acceptance Tests for Create Course"""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

class TestCreateCourseAcceptance:
    """Acceptance tests for create course API"""
    
    @patch('src.services.course_service.get_conn')
    def test_api_create_course_success_positive(self, mock_get_conn, mock_db_connection, sample_course):
        """Positive: API successfully creates a course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [None, sample_course]
        
        response = client.post("/courses", json={
            "course_name": "Introduction to Python",
            "course_code": "CS101",
            "description": "Learn Python basics",
            "status": "active"
        })
        
    @patch('src.services.course_service.get_conn')
    def test_api_get_course_by_id_positive(self, mock_get_conn, mock_db_connection, sample_course):
        """Positive: API returns specific course by ID"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = sample_course
        
        response = client.get("/courses/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
        assert data['course_code'] == 'CS101'
    
    @patch('src.services.course_service.get_conn')
    def test_api_get_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API returns 404 for non-existent course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = None
        
        response = client.get("/courses/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# test_search_course_feature.py
"""Feature Tests for Search Course Story"""

import pytest
from unittest.mock import patch

class TestSearchCourseFeature:
    """
    Feature: Search Course
    As a user
    I want to search and view course information
    So that I can find specific courses or browse all available courses
    """
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_view_all_courses(self, mock_get_conn, mock_db_connection, sample_courses):
        """
        Scenario: View all courses in the system
        Given multiple courses exist in the system
        When I request to view all courses
        Then I should see a list of all courses
        And each course should include basic information
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchall.return_value = sample_courses
        
        service = CourseService()
        result = service.get_all_courses()
        
        assert len(result) == 3
        assert all('course_name' in course for course in result)
        assert all('course_code' in course for course in result)
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_view_course_details(self, mock_get_conn, mock_db_connection, sample_course):
        """
        Scenario: View detailed information for a specific course
        Given a course exists with id 1
        When I request details for course id 1
        Then I should see complete course information
        And the information should include student count
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = sample_course
        
        service = CourseService()
        result = service.get_course_by_id(1)
        
        assert result is not None
        assert result['id'] == 1
        assert 'number_student' in result


# ============================================================================
# STORY 5: FILTER COURSE
# ============================================================================

# test_filter_course_unit.py
"""Unit Tests for Filter Course"""

from src.services.course_service import CourseService
import pytest
from unittest.mock import patch

class TestFilterCourseUnit:
    """Unit tests for filter course functionality"""
    
    @patch('src.services.course_service.get_conn')
    def test_filter_active_courses_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: Successfully filter active courses"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        active_courses = [c for c in sample_courses if c['status'] == 'active']
        mock_cursor.fetchall.return_value = active_courses
        
        service = CourseService()
        result = service.get_all_courses(status='active')
        
        assert len(result) == 2
        assert all(course['status'] == 'active' for course in result)
    
    @patch('src.services.course_service.get_conn')
    def test_filter_inactive_courses_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: Successfully filter inactive courses"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        inactive_courses = [c for c in sample_courses if c['status'] == 'inactive']
        mock_cursor.fetchall.return_value = inactive_courses
        
        service = CourseService()
        result = service.get_all_courses(status='inactive')
        
        assert len(result) == 1
        assert all(course['status'] == 'inactive' for course in result)
    
    @patch('src.services.course_service.get_conn')
    def test_filter_no_status_returns_all_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: No filter returns all courses"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchall.return_value = sample_courses
        
        service = CourseService()
        result = service.get_all_courses()
        
        assert len(result) == 3
    
    @patch('src.services.course_service.get_conn')
    def test_filter_no_matching_courses_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Filter returns empty list when no matches"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchall.return_value = []
        
        service = CourseService()
        result = service.get_all_courses(status='inactive')
        
        assert result == []


# test_filter_course_acceptance.py
"""Acceptance Tests for Filter Course"""

from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

class TestFilterCourseAcceptance:
    """Acceptance tests for filter course API"""
    
    @patch('src.services.course_service.get_conn')
    def test_api_filter_active_courses_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: API filters active courses successfully"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        active_courses = [c for c in sample_courses if c['status'] == 'active']
        mock_cursor.fetchall.return_value = active_courses
        
        response = client.get("/courses?status=active")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(course['status'] == 'active' for course in data)
    
    @patch('src.services.course_service.get_conn')
    def test_api_filter_inactive_courses_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: API filters inactive courses successfully"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        inactive_courses = [c for c in sample_courses if c['status'] == 'inactive']
        mock_cursor.fetchall.return_value = inactive_courses
        
        response = client.get("/courses?status=inactive")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert all(course['status'] == 'inactive' for course in data)
    
    @patch('src.services.course_service.get_conn')
    def test_api_no_filter_returns_all_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: API returns all courses without filter"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchall.return_value = sample_courses
        
        response = client.get("/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


# test_filter_course_feature.py
"""Feature Tests for Filter Course Story"""

import pytest
from unittest.mock import patch

class TestFilterCourseFeature:
    """
    Feature: Filter Courses by Status
    As a user
    I want to filter courses by their status
    So that I can view only active or inactive courses
    """
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_filter_active_courses(self, mock_get_conn, mock_db_connection, sample_courses):
        """
        Scenario: Filter to view only active courses
        Given multiple courses exist with different statuses
        When I filter by status "active"
        Then I should only see active courses
        And inactive courses should not be displayed
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        active_courses = [c for c in sample_courses if c['status'] == 'active']
        mock_cursor.fetchall.return_value = active_courses
        
        service = CourseService()
        result = service.get_all_courses(status='active')
        
        assert len(result) == 2
        assert all(course['status'] == 'active' for course in result)
        assert not any(course['status'] == 'inactive' for course in result)
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_filter_inactive_courses(self, mock_get_conn, mock_db_connection, sample_courses):
        """
        Scenario: Filter to view only inactive courses
        Given multiple courses exist with different statuses
        When I filter by status "inactive"
        Then I should only see inactive courses
        And active courses should not be displayed
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        inactive_courses = [c for c in sample_courses if c['status'] == 'inactive']
        mock_cursor.fetchall.return_value = inactive_courses
        
        service = CourseService()
        result = service.get_all_courses(status='inactive')
        
        assert len(result) == 1
        assert all(course['status'] == 'inactive' for course in result)
        assert not any(course['status'] == 'active' for course in result)


# ============================================================================
# STORY 6: ACTIVATE/DEACTIVATE COURSE
# ============================================================================

# test_status_course_unit.py
"""Unit Tests for Activate/Deactivate Course"""

from src.services.course_service import CourseService
import pytest
from unittest.mock import patch

class TestCourseStatusUnit:
    """Unit tests for course status change functionality"""
    
    @patch('src.services.course_service.get_conn')
    def test_activate_course_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Successfully activate a course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        activated_course = {
            'id': 1,
            'course_name': 'Test Course',
            'course_code': 'CS101',
            'description': 'Test',
            'status': 'active'
        }
        mock_cursor.fetchone.return_value = activated_course
        
        service = CourseService()
        result = service.update_course_status(1, 'active')
        
        assert result['status'] == 'active'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_deactivate_course_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Successfully deactivate a course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        deactivated_course = {
            'id': 1,
            'course_name': 'Test Course',
            'course_code': 'CS101',
            'description': 'Test',
            'status': 'inactive'
        }
        mock_cursor.fetchone.return_value = deactivated_course
        
        service = CourseService()
        result = service.update_course_status(1, 'inactive')
        
        assert result['status'] == 'inactive'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_change_status_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: Fail to change status of non-existent course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = None
        
        service = CourseService()
        result = service.update_course_status(999, 'active')
        
        assert result is None
        mock_conn.commit.assert_not_called()
    
    @patch('src.services.course_service.get_conn')
    def test_toggle_status_multiple_times_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Toggle course status multiple times"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        # First deactivate
        deactivated = {'id': 1, 'course_name': 'Test', 'course_code': 'CS101', 
                      'description': 'Test', 'status': 'inactive'}
        mock_cursor.fetchone.return_value = deactivated
        
        service = CourseService()
        result1 = service.update_course_status(1, 'inactive')
        assert result1['status'] == 'inactive'
        
        # Then reactivate
        activated = {'id': 1, 'course_name': 'Test', 'course_code': 'CS101',
                    'description': 'Test', 'status': 'active'}
        mock_cursor.fetchone.return_value = activated
        
        result2 = service.update_course_status(1, 'active')
        assert result2['status'] == 'active'


# test_status_course_acceptance.py
"""Acceptance Tests for Activate/Deactivate Course"""

from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

class TestCourseStatusAcceptance:
    """Acceptance tests for course status change API"""
    
    @patch('src.services.course_service.get_conn')
    def test_api_activate_course_positive(self, mock_get_conn, mock_db_connection):
        """Positive: API successfully activates a course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        activated_course = {
            'id': 1,
            'course_name': 'Test Course',
            'course_code': 'CS101',
            'description': 'Test',
            'status': 'active'
        }
        mock_cursor.fetchone.return_value = activated_course
        
        response = client.patch("/courses/1/status", json={"status": "active"})
        
        assert response.status_code == 200
        assert "activated" in response.json()["message"]
        assert response.json()["course"]["status"] == "active"
    
    @patch('src.services.course_service.get_conn')
    def test_api_deactivate_course_positive(self, mock_get_conn, mock_db_connection):
        """Positive: API successfully deactivates a course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        deactivated_course = {
            'id': 1,
            'course_name': 'Test Course',
            'course_code': 'CS101',
            'description': 'Test',
            'status': 'inactive'
        }
        mock_cursor.fetchone.return_value = deactivated_course
        
        response = client.patch("/courses/1/status", json={"status": "inactive"})
        
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"]
        assert response.json()["course"]["status"] == "inactive"
    
    @patch('src.services.course_service.get_conn')
    def test_api_invalid_status_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API rejects invalid status value"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.patch("/courses/1/status", json={"status": "invalid"})
        
        assert response.status_code == 400
        assert "active" in response.json()["detail"]
        assert "inactive" in response.json()["detail"]
    
    @patch('src.services.course_service.get_conn')
    def test_api_change_status_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API returns 404 for non-existent course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = None
        
        response = client.patch("/courses/999/status", json={"status": "active"})
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# test_status_course_feature.py
"""Feature Tests for Activate/Deactivate Course Story"""

import pytest
from unittest.mock import patch

class TestCourseStatusFeature:
    """
    Feature: Activate and Deactivate Courses
    As an admin
    I want to activate or deactivate courses
    So that I can control which courses are available for enrollment
    """
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_deactivate_course_for_maintenance(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Deactivate a course for maintenance
        Given an active course exists
        When I change the course status to "inactive"
        Then the course should be marked as inactive
        And students should not be able to enroll in it
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        deactivated_course = {
            'id': 1,
            'course_name': 'Python Course',
            'course_code': 'CS101',
            'description': 'Test',
            'status': 'inactive'
        }
        mock_cursor.fetchone.return_value = deactivated_course
        
        service = CourseService()
        result = service.update_course_status(1, 'inactive')
        
        assert result['status'] == 'inactive'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_reactivate_course_after_maintenance(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Reactivate a course after maintenance
        Given an inactive course exists
        When I change the course status to "active"
        Then the course should be marked as active
        And students should be able to enroll in it again
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        activated_course = {
            'id': 1,
            'course_name': 'Python Course',
            'course_code': 'CS101',
            'description': 'Test',
            'status': 'active'
        }
        mock_cursor.fetchone.return_value = activated_course
        
        service = CourseService()
        result = service.update_course_status(1, 'active')
        
        assert result['status'] == 'active'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_deactivate_before_deletion(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Deactivate course before deletion
        Given an active course needs to be removed
        When I deactivate the course first
        Then the course status should change to inactive
        And the course can then be safely deleted
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        # First deactivate
        deactivated = {
            'id': 1,
            'course_name': 'Old Course',
            'course_code': 'OLD101',
            'description': 'Deprecated',
            'status': 'inactive'
        }
        mock_cursor.fetchone.side_effect = [deactivated, {'status': 'inactive'}]
        
        service = CourseService()
        
        # Deactivate the course
        result = service.update_course_status(1, 'inactive')
        assert result['status'] == 'inactive'
        
        # Now it can be deleted
        delete_result = service.delete_course(1)
        assert delete_result is True
    
    @patch('src.services.course_service.get_conn')
    def test_api_create_course_duplicate_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API rejects duplicate course code"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id': 1}
        
        response = client.post("/courses", json={
            "course_name": "Duplicate Course",
            "course_code": "CS101",
            "description": "Test",
            "status": "active"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @patch('src.services.course_service.get_conn')
    def test_api_create_course_missing_required_fields_negative(self, mock_get_conn):
        """Negative: API rejects request with missing required fields"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post("/courses", json={
            "course_name": "Test Course"
            # Missing course_code
        })
        
        assert response.status_code == 422


# test_create_course_feature.py
"""Feature Tests for Create Course Story"""

import pytest
from unittest.mock import patch

class TestCreateCourseFeature:
    """
    Feature: Create Course
    As an admin
    I want to create a new course
    So that instructors can teach and students can enroll
    """
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_create_course_with_all_fields(self, mock_get_conn, mock_db_connection, sample_course):
        """
        Scenario: Create a course with all required and optional fields
        Given I am an admin user
        When I provide course name, code, description, and status
        Then the course should be created successfully
        And the course should be stored in the database
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [None, sample_course]
        
        service = CourseService()
        result = service.create_course({
            'course_name': 'Introduction to Python',
            'course_code': 'CS101',
            'description': 'Learn Python basics',
            'status': 'active'
        })
        
        assert result is not None
        assert result['course_code'] == 'CS101'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_prevent_duplicate_course_code(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Prevent creating courses with duplicate course codes
        Given a course with code "CS101" already exists
        When I try to create another course with code "CS101"
        Then the system should reject the request
        And show an error message about duplicate course code
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id': 1}
        
        service = CourseService()
        
        with pytest.raises(ValueError) as exc_info:
            service.create_course({
                'course_name': 'Another Course',
                'course_code': 'CS101',
                'description': 'Test'
            })
        
        assert "already exists" in str(exc_info.value)
        mock_conn.commit.assert_not_called()


# ============================================================================
# STORY 2: UPDATE COURSE
# ============================================================================

# test_update_course_unit.py
"""Unit Tests for Update Course"""

from src.services.course_service import CourseService
import pytest
from unittest.mock import patch

class TestUpdateCourseUnit:
    """Unit tests for update course functionality"""
    
    @patch('src.services.course_service.get_conn')
    def test_update_course_name_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Successfully update course name"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        updated_course = {
            'id': 1,
            'course_name': 'Updated Python Course',
            'course_code': 'CS101',
            'description': 'Learn Python basics',
            'status': 'active'
        }
        mock_cursor.fetchone.return_value = updated_course
        
        service = CourseService()
        result = service.update_course(1, {'course_name': 'Updated Python Course'})
        
        assert result['course_name'] == 'Updated Python Course'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_update_course_code_duplicate_negative(self, mock_get_conn, mock_db_connection):
        """Negative: Fail to update course code to existing one"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = {'id': 2}  # Another course exists
        
        service = CourseService()
        
        with pytest.raises(ValueError, match="already exists"):
            service.update_course(1, {'course_code': 'CS202'})
        
        mock_conn.commit.assert_not_called()
    
    @patch('src.services.course_service.get_conn')
    def test_update_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: Update non-existent course returns None"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = None
        
        service = CourseService()
        result = service.update_course(999, {'course_name': 'Test'})
        
        assert result is None
    
    @patch('src.services.course_service.get_conn')
    def test_update_multiple_fields_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Update multiple fields at once"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        updated_course = {
            'id': 1,
            'course_name': 'Advanced Python',
            'course_code': 'CS101',
            'description': 'Advanced concepts',
            'status': 'active'
        }
        mock_cursor.fetchone.return_value = updated_course
        
        service = CourseService()
        result = service.update_course(1, {
            'course_name': 'Advanced Python',
            'description': 'Advanced concepts'
        })
        
        assert result['course_name'] == 'Advanced Python'
        assert result['description'] == 'Advanced concepts'


# test_update_course_acceptance.py
"""Acceptance Tests for Update Course"""

from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

class TestUpdateCourseAcceptance:
    """Acceptance tests for update course API"""
    
    @patch('src.services.course_service.get_conn')
    def test_api_update_course_success_positive(self, mock_get_conn, mock_db_connection):
        """Positive: API successfully updates a course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        updated_course = {
            'id': 1,
            'course_name': 'Updated Course',
            'course_code': 'CS101',
            'description': 'Updated description',
            'status': 'active'
        }
        mock_cursor.fetchone.return_value = updated_course
        
        response = client.put("/courses/1", json={
            "course_name": "Updated Course",
            "description": "Updated description"
        })
        
        assert response.status_code == 200
        assert response.json()["message"] == "Course updated successfully"
        assert response.json()["course"]["course_name"] == "Updated Course"
    
    @patch('src.services.course_service.get_conn')
    def test_api_update_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API returns 404 for non-existent course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = None
        
        response = client.put("/courses/999", json={
            "course_name": "Test"
        })
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('src.services.course_service.get_conn')
    def test_api_update_course_duplicate_code_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API rejects duplicate course code update"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id': 2}
        
        response = client.put("/courses/1", json={
            "course_code": "CS202"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


# test_update_course_feature.py
"""Feature Tests for Update Course Story"""

import pytest
from unittest.mock import patch

class TestUpdateCourseFeature:
    """
    Feature: Update Course
    As an admin
    I want to update course information
    So that course details remain accurate and up-to-date
    """
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_update_course_information(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Update course information successfully
        Given a course exists with id 1
        When I update the course name and description
        Then the course information should be updated
        And the changes should be saved to the database
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        updated_course = {
            'id': 1,
            'course_name': 'Updated Python',
            'course_code': 'CS101',
            'description': 'Updated description',
            'status': 'active'
        }
        mock_cursor.fetchone.return_value = updated_course
        
        service = CourseService()
        result = service.update_course(1, {
            'course_name': 'Updated Python',
            'description': 'Updated description'
        })
        
        assert result['course_name'] == 'Updated Python'
        assert result['description'] == 'Updated description'
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_prevent_duplicate_code_on_update(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Prevent updating to a duplicate course code
        Given courses exist with codes "CS101" and "CS202"
        When I try to update CS101's code to "CS202"
        Then the system should reject the change
        And show an error about duplicate course code
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id': 2}
        
        service = CourseService()
        
        with pytest.raises(ValueError) as exc_info:
            service.update_course(1, {'course_code': 'CS202'})
        
        assert "already exists" in str(exc_info.value)
        mock_conn.commit.assert_not_called()


# ============================================================================
# STORY 3: DELETE COURSE
# ============================================================================

# test_delete_course_unit.py
"""Unit Tests for Delete Course"""

from src.services.course_service import CourseService
import pytest
from unittest.mock import patch

class TestDeleteCourseUnit:
    """Unit tests for delete course functionality"""
    
    @patch('src.services.course_service.get_conn')
    def test_delete_inactive_course_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Successfully delete an inactive course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = {'status': 'inactive'}
        
        service = CourseService()
        result = service.delete_course(1)
        
        assert result is True
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_delete_active_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: Fail to delete an active course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = {'status': 'active'}
        
        service = CourseService()
        
        with pytest.raises(ValueError, match="Only inactive courses can be deleted"):
            service.delete_course(1)
        
        mock_conn.commit.assert_not_called()
    
    @patch('src.services.course_service.get_conn')
    def test_delete_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: Fail to delete non-existent course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = None
        
        service = CourseService()
        result = service.delete_course(999)
        
        assert result is False
        mock_conn.commit.assert_not_called()
    
    @patch('src.services.course_service.get_conn')
    def test_delete_course_cascades_related_data_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Deleting course removes all related data"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = {'status': 'inactive'}
        
        service = CourseService()
        result = service.delete_course(1)
        
        assert result is True
        # Verify multiple DELETE queries were executed
        assert mock_cursor.execute.call_count > 1
        mock_conn.commit.assert_called_once()


# test_delete_course_acceptance.py
"""Acceptance Tests for Delete Course"""

from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

class TestDeleteCourseAcceptance:
    """Acceptance tests for delete course API"""
    
    @patch('src.services.course_service.get_conn')
    def test_api_delete_inactive_course_positive(self, mock_get_conn, mock_db_connection):
        """Positive: API successfully deletes inactive course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'status': 'inactive'}
        
        response = client.delete("/courses/1")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Course deleted successfully"
    
    @patch('src.services.course_service.get_conn')
    def test_api_delete_active_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API rejects deletion of active course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'status': 'active'}
        
        response = client.delete("/courses/1")
        
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"]
    
    @patch('src.services.course_service.get_conn')
    def test_api_delete_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: API returns 404 for non-existent course"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = None
        
        response = client.delete("/courses/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# test_delete_course_feature.py
"""Feature Tests for Delete Course Story"""

import pytest
from unittest.mock import patch

class TestDeleteCourseFeature:
    """
    Feature: Delete Course
    As an admin
    I want to delete inactive courses
    So that obsolete courses are removed from the system
    """
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_delete_inactive_course(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Successfully delete an inactive course
        Given a course exists with status "inactive"
        When I request to delete the course
        Then the course and all related data should be removed
        And a success confirmation should be returned
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'status': 'inactive'}
        
        service = CourseService()
        result = service.delete_course(1)
        
        assert result is True
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.course_service.get_conn')
    def test_scenario_prevent_deleting_active_course(self, mock_get_conn, mock_db_connection):
        """
        Scenario: Prevent deletion of active courses
        Given a course exists with status "active"
        When I try to delete the course
        Then the system should reject the deletion
        And show an error message requiring course deactivation first
        """
        from src.services.course_service import CourseService
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'status': 'active'}
        
        service = CourseService()
        
        with pytest.raises(ValueError) as exc_info:
            service.delete_course(1)
        
        assert "inactive" in str(exc_info.value).lower()
        assert "deactivate" in str(exc_info.value).lower()
        mock_conn.commit.assert_not_called()


# ============================================================================
# STORY 4: SEARCH COURSE
# ============================================================================

# test_search_course_unit.py
"""Unit Tests for Search Course"""

from src.services.course_service import CourseService
import pytest
from unittest.mock import patch

class TestSearchCourseUnit:
    """Unit tests for search course functionality"""
    
    @patch('src.services.course_service.get_conn')
    def test_get_all_courses_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: Successfully retrieve all courses"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchall.return_value = sample_courses
        
        service = CourseService()
        result = service.get_all_courses()
        
        assert len(result) == 3
        assert result[0]['course_code'] == 'CS101'
        assert result[1]['course_code'] == 'CS202'
    
    @patch('src.services.course_service.get_conn')
    def test_get_course_by_id_positive(self, mock_get_conn, mock_db_connection, sample_course):
        """Positive: Successfully retrieve course by ID"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = sample_course
        
        service = CourseService()
        result = service.get_course_by_id(1)
        
        assert result is not None
        assert result['id'] == 1
        assert result['course_code'] == 'CS101'
    
    @patch('src.services.course_service.get_conn')
    def test_get_nonexistent_course_negative(self, mock_get_conn, mock_db_connection):
        """Negative: Return None for non-existent course"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = None
        
        service = CourseService()
        result = service.get_course_by_id(999)
        
        assert result is None
    
    @patch('src.services.course_service.get_conn')
    def test_get_empty_courses_list_positive(self, mock_get_conn, mock_db_connection):
        """Positive: Return empty list when no courses exist"""
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchall.return_value = []
        
        service = CourseService()
        result = service.get_all_courses()
        
        assert result == []
        assert isinstance(result, list)


# test_search_course_acceptance.py
"""Acceptance Tests for Search Course"""

from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

class TestSearchCourseAcceptance:
    """Acceptance tests for search course API"""
    
    @patch('src.services.course_service.get_conn')
    def test_api_get_all_courses_positive(self, mock_get_conn, mock_db_connection, sample_courses):
        """Positive: API returns all courses"""
        from src.routers.course import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        mock_conn, mock_cursor = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchall.return_value = sample_courses
        
        response = client.get("/courses")
        
        assert response.status_code == 200