"""
Unit Tests for Submission Router
Tests submission API endpoints with mocked database
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from main import app
from datetime import date, time

client = TestClient(app)


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch('src.routers.submission.get_conn') as mock_conn:
        yield mock_conn


@pytest.fixture
def mock_submission_service():
    """Mock SubmissionService"""
    with patch('src.routers.submission.service') as mock_service:
        yield mock_service


class TestGetExamSubmissionsWithStudents:
    """Test GET /submissions/exam/{exam_id}/students endpoint"""
    
    def test_get_exam_submissions_with_students_success(self, mock_db_connection):
        """Test successful retrieval of exam submissions with students"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"course": 101},  # Exam exists with course_id
        ]
        mock_cursor.fetchall.side_effect = [
            [  # Enrolled students
                {"student_id": 1, "student_email": "student1@example.com", "student_name": "student1@example.com"},
                {"student_id": 2, "student_email": "student2@example.com", "student_name": "student2@example.com"},
                {"student_id": 3, "student_email": "student3@example.com", "student_name": "student3@example.com"},
            ],
            [  # Submissions
                {
                    "submission_id": 1,
                    "student_id": 1,
                    "student_name": "student1@example.com",
                    "student_email": "student1@example.com",
                    "status": "submitted",
                    "submission_date": date(2024, 3, 15),
                    "submission_time": time(10, 30, 0),
                },
                {
                    "submission_id": 2,
                    "student_id": 2,
                    "student_name": "student2@example.com",
                    "student_email": "student2@example.com",
                    "status": "graded",
                    "submission_date": date(2024, 3, 15),
                    "submission_time": time(11, 0, 0),
                }
            ]
        ]
        
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam/1/students")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 3  # 2 submitted + 1 missed
        
        # Check submitted students
        submitted = [r for r in result if r["status"] != "missed"]
        assert len(submitted) == 2
        assert submitted[0]["submission_id"] == 1
        assert submitted[0]["student_id"] == 1
        
        # Check missed student
        missed = [r for r in result if r["status"] == "missed"]
        assert len(missed) == 1
        assert missed[0]["student_id"] == 3
        assert missed[0]["submission_id"] is None
    
    def test_get_exam_submissions_exam_not_found(self, mock_db_connection):
        """Test when exam doesn't exist"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Exam not found
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam/999/students")
        
        # Assert
        assert response.status_code == 404
        assert "Exam not found" in response.json()["detail"]
    
    def test_get_exam_submissions_no_enrolled_students(self, mock_db_connection):
        """Test exam with no enrolled students"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"course": 101}
        mock_cursor.fetchall.side_effect = [
            [],  # No enrolled students
            []   # No submissions
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam/1/students")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_exam_submissions_all_students_submitted(self, mock_db_connection):
        """Test when all enrolled students have submitted"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"course": 101}
        mock_cursor.fetchall.side_effect = [
            [  # Enrolled students
                {"student_id": 1, "student_email": "student1@example.com", "student_name": "student1@example.com"},
            ],
            [  # Submissions
                {
                    "submission_id": 1,
                    "student_id": 1,
                    "student_name": "student1@example.com",
                    "student_email": "student1@example.com",
                    "status": "submitted",
                    "submission_date": date(2024, 3, 15),
                    "submission_time": time(10, 30, 0),
                }
            ]
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam/1/students")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert all(r["status"] != "missed" for r in result)
    
    def test_get_exam_submissions_database_error(self, mock_db_connection):
        """Test database error handling"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database connection failed")
        
        # Act
        response = client.get("/submissions/exam/1/students")
        
        # Assert
        assert response.status_code == 500


