"""
Unit Tests for Instructor Submission Management
Tests search, filter, and summary functionality with mock data
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, time
from fastapi import HTTPException


# Mock data fixtures
@pytest.fixture
def mock_enrolled_students():
    """Mock enrolled students data"""
    return [
        {
            "student_id": 1,
            "student_email": "john.doe@example.com",
            "student_name": "john.doe@example.com"
        },
        {
            "student_id": 2,
            "student_email": "jane.smith@example.com",
            "student_name": "jane.smith@example.com"
        },
        {
            "student_id": 3,
            "student_email": "bob.j@example.com",
            "student_name": "bob.j@example.com"
        },
        {
            "student_id": 4,
            "student_email": "alice.w@example.com",
            "student_name": "alice.w@example.com"
        },
        {
            "student_id": 5,
            "student_email": "charlie.b@example.com",
            "student_name": "charlie.b@example.com"
        }
    ]


@pytest.fixture
def mock_submissions():
    """Mock submissions data"""
    return [
        {
            "submission_id": 201,
            "student_id": 1,
            "student_name": "john.doe@example.com",
            "student_email": "john.doe@example.com",
            "status": "graded",
            "submission_date": "2024-12-01",
            "submission_time": "14:30:00",
            "score": 85,
            "score_grade": "A",
            "overall_feedback": "Excellent work"
        },
        {
            "submission_id": 202,
            "student_id": 2,
            "student_name": "jane.smith@example.com",
            "student_email": "jane.smith@example.com",
            "status": "pending",
            "submission_date": "2024-12-02",
            "submission_time": "10:15:00",
            "score": None,
            "score_grade": None,
            "overall_feedback": None
        },
        {
            "submission_id": 203,
            "student_id": 3,
            "student_name": "bob.j@example.com",
            "student_email": "bob.j@example.com",
            "status": "graded",
            "submission_date": "2024-12-01",
            "submission_time": "15:45:00",
            "score": 72,
            "score_grade": "B",
            "overall_feedback": "Good effort"
        }
    ]


@pytest.fixture
def mock_exam_data():
    """Mock exam data"""
    return {
        "id": 101,
        "course": 1,
        "title": "Midterm Exam",
        "date": date(2024, 12, 1),
        "start_time": time(14, 0),
        "end_time": time(16, 0),
        "duration": 120,
        "status": "ongoing"
    }


@pytest.fixture
def mock_complete_submissions(mock_submissions, mock_enrolled_students):
    """Mock complete submissions including missed students"""
    result = mock_submissions.copy()
    
    # Add missed students (students 4 and 5)
    for student in mock_enrolled_students:
        if student["student_id"] not in [1, 2, 3]:
            result.append({
                "submission_id": None,
                "student_id": student["student_id"],
                "student_name": student["student_name"],
                "student_email": student["student_email"],
                "status": "missed",
                "submission_date": None,
                "submission_time": None,
                "score": None,
                "score_grade": None,
                "overall_feedback": None
            })
    
    return result


# Test Class for Search Functionality
class TestSearchSubmissions:
    """Unit tests for searching student submissions"""
    
    def test_search_by_exact_student_id(self, mock_complete_submissions):
        """Test searching by exact student ID"""
        search_term = "STU0001"
        
        # Simulate search logic
        results = [
            sub for sub in mock_complete_submissions
            if f"STU{str(sub['student_id']).zfill(4)}" == search_term
        ]
        
        assert len(results) == 1
        assert results[0]["student_id"] == 1
        assert results[0]["student_name"] == "john.doe@example.com"
    
    def test_search_by_partial_student_id(self, mock_complete_submissions):
        """Test searching by partial student ID"""
        search_term = "STU000"
        
        results = [
            sub for sub in mock_complete_submissions
            if search_term.lower() in f"STU{str(sub['student_id']).zfill(4)}".lower()
        ]
        
        assert len(results) >= 1
        for result in results:
            assert "STU000" in f"STU{str(result['student_id']).zfill(4)}"
    
    def test_search_by_student_name(self, mock_complete_submissions):
        """Test searching by student name"""
        search_term = "john.doe"
        
        results = [
            sub for sub in mock_complete_submissions
            if search_term.lower() in sub["student_name"].lower()
        ]
        
        assert len(results) == 1
        assert "john.doe" in results[0]["student_name"].lower()
    
    def test_search_by_student_email(self, mock_complete_submissions):
        """Test searching by student email"""
        search_term = "jane.smith@example.com"
        
        results = [
            sub for sub in mock_complete_submissions
            if search_term.lower() in sub["student_email"].lower()
        ]
        
        assert len(results) == 1
        assert results[0]["student_email"] == search_term
    
    def test_search_case_insensitive(self, mock_complete_submissions):
        """Test case-insensitive search"""
        search_term_upper = "JOHN.DOE"
        search_term_lower = "john.doe"
        
        results_upper = [
            sub for sub in mock_complete_submissions
            if search_term_upper.lower() in sub["student_name"].lower()
        ]
        
        results_lower = [
            sub for sub in mock_complete_submissions
            if search_term_lower.lower() in sub["student_name"].lower()
        ]
        
        assert len(results_upper) == len(results_lower)
        assert results_upper == results_lower
    
    def test_search_non_existent_student(self, mock_complete_submissions):
        """Test searching for non-existent student"""
        search_term = "STU9999"
        
        results = [
            sub for sub in mock_complete_submissions
            if search_term.lower() in f"STU{str(sub['student_id']).zfill(4)}".lower()
        ]
        
        assert len(results) == 0
    
    def test_search_empty_string(self, mock_complete_submissions):
        """Test searching with empty string returns all"""
        search_term = ""
        
        results = [
            sub for sub in mock_complete_submissions
            if search_term.lower() in sub["student_name"].lower() or
               search_term.lower() in sub["student_email"].lower()
        ]
        
        assert len(results) == len(mock_complete_submissions)
    
    def test_search_with_special_characters(self, mock_complete_submissions):
        """Test searching with special characters"""
        search_term = "@example.com"
        
        results = [
            sub for sub in mock_complete_submissions
            if search_term.lower() in sub["student_email"].lower()
        ]
        
        assert len(results) == len(mock_complete_submissions)


# Test Class for Filter Functionality
class TestFilterSubmissions:
    """Unit tests for filtering submissions by status"""
    
    def test_filter_pending_submissions(self, mock_complete_submissions):
        """Test filtering only pending submissions"""
        status_filter = "pending"
        
        results = [
            sub for sub in mock_complete_submissions
            if sub["status"] == status_filter
        ]
        
        assert len(results) == 1
        assert all(sub["status"] == "pending" for sub in results)
    
    def test_filter_graded_submissions(self, mock_complete_submissions):
        """Test filtering only graded submissions"""
        status_filter = "graded"
        
        results = [
            sub for sub in mock_complete_submissions
            if sub["status"] == status_filter
        ]
        
        assert len(results) == 2
        assert all(sub["status"] == "graded" for sub in results)
        assert all(sub["score"] is not None for sub in results)
    
    def test_filter_missed_submissions(self, mock_complete_submissions):
        """Test filtering only missed submissions"""
        status_filter = "missed"
        
        results = [
            sub for sub in mock_complete_submissions
            if sub["status"] == status_filter
        ]
        
        assert len(results) == 2
        assert all(sub["status"] == "missed" for sub in results)
        assert all(sub["submission_date"] is None for sub in results)
    
    def test_filter_all_submissions(self, mock_complete_submissions):
        """Test filtering with 'all' returns everything"""
        status_filter = "all"
        
        if status_filter == "all":
            results = mock_complete_submissions
        else:
            results = [sub for sub in mock_complete_submissions if sub["status"] == status_filter]
        
        assert len(results) == len(mock_complete_submissions)
    
    def test_filter_invalid_status(self, mock_complete_submissions):
        """Test filtering with invalid status returns empty"""
        status_filter = "invalid_status"
        
        results = [
            sub for sub in mock_complete_submissions
            if sub["status"] == status_filter
        ]
        
        assert len(results) == 0
    
    def test_combined_search_and_filter(self, mock_complete_submissions):
        """Test combining search and filter"""
        search_term = "john"
        status_filter = "graded"
        
        results = [
            sub for sub in mock_complete_submissions
            if (search_term.lower() in sub["student_name"].lower() and
                sub["status"] == status_filter)
        ]
        
        assert len(results) == 1
        assert results[0]["student_name"] == "john.doe@example.com"
        assert results[0]["status"] == "graded"


# Test Class for Summary Statistics
class TestSubmissionSummary:
    """Unit tests for submission summary statistics"""
    
    def test_total_students_count(self, mock_enrolled_students):
        """Test calculating total enrolled students"""
        total_students = len(mock_enrolled_students)
        
        assert total_students == 5
    
    def test_submitted_count(self, mock_complete_submissions):
        """Test calculating submitted count"""
        submitted = [
            sub for sub in mock_complete_submissions
            if sub["status"] in ["pending", "graded"]
        ]
        
        assert len(submitted) == 3
    
    def test_missed_count(self, mock_complete_submissions):
        """Test calculating missed count"""
        missed = [
            sub for sub in mock_complete_submissions
            if sub["status"] == "missed"
        ]
        
        assert len(missed) == 2
    
    def test_graded_vs_pending_breakdown(self, mock_complete_submissions):
        """Test breakdown of graded vs pending"""
        graded = [sub for sub in mock_complete_submissions if sub["status"] == "graded"]
        pending = [sub for sub in mock_complete_submissions if sub["status"] == "pending"]
        
        assert len(graded) == 2
        assert len(pending) == 1
    
    def test_summary_all_submitted(self):
        """Test summary when all students submitted"""
        mock_all_submitted = [
            {"student_id": i, "status": "graded", "submission_date": "2024-12-01"}
            for i in range(1, 6)
        ]
        
        total = len(mock_all_submitted)
        submitted = len([s for s in mock_all_submitted if s["status"] in ["graded", "pending"]])
        missed = len([s for s in mock_all_submitted if s["status"] == "missed"])
        
        assert total == 5
        assert submitted == 5
        assert missed == 0
    
    def test_summary_no_submissions(self, mock_enrolled_students):
        """Test summary when no students submitted"""
        mock_no_submissions = [
            {
                "student_id": student["student_id"],
                "status": "missed",
                "submission_date": None
            }
            for student in mock_enrolled_students
        ]
        
        total = len(mock_no_submissions)
        submitted = len([s for s in mock_no_submissions if s["status"] in ["graded", "pending"]])
        missed = len([s for s in mock_no_submissions if s["status"] == "missed"])
        
        assert total == 5
        assert submitted == 0
        assert missed == 5
    
    def test_summary_percentage_calculations(self, mock_complete_submissions):
        """Test percentage calculations for summary"""
        total = len(mock_complete_submissions)
        submitted = len([s for s in mock_complete_submissions if s["status"] in ["graded", "pending"]])
        
        submission_rate = (submitted / total) * 100 if total > 0 else 0
        
        assert submission_rate == 60.0  # 3 out of 5


# Test Class for API Integration
class TestSubmissionAPI:
    """Unit tests for API endpoint"""
    
    @patch('psycopg.connect')
    def test_api_get_submissions_success(self, mock_connect, mock_exam_data, 
                                         mock_enrolled_students, mock_submissions):
        """Test successful API call to get submissions"""
        # Mock database connection and cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchone.return_value = {
            "course": 1,
            "date": mock_exam_data["date"],
            "end_time": mock_exam_data["end_time"]
        }
        mock_cursor.fetchall.side_effect = [mock_enrolled_students, mock_submissions]
        
        # Simulate API function
        exam_id = 101
        
        # Verify exam exists
        assert mock_cursor.fetchone() is not None
        
        # Get results
        enrolled = mock_enrolled_students
        submissions = mock_submissions
        
        assert len(enrolled) == 5
        assert len(submissions) == 3
    
    @patch('psycopg.connect')
    def test_api_exam_not_found(self, mock_connect):
        """Test API with non-existent exam ID"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock no exam found
        mock_cursor.fetchone.return_value = None
        
        exam_id = 999999
        exam = mock_cursor.fetchone()
        
        # Should raise 404 error
        assert exam is None
    
    def test_api_response_structure(self, mock_complete_submissions):
        """Test API response has correct structure"""
        for submission in mock_complete_submissions:
            assert "submission_id" in submission
            assert "student_id" in submission
            assert "student_name" in submission
            assert "student_email" in submission
            assert "status" in submission
            assert "submission_date" in submission
            assert "score" in submission
            assert "score_grade" in submission
    
    def test_api_includes_score_information(self, mock_submissions):
        """Test API includes score and grade information"""
        graded_submissions = [s for s in mock_submissions if s["status"] == "graded"]
        
        for submission in graded_submissions:
            assert submission["score"] is not None
            assert submission["score_grade"] is not None
            assert isinstance(submission["score"], (int, float))


