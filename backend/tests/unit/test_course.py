import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import router and service
from src.routers.course import router
from src.services.course_service import CourseService

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestCourseRoutes:
    """Test cases for course routes"""

    @patch('src.routers.course.CourseService.get_all_courses')
    def test_get_all_courses_success(self, mock_get_all):
        """Test successful retrieval of all courses"""
        mock_courses = [
            {'id': 1, 'course_name': 'Python Programming', 'course_code': 'CS101', 'description': 'Introduction to Python'},
            {'id': 2, 'course_name': 'Data Structures', 'course_code': 'CS102', 'description': 'Learn data structures'}
        ]
        mock_get_all.return_value = mock_courses

        response = client.get("/courses")

        assert response.status_code == 200
        assert response.json() == mock_courses
        mock_get_all.assert_called_once()

    @patch('src.routers.course.CourseService.get_all_courses')
    def test_get_all_courses_empty(self, mock_get_all):
        """Test retrieval when no courses exist"""
        mock_get_all.return_value = []

        response = client.get("/courses")

        assert response.status_code == 200
        assert response.json() == []
        mock_get_all.assert_called_once()

    @patch('src.routers.course.CourseService.get_all_courses')
    def test_get_all_courses_error(self, mock_get_all):
        """Test error handling when service raises exception"""
        mock_get_all.side_effect = Exception("Database connection failed")

        response = client.get("/courses")

        assert response.status_code == 500
        assert "Database connection failed" in response.json()['detail']
        mock_get_all.assert_called_once()


class TestCourseService:
    """Test cases for course service"""

    @patch('src.services.course_service.get_conn')
    def test_get_all_courses_success(self, mock_get_conn):
        mock_courses = [
            {'id': 1, 'course_name': 'Python Programming', 'course_code': 'CS101', 'description': 'Introduction to Python'},
            {'id': 2, 'course_name': 'Data Structures', 'course_code': 'CS102', 'description': 'Learn data structures'}
        ]

        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_courses
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn_instance.__enter__.return_value = mock_conn_instance
        mock_conn_instance.__exit__.return_value = None

        mock_get_conn.return_value = mock_conn_instance

        service = CourseService()
        result = service.get_all_courses()

        assert result == mock_courses
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()

    @patch('src.services.course_service.get_conn')
    def test_get_all_courses_empty_result(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn_instance.__enter__.return_value = mock_conn_instance
        mock_conn_instance.__exit__.return_value = None

        mock_get_conn.return_value = mock_conn_instance

        service = CourseService()
        result = service.get_all_courses()

        assert result == []
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()

    @patch('src.services.course_service.get_conn')
    def test_get_all_courses_db_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Connection failed")

        service = CourseService()
        with pytest.raises(Exception) as exc_info:
            service.get_all_courses()

        assert "Connection failed" in str(exc_info.value)

    @patch('src.routers.course.CourseService.get_all_courses')
    def test_get_all_courses_error(self, mock_get_all):
        mock_get_all.side_effect = Exception("Database connection failed")

        response = client.get("/courses")

        assert response.status_code == 500
        assert "Database connection failed" in response.json()['detail']