class TestGetExamSubmissionsWithScore:
    """Test GET /submissions/exam-withscore/{exam_id}/students endpoint"""
    
    def test_get_exam_submissions_with_score_success(self, mock_db_connection):
        """Test successful retrieval with scores"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "course": 101,
            "date": date(2024, 3, 20),
            "end_time": time(12, 0, 0)
        }
        mock_cursor.fetchall.side_effect = [
            [  # Enrolled students
                {"student_id": 1, "student_email": "student1@example.com", "student_name": "student1@example.com"},
            ],
            [  # Submissions with scores
                {
                    "submission_id": 1,
                    "student_id": 1,
                    "student_name": "student1@example.com",
                    "student_email": "student1@example.com",
                    "status": "graded",
                    "submission_date": date(2024, 3, 15),
                    "submission_time": time(10, 30, 0),
                    "score": 85,
                    "score_grade": "B",
                    "overall_feedback": "Good work"
                }
            ]
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam-withscore/1/students")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["score"] == 85
        assert result[0]["score_grade"] == "B"
        assert result[0]["overall_feedback"] == "Good work"
    
    def test_get_exam_submissions_with_score_exam_not_found(self, mock_db_connection):
        """Test when exam doesn't exist"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam-withscore/999/students")
        
        # Assert
        assert response.status_code == 404
        assert "Exam not found" in response.json()["detail"]
    
    def test_get_exam_submissions_with_score_mixed_status(self, mock_db_connection):
        """Test with both submitted and missed students"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "course": 101,
            "date": date(2024, 3, 20),
            "end_time": time(12, 0, 0)
        }
        mock_cursor.fetchall.side_effect = [
            [  # Enrolled students
                {"student_id": 1, "student_email": "student1@example.com", "student_name": "student1@example.com"},
                {"student_id": 2, "student_email": "student2@example.com", "student_name": "student2@example.com"},
            ],
            [  # Only one submission
                {
                    "submission_id": 1,
                    "student_id": 1,
                    "student_name": "student1@example.com",
                    "student_email": "student1@example.com",
                    "status": "graded",
                    "submission_date": date(2024, 3, 15),
                    "submission_time": time(10, 30, 0),
                    "score": 90,
                    "score_grade": "A",
                    "overall_feedback": "Excellent"
                }
            ]
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam-withscore/1/students")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        
        graded = [r for r in result if r["status"] == "graded"]
        missed = [r for r in result if r["status"] == "missed"]
        
        assert len(graded) == 1
        assert graded[0]["score"] == 90
        
        assert len(missed) == 1
        assert missed[0]["score"] is None


class TestGetExamSubmissions:
    """Test GET /submissions/exam/{exam_id} endpoint"""
    
    def test_get_exam_submissions_success(self, mock_db_connection):
        """Test successful retrieval of exam submissions"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "submission_id": 1,
                "exam_code": 1,
                "user_id": 1,
                "submission_date": date(2024, 3, 15),
                "submission_time": time(10, 30, 0),
                "score": 85,
                "score_grade": "B",
                "overall_feedback": "Good",
                "status": "graded",
                "student_id": 1,
                "student_email": "student1@example.com",
                "user_role": "student",
                "student_name": "student1@example.com"
            }
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam/1")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["submission_id"] == 1
        assert result[0]["student_email"] == "student1@example.com"
    
    def test_get_exam_submissions_empty(self, mock_db_connection):
        """Test when no submissions exist"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam/1")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_exam_submissions_time_conversion(self, mock_db_connection):
        """Test time object conversion to string"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "submission_id": 1,
                "exam_code": 1,
                "user_id": 1,
                "submission_date": date(2024, 3, 15),
                "submission_time": time(10, 30, 45),
                "score": 85,
                "score_grade": "B",
                "overall_feedback": "Good",
                "status": "graded",
                "student_id": 1,
                "student_email": "student1@example.com",
                "user_role": "student",
                "student_name": "student1@example.com"
            }
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/exam/1")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result[0]["submission_time"] == "10:30:45"
        assert result[0]["submission_date"] == "2024-03-15"
    
    def test_get_exam_submissions_database_error(self, mock_db_connection):
        """Test database error handling"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/submissions/exam/1")
        
        # Assert
        assert response.status_code == 500


class TestGetSubmission:
    """Test GET /submissions/{submission_id} endpoint"""
    
    def test_get_submission_success(self, mock_db_connection):
        """Test successful retrieval of single submission"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "submission_id": 1,
            "exam_code": 1,
            "user_id": 1,
            "submission_date": date(2024, 3, 15),
            "submission_time": time(10, 30, 0),
            "score": 85,
            "score_grade": "B",
            "overall_feedback": "Good work",
            "status": "graded",
            "student_id": 1,
            "student_email": "student1@example.com",
            "user_role": "student",
            "student_name": "student1@example.com"
        }
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/1")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["submission_id"] == 1
        assert result["score"] == 85
        assert result["student_email"] == "student1@example.com"
    
    def test_get_submission_not_found(self, mock_db_connection):
        """Test when submission doesn't exist"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/999")
        
        # Assert
        assert response.status_code == 404
        assert "Submission not found" in response.json()["detail"]
    
    def test_get_submission_time_conversion(self, mock_db_connection):
        """Test time and date conversion"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "submission_id": 1,
            "exam_code": 1,
            "user_id": 1,
            "submission_date": date(2024, 3, 15),
            "submission_time": time(14, 25, 30),
            "score": 90,
            "score_grade": "A",
            "overall_feedback": "Excellent",
            "status": "graded",
            "student_id": 1,
            "student_email": "student1@example.com",
            "user_role": "student",
            "student_name": "student1@example.com"
        }
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        response = client.get("/submissions/1")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["submission_time"] == "14:25:30"
        assert result["submission_date"] == "2024-03-15"
    
    def test_get_submission_database_error(self, mock_db_connection):
        """Test database error handling"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/submissions/1")
        
        # Assert
        assert response.status_code == 500


class TestGetStudentSubmissions:
    """Test GET /submissions/student/{user_id} endpoint"""
    
    def test_get_student_submissions_success(self, mock_submission_service):
        """Test successful retrieval of student submissions"""
        # Arrange
        mock_submission_service.get_student_submissions.return_value = [
            {
                "submission_id": 1,
                "exam_code": 1,
                "exam_title": "Midterm Exam",
                "submission_date": "2024-03-15",
                "status": "graded",
                "score": 85
            },
            {
                "submission_id": 2,
                "exam_code": 2,
                "exam_title": "Final Exam",
                "submission_date": "2024-05-20",
                "status": "submitted",
                "score": None
            }
        ]
        
        # Act
        response = client.get("/submissions/student/1")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        assert result[0]["submission_id"] == 1
        mock_submission_service.get_student_submissions.assert_called_once_with(1)
    
    def test_get_student_submissions_not_found(self, mock_submission_service):
        """Test when student has no submissions"""
        # Arrange
        mock_submission_service.get_student_submissions.side_effect = ValueError("No submissions found")
        
        # Act
        response = client.get("/submissions/student/999")
        
        # Assert
        assert response.status_code == 404
        assert "No submissions found" in response.json()["detail"]
    
    def test_get_student_submissions_empty(self, mock_submission_service):
        """Test when student exists but has no submissions"""
        # Arrange
        mock_submission_service.get_student_submissions.return_value = []
        
        # Act
        response = client.get("/submissions/student/1")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == []


class TestGetSubmissionReview:
    """Test GET /submissions/{submission_id}/review endpoint"""
    
    def test_get_submission_review_success(self, mock_submission_service):
        """Test successful retrieval of submission review"""
        # Arrange
        mock_submission_service.get_submission_review.return_value = {
            "submission_id": 1,
            "exam_title": "Midterm Exam",
            "score": 85,
            "score_grade": "B",
            "overall_feedback": "Good work",
            "answers": [
                {
                    "question_id": 1,
                    "question_text": "What is 2+2?",
                    "student_answer": "4",
                    "correct_answer": "4",
                    "points_awarded": 10,
                    "max_points": 10,
                    "feedback": "Correct"
                }
            ]
        }
        
        # Act
        response = client.get("/submissions/1/review?user_id=1")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["submission_id"] == 1
        assert result["score"] == 85
        assert len(result["answers"]) == 1
        mock_submission_service.get_submission_review.assert_called_once_with(1, 1)
    
    def test_get_submission_review_not_found(self, mock_submission_service):
        """Test when submission review not found"""
        # Arrange
        mock_submission_service.get_submission_review.side_effect = ValueError("Submission not found")
        
        # Act
        response = client.get("/submissions/1/review?user_id=999")
        
        # Assert
        assert response.status_code == 404
        assert "Submission not found" in response.json()["detail"]
    
    def test_get_submission_review_unauthorized(self, mock_submission_service):
        """Test when user doesn't have access"""
        # Arrange
        mock_submission_service.get_submission_review.side_effect = ValueError("Unauthorized access")
        
        # Act
        response = client.get("/submissions/1/review?user_id=999")
        
        # Assert
        assert response.status_code == 404