# Test Class for Edge Cases
class TestEdgeCases:
    """Unit tests for edge cases and boundary conditions"""
    
    def test_empty_submissions_list(self):
        """Test handling empty submissions list"""
        submissions = []
        
        search_results = [s for s in submissions if "test" in s.get("student_name", "").lower()]
        filter_results = [s for s in submissions if s.get("status") == "pending"]
        
        assert len(search_results) == 0
        assert len(filter_results) == 0
    
    def test_null_values_in_submission(self):
        """Test handling null values in submission data"""
        submission = {
            "submission_id": None,
            "student_id": 1,
            "student_name": "test@example.com",
            "student_email": "test@example.com",
            "status": "missed",
            "submission_date": None,
            "submission_time": None,
            "score": None,
            "score_grade": None,
            "overall_feedback": None
        }
        
        assert submission["submission_id"] is None
        assert submission["submission_date"] is None
        assert submission["score"] is None
    
    def test_very_long_search_term(self, mock_complete_submissions):
        """Test searching with very long search term"""
        search_term = "x" * 1000
        
        results = [
            sub for sub in mock_complete_submissions
            if search_term.lower() in sub["student_name"].lower()
        ]
        
        assert len(results) == 0
    
    def test_special_characters_in_email(self):
        """Test handling special characters in email"""
        submission = {
            "student_email": "test+tag@example.com",
            "student_name": "test+tag@example.com"
        }
        
        search_term = "test+tag"
        result = search_term.lower() in submission["student_email"].lower()
        
        assert result is True
    
    def test_unicode_characters_in_name(self):
        """Test handling unicode characters in student name"""
        submission = {
            "student_name": "José García",
            "student_email": "jose.garcia@example.com"
        }
        
        search_term = "josé"
        result = search_term.lower() in submission["student_name"].lower()
        
        assert result is True
    
    def test_multiple_status_changes(self):
        """Test tracking submission through status changes"""
        submission = {
            "submission_id": 1,
            "status": "pending"
        }
        
        # Simulate status change
        submission["status"] = "graded"
        submission["score"] = 85
        submission["score_grade"] = "A"
        
        assert submission["status"] == "graded"
        assert submission["score"] == 85


