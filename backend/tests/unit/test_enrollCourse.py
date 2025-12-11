"""
Unit Tests for Course Enrollment Service
Tests CourseService enrollment methods
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.course_service import CourseService


@pytest.fixture
def course_service():
    """Create CourseService instance"""
    return CourseService()


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch('src.services.course_service.get_conn') as mock_conn:
        yield mock_conn


class TestGetStudentCourses:
    """Unit tests for get_student_courses method"""
    
    def test_get_student_courses_success(self, course_service, mock_db_connection):
        """Test getting courses for an enrolled student"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "course_name": "Mathematics",
                "course_code": "MATH101",
                "description": "Basic math",
                "status": "active",
                "number_student": 30,
                "instructor": "teacher@example.com",
                "enrollment_id": 1
            }
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.get_student_courses(student_id=1)
        
        # Assert
        assert len(result) == 1
        assert result[0]["course_name"] == "Mathematics"
        assert result[0]["course_code"] == "MATH101"
        assert result[0]["status"] == "active"
        assert "enrollment_id" in result[0]
        
        # Verify SQL was executed
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "studentCourse" in sql
        assert "student_id = %s" in sql
    
    def test_get_student_courses_no_enrollments(self, course_service, mock_db_connection):
        """Test getting courses for student with no enrollments"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.get_student_courses(student_id=999)
        
        # Assert
        assert result == []
    
    def test_get_student_courses_only_active(self, course_service, mock_db_connection):
        """Test that only active courses are returned"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "course_name": "Active Course",
                "course_code": "ACT101",
                "description": "Active",
                "status": "active",
                "number_student": 10,
                "instructor": "teacher@example.com",
                "enrollment_id": 1
            }
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.get_student_courses(student_id=1)
        
        # Assert
        assert len(result) == 1
        assert result[0]["status"] == "active"
        
        # Verify SQL includes status filter
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "c.status = 'active'" in sql


class TestGetAvailableCoursesForStudent:
    """Unit tests for get_available_courses_for_student method"""
    
    def test_get_available_courses_success(self, course_service, mock_db_connection):
        """Test getting available courses for student"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 2,
                "course_name": "Physics",
                "course_code": "PHYS101",
                "description": "Basic physics",
                "status": "active",
                "number_student": 25,
                "instructor": "prof.physics@example.com"
            }
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.get_available_courses_for_student(student_id=1)
        
        # Assert
        assert len(result) == 1
        assert result[0]["course_name"] == "Physics"
        assert result[0]["course_code"] == "PHYS101"
        assert result[0]["status"] == "active"
        
        # Verify SQL was executed
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "NOT IN" in sql  # Should exclude already enrolled courses
        assert "c.status = 'active'" in sql
    
    def test_get_available_courses_all_enrolled(self, course_service, mock_db_connection):
        """Test getting available courses when student is enrolled in all"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.get_available_courses_for_student(student_id=1)
        
        # Assert
        assert result == []


class TestEnrollStudent:
    """Unit tests for enroll_student method"""
    
    def test_enroll_student_success(self, course_service, mock_db_connection):
        """Test successful student enrollment"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock for check_student_sql, check_course_sql, check_enrollment_sql, insert_sql
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "user_email": "student1@example.com"},  # Student exists
            {"id": 101, "course_name": "Math", "status": "active"},  # Course exists and active
            None,  # Not already enrolled
            {"id": 1001, "student_id": 1, "course_id": 101}  # Enrollment created
        ]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.__enter__.return_value = mock_conn
        
        # Act
        result = course_service.enroll_student(student_id=1, course_id=101)
        
        # Assert
        assert result["id"] == 1001
        assert result["student_id"] == 1
        assert result["course_id"] == 101
        assert result["course_name"] == "Math"
        assert result["student_email"] == "student1@example.com"
        
        # Verify commit was called on connection
        mock_conn.commit.assert_called_once()
    
    def test_enroll_student_already_enrolled(self, course_service, mock_db_connection):
        """Test enrolling student who is already enrolled"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "user_email": "student1@example.com"},  # Student exists
            {"id": 101, "course_name": "Math", "status": "active"},  # Course exists
            {"id": 1001}  # Already enrolled
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="already enrolled"):
            course_service.enroll_student(student_id=1, course_id=101)
    
    def test_enroll_student_not_student(self, course_service, mock_db_connection):
        """Test enrolling a non-student user"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Student not found
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="not a student"):
            course_service.enroll_student(student_id=999, course_id=101)
    
    def test_enroll_student_course_not_found(self, course_service, mock_db_connection):
        """Test enrolling in non-existent course"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "user_email": "student1@example.com"},  # Student exists
            None  # Course not found
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="Course not found"):
            course_service.enroll_student(student_id=1, course_id=999)
    
    def test_enroll_student_inactive_course(self, course_service, mock_db_connection):
        """Test enrolling in inactive course"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "user_email": "student1@example.com"},  # Student exists
            {"id": 101, "course_name": "Math", "status": "inactive"}  # Course inactive
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="inactive course"):
            course_service.enroll_student(student_id=1, course_id=101)


class TestUnenrollStudent:
    """Unit tests for unenroll_student method"""
    
    def test_unenroll_student_success(self, course_service, mock_db_connection):
        """Test successful student unenrollment"""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1001}  # Enrollment found and deleted
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.__enter__.return_value = mock_conn
        
        # Act
        result = course_service.unenroll_student(student_id=1, course_id=101)
        
        # Assert
        assert result is True
        
        # Verify SQL was executed
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "DELETE FROM" in sql
        assert "studentCourse" in sql
        assert "RETURNING" in sql
        
        # Verify commit was called on connection
        mock_conn.commit.assert_called_once()
    
    def test_unenroll_student_not_enrolled(self, course_service, mock_db_connection):
        """Test unenrolling student who is not enrolled"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No enrollment found
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.unenroll_student(student_id=999, course_id=999)
        
        # Assert
        assert result is False


class TestIsStudentEnrolled:
    """Unit tests for is_student_enrolled method"""
    
    def test_is_student_enrolled_true(self, course_service, mock_db_connection):
        """Test checking enrolled student"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1001}  # Enrollment exists
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.is_student_enrolled(student_id=1, course_id=101)
        
        # Assert
        assert result is True
    
    def test_is_student_enrolled_false(self, course_service, mock_db_connection):
        """Test checking non-enrolled student"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No enrollment
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.is_student_enrolled(student_id=999, course_id=999)
        
        # Assert
        assert result is False


class TestEnrollmentEdgeCases:
    """Test edge cases for enrollment functionality"""
    
    def test_enroll_student_database_error(self, course_service, mock_db_connection):
        """Test enrollment when database error occurs"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database"):
            course_service.enroll_student(student_id=1, course_id=101)


class TestEnrollmentDataValidation:
    """Test data validation in enrollment methods"""
    
    def test_invalid_student_id(self, course_service, mock_db_connection):
        """Test with invalid student ID"""
        # Arrange
        mock_cursor = MagicMock()
        # Database will likely raise an error or return no results for invalid ID
        mock_cursor.fetchall.return_value = []
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.get_student_courses(student_id=-1)
        
        # Assert - should return empty list, not raise exception
        assert result == []
    
    def test_invalid_course_id(self, course_service, mock_db_connection):
        """Test with invalid course ID"""
        # Arrange
        mock_cursor = MagicMock()
        # Database will likely return no results for invalid ID
        mock_cursor.fetchall.return_value = []
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = course_service.get_available_courses_for_student(student_id=-1)
        
        # Assert - should return empty list, not raise exception
        assert result == []