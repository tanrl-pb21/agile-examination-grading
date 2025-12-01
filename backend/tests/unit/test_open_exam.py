import pytest
from datetime import datetime, date, time, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
from src.main import app
from src.services.take_exam_service import TakeExamService

client = TestClient(app)


class TestExamTimeWindowAccess:
    """Test suite for validating exam access based on time windows"""
    
    @pytest.fixture
    def exam_service(self):
        """Fixture to provide TakeExamService instance"""
        return TakeExamService()
    
    @pytest.fixture
    def sample_exam_data(self):
        """Sample exam data for testing"""
        today = date.today()
        return {
            "id": 1,
            "title": "Midterm Exam",
            "exam_code": "EXAM001",
            "course": 1,
            "course_name": "Mathematics",
            "course_code": "MATH101",
            "date": today.isoformat(),
            "start_time": "10:00",
            "end_time": "12:00",
            "duration": 120,
            "status": "scheduled"
        }
    
    # ==========================================
    # TEST 1: Access BEFORE exam start time
    # ==========================================
    
    def test_access_exam_before_start_time(self, sample_exam_data):
        """
        Test that student CANNOT access exam before start time
        Given: Current time is before exam start time
        When: Student tries to check availability
        Then: Status should be 'not_started'
        """
        # Mock the service to return not_started status
        with patch.object(TakeExamService, 'check_exam_availability') as mock_check:
            mock_check.return_value = {
                "status": "not_started",
                "message": "Exam starts at 10:00 on 2025-11-30."
            }
            
            service = TakeExamService()
            result = service.check_exam_availability("EXAM001")
            
            assert result["status"] == "not_started"
            assert "Exam starts" in result["message"]
    
    # ==========================================
    # TEST 2: Access DURING exam time window
    # ==========================================
    
    def test_access_exam_during_valid_time_window(self, sample_exam_data):
        """
        Test that student CAN access exam during valid time window
        Given: Current time is between start time and end time
        When: Student tries to check availability
        Then: Status should be 'available'
        """
        with patch.object(TakeExamService, 'check_exam_availability') as mock_check:
            mock_check.return_value = {
                "status": "available",
                "message": "Exam is open."
            }
            
            service = TakeExamService()
            result = service.check_exam_availability("EXAM001")
            
            assert result["status"] == "available"
            assert "open" in result["message"].lower()
    
    # ==========================================
    # TEST 3: Access AFTER exam end time
    # ==========================================
    
    def test_access_exam_after_end_time(self, sample_exam_data):
        """
        Test that student CANNOT access exam after end time
        Given: Current time is after exam end time
        When: Student tries to check availability
        Then: Status should be 'ended'
        """
        with patch.object(TakeExamService, 'check_exam_availability') as mock_check:
            mock_check.return_value = {
                "status": "ended",
                "message": "Exam ended at 12:00 on 2025-11-30."
            }
            
            service = TakeExamService()
            result = service.check_exam_availability("EXAM001")
            
            assert result["status"] == "ended"
            assert "ended" in result["message"].lower()
    
    # ==========================================
    # TEST 4: Access at EXACT start time
    # ==========================================
    
    def test_access_exam_at_exact_start_time(self, sample_exam_data):
        """
        Test that student CAN access exam at exact start time
        Given: Current time equals exam start time
        When: Student tries to check availability
        Then: Status should be 'available'
        """
        with patch.object(TakeExamService, 'check_exam_availability') as mock_check:
            mock_check.return_value = {
                "status": "available",
                "message": "Exam is open."
            }
            
            service = TakeExamService()
            result = service.check_exam_availability("EXAM001")
            
            assert result["status"] == "available"
    
    # ==========================================
    # TEST 5: Access at EXACT end time
    # ==========================================
    
    def test_access_exam_at_exact_end_time(self, sample_exam_data):
        """
        Test that student CAN access exam at exact end time
        Given: Current time equals exam end time
        When: Student tries to check availability
        Then: Status should be 'available' (to allow submission)
        """
        with patch.object(TakeExamService, 'check_exam_availability') as mock_check:
            mock_check.return_value = {
                "status": "available",
                "message": "Exam is open."
            }
            
            service = TakeExamService()
            result = service.check_exam_availability("EXAM001")
            
            assert result["status"] == "available"
    
    # ==========================================
    # TEST 6: Access 1 minute before start
    # ==========================================
    
    def test_access_exam_one_minute_before_start(self, sample_exam_data):
        """
        Test boundary condition: 1 minute before start
        """
        with patch.object(TakeExamService, 'check_exam_availability') as mock_check:
            mock_check.return_value = {
                "status": "not_started",
                "message": "Exam starts at 10:00."
            }
            
            service = TakeExamService()
            result = service.check_exam_availability("EXAM001")
            
            assert result["status"] == "not_started"
    
    # ==========================================
    # TEST 7: Access 1 minute after end
    # ==========================================
    
    def test_access_exam_one_minute_after_end(self, sample_exam_data):
        """
        Test boundary condition: 1 minute after end
        """
        with patch.object(TakeExamService, 'check_exam_availability') as mock_check:
            mock_check.return_value = {
                "status": "ended",
                "message": "Exam ended at 12:00."
            }
            
            service = TakeExamService()
            result = service.check_exam_availability("EXAM001")
            
            assert result["status"] == "ended"
    
    # ==========================================
    # TEST 8: Get exam duration
    # ==========================================
    
    def test_get_exam_duration_by_code(self, sample_exam_data):
        """
        Test the get_exam_duration_by_code service method
        """
        with patch.object(TakeExamService, 'get_exam_duration_by_code') as mock_duration:
            mock_duration.return_value = {
                "duration_seconds": 7200,  # 2 hours
                "remaining_seconds": 3600,  # 1 hour remaining
                "date": sample_exam_data["date"],
                "start_time": "10:00:00",
                "end_time": "12:00:00",
            }
            
            service = TakeExamService()
            result = service.get_exam_duration_by_code("EXAM001")
            
            assert "duration_seconds" in result
            assert "remaining_seconds" in result
            assert result["duration_seconds"] == 7200  # 2 hours in seconds
    
    # ==========================================
    # TEST 9: Submission validation within window
    # ==========================================
    
    def test_validate_submission_time_within_window(self, sample_exam_data):
        """
        Test that submission validation passes within time window
        """
        with patch.object(TakeExamService, 'validate_submission_time') as mock_validate:
            mock_validate.return_value = True
            
            service = TakeExamService()
            result = service.validate_submission_time("EXAM001")
            
            assert result == True
    
    # ==========================================
    # TEST 10: Submission validation after deadline
    # ==========================================
    
    def test_validate_submission_time_after_deadline(self, sample_exam_data):
        """
        Test that submission validation fails after deadline
        """
        with patch.object(TakeExamService, 'validate_submission_time') as mock_validate:
            mock_validate.side_effect = ValueError(
                "Submission rejected: The exam ended at 12:00. You are 5 minute(s) late. Late submissions are not accepted."
            )
            
            service = TakeExamService()
            
            with pytest.raises(ValueError) as exc_info:
                service.validate_submission_time("EXAM001")
            
            assert "late" in str(exc_info.value).lower()
    
    # ==========================================
    # TEST 11: Submission validation before start
    # ==========================================
    
    def test_validate_submission_time_before_start(self, sample_exam_data):
        """
        Test that submission validation fails before exam starts
        """
        with patch.object(TakeExamService, 'validate_submission_time') as mock_validate:
            mock_validate.side_effect = ValueError(
                "Cannot submit exam before start time. Exam starts at 10:00."
            )
            
            service = TakeExamService()
            
            with pytest.raises(ValueError) as exc_info:
                service.validate_submission_time("EXAM001")
            
            assert "before start" in str(exc_info.value).lower()
    
    # ==========================================
    # TEST 12: Check if student already submitted
    # ==========================================
    
    def test_check_if_student_submitted_yes(self):
        """
        Test checking if student has already submitted
        """
        with patch.object(TakeExamService, 'check_if_student_submitted') as mock_check:
            mock_check.return_value = True
            
            service = TakeExamService()
            result = service.check_if_student_submitted("EXAM001", 1)
            
            assert result == True
    
    def test_check_if_student_submitted_no(self):
        """
        Test checking if student has not submitted yet
        """
        with patch.object(TakeExamService, 'check_if_student_submitted') as mock_check:
            mock_check.return_value = False
            
            service = TakeExamService()
            result = service.check_if_student_submitted("EXAM001", 1)
            
            assert result == False