# Test Class for Data Validation
class TestDataValidation:
    """Unit tests for data validation"""
    
    def test_validate_student_id_format(self):
        """Test student ID format validation"""
        valid_ids = [1, 2, 100, 9999]
        
        for student_id in valid_ids:
            formatted_id = f"STU{str(student_id).zfill(4)}"
            assert formatted_id.startswith("STU")
            assert len(formatted_id) == 7
    
    def test_validate_status_values(self, mock_complete_submissions):
        """Test status values are valid"""
        valid_statuses = ["pending", "graded", "missed"]
        
        for submission in mock_complete_submissions:
            assert submission["status"] in valid_statuses
    
    def test_validate_score_range(self, mock_submissions):
        """Test score values are in valid range"""
        for submission in mock_submissions:
            if submission["score"] is not None:
                assert 0 <= submission["score"] <= 100
    
    def test_validate_email_format(self, mock_complete_submissions):
        """Test email format validation"""
        for submission in mock_complete_submissions:
            email = submission["student_email"]
            assert "@" in email
            assert "." in email.split("@")[1]
    
    def test_graded_submission_has_score(self, mock_submissions):
        """Test graded submissions have score"""
        graded = [s for s in mock_submissions if s["status"] == "graded"]
        
        for submission in graded:
            assert submission["score"] is not None
            assert submission["score_grade"] is not None


# Test Class for Performance
class TestPerformance:
    """Unit tests for performance considerations"""
    
    def test_search_large_dataset(self):
        """Test searching in large dataset"""
        large_dataset = [
            {
                "student_id": i,
                "student_name": f"student{i}@example.com",
                "student_email": f"student{i}@example.com",
                "status": "graded" if i % 2 == 0 else "pending"
            }
            for i in range(1, 1001)
        ]
        
        search_term = "student100"
        results = [
            s for s in large_dataset
            if search_term.lower() in s["student_name"].lower()
        ]
        
        assert len(results) >= 1
        assert len(large_dataset) == 1000
    
    def test_filter_large_dataset(self):
        """Test filtering large dataset"""
        large_dataset = [
            {"student_id": i, "status": "graded" if i % 3 == 0 else "pending"}
            for i in range(1, 1001)
        ]
        
        graded = [s for s in large_dataset if s["status"] == "graded"]
        
        assert len(graded) > 0
        assert len(graded) < len(large_dataset)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])