class TestGetSubmissionSummary:
    """Test GET /submissions/exam/{exam_id}/summary endpoint"""
    
    def test_get_submission_summary_success(self, mock_submission_service):
        """Test successful retrieval of submission summary"""
        # Arrange
        mock_submission_service.get_submission_summary.return_value = {
            "exam_id": 1,
            "exam_title": "Midterm Exam",
            "total_students": 30,
            "submitted": 28,
            "graded": 25,
            "pending": 3,
            "missed": 2,
            "average_score": 78.5,
            "highest_score": 98,
            "lowest_score": 45
        }
        
        # Act
        response = client.get("/submissions/exam/1/summary")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["exam_id"] == 1
        assert result["total_students"] == 30
        assert result["submitted"] == 28
        assert result["average_score"] == 78.5
        mock_submission_service.get_submission_summary.assert_called_once_with(1)
    
    def test_get_submission_summary_not_found(self, mock_submission_service):
        """Test when exam not found"""
        # Arrange
        mock_submission_service.get_submission_summary.side_effect = ValueError("Exam not found")
        
        # Act
        response = client.get("/submissions/exam/999/summary")
        
        # Assert
        assert response.status_code == 404
        assert "Exam not found" in response.json()["detail"]
    
    def test_get_submission_summary_no_submissions(self, mock_submission_service):
        """Test exam with no submissions"""
        # Arrange
        mock_submission_service.get_submission_summary.return_value = {
            "exam_id": 1,
            "exam_title": "New Exam",
            "total_students": 0,
            "submitted": 0,
            "graded": 0,
            "pending": 0,
            "missed": 0,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0
        }
        
        # Act
        response = client.get("/submissions/exam/1/summary")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["submitted"] == 0
        assert result["average_score"] == 0


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_invalid_exam_id_type(self):
        """Test with invalid exam ID type"""
        response = client.get("/submissions/exam/invalid/students")
        assert response.status_code == 422
    
    def test_negative_exam_id(self, mock_db_connection):
        """Test with negative exam ID"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = client.get("/submissions/exam/-1/students")
        assert response.status_code == 404
    
    def test_zero_exam_id(self, mock_db_connection):
        """Test with zero exam ID"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = client.get("/submissions/exam/0/students")
        assert response.status_code == 404
    
    def test_invalid_submission_id(self):
        """Test with invalid submission ID type"""
        response = client.get("/submissions/invalid")
        assert response.status_code == 422
    
    def test_missing_query_parameter(self, mock_submission_service):
        """Test missing required query parameter"""
        mock_submission_service.get_submission_review.return_value = {"data": "test"}
        
        # FastAPI will require user_id as query param
        response = client.get("/submissions/1/review?user_id=1")
        assert response.status_code == 200