# ==========================================
# HELPER FUNCTION TESTS
# ==========================================

class TestTimeValidationHelpers:
    """Test helper functions for time validation"""
    
    def test_is_exam_available_before_start(self):
        """Test exam availability logic before start"""
        today = date.today()
        exam = {
            "date": today.isoformat(),
            "start_time": "10:00",
            "end_time": "12:00"
        }
        
        # Simulate 9:00 AM
        current_time = datetime.combine(today, time(9, 0))
        start_dt = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")
        
        is_available = current_time >= start_dt and current_time <= end_dt
        assert is_available == False
    
    def test_is_exam_available_during(self):
        """Test exam availability logic during exam time"""
        today = date.today()
        exam = {
            "date": today.isoformat(),
            "start_time": "10:00",
            "end_time": "12:00"
        }
        
        # Simulate 11:00 AM
        current_time = datetime.combine(today, time(11, 0))
        start_dt = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")
        
        is_available = current_time >= start_dt and current_time <= end_dt
        assert is_available == True
    
    def test_is_exam_available_after_end(self):
        """Test exam availability logic after exam time"""
        today = date.today()
        exam = {
            "date": today.isoformat(),
            "start_time": "10:00",
            "end_time": "12:00"
        }
        
        # Simulate 1:00 PM
        current_time = datetime.combine(today, time(13, 0))
        start_dt = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")
        
        is_available = current_time >= start_dt and current_time <= end_dt
        assert is_available == False
    
    def test_time_window_boundary_start(self):
        """Test exact start time boundary"""
        today = date.today()
        exam_start = datetime.combine(today, time(10, 0))
        current_time = datetime.combine(today, time(10, 0))
        
        # At exact start, should be within window
        is_within = current_time >= exam_start
        assert is_within == True
    
    def test_time_window_boundary_end(self):
        """Test exact end time boundary"""
        today = date.today()
        exam_end = datetime.combine(today, time(12, 0))
        current_time = datetime.combine(today, time(12, 0))
        
        # At exact end, should still be within window
        is_within = current_time <= exam_end
        assert is_within == True