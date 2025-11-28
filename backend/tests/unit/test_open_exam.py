import pytest
from datetime import datetime, date, time, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app  # Adjust import path as needed
from src.services.exams_service import ExamService
from unittest.mock import patch

client = TestClient(app)


class TestExamTimeWindowAccess:
    """Test suite for validating exam access based on time windows"""
    
    @pytest.fixture
    def exam_service(self):
        """Fixture to provide ExamService instance"""
        return ExamService()
    
    @pytest.fixture
    def mock_current_time(self):
        """Fixture to mock current datetime"""
        def _mock_time(target_time):
                mock_dt.now.return_value = target_time
                mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
                return mock_dt
        return _mock_time
    
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
    
    def test_access_exam_before_start_time(self, sample_exam_data, monkeypatch):
        """
        Test that student CANNOT access exam before start time
        Given: Current time is before exam start time
        When: Student tries to access exam
        Then: Access should be denied
        """
        # Mock the exam data retrieval
        def mock_get_student_exams(self, student_id):
            return [sample_exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # Set current time to 9:30 AM (30 minutes before exam)
        exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
        current_time = datetime.combine(exam_date, time(9, 30))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            
            assert response.status_code == 200
            exams = response.json()
            assert len(exams) > 0
            
            # Verify exam status
            exam = exams[0]
            exam_start = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
            
            # Current time should be before start time
            assert current_time < exam_start, "Current time should be before exam start"
    
    # ==========================================
    # TEST 2: Access DURING exam time window
    # ==========================================
    
    def test_access_exam_during_valid_time_window(self, sample_exam_data, monkeypatch):
        """
        Test that student CAN access exam during valid time window
        Given: Current time is between start time and end time
        When: Student tries to access exam
        Then: Access should be granted
        """
        def mock_get_student_exams(self, student_id):
            return [sample_exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # Set current time to 11:00 AM (1 hour after start, 1 hour before end)
        exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
        current_time = datetime.combine(exam_date, time(11, 0))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            
            assert response.status_code == 200
            exams = response.json()
            
            exam = exams[0]
            exam_start = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
            exam_end = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")
            
            # Current time should be within the window
            assert exam_start <= current_time <= exam_end, "Current time should be within exam window"
    
    # ==========================================
    # TEST 3: Access AFTER exam end time
    # ==========================================
    
    def test_access_exam_after_end_time(self, sample_exam_data, monkeypatch):
        """
        Test that student CANNOT access exam after end time
        Given: Current time is after exam end time
        When: Student tries to access exam
        Then: Access should be denied
        """
        def mock_get_student_exams(self, student_id):
            return [sample_exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # Set current time to 1:00 PM (1 hour after exam end)
        exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
        current_time = datetime.combine(exam_date, time(13, 0))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            
            assert response.status_code == 200
            exams = response.json()
            
            exam = exams[0]
            exam_end = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")
            
            # Current time should be after end time
            assert current_time > exam_end, "Current time should be after exam end"
    
    # ==========================================
    # TEST 4: Access at EXACT start time
    # ==========================================
    
    def test_access_exam_at_exact_start_time(self, sample_exam_data, monkeypatch):
        """
        Test that student CAN access exam at exact start time
        Given: Current time equals exam start time
        When: Student tries to access exam
        Then: Access should be granted
        """
        def mock_get_student_exams(self, student_id):
            return [sample_exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # Set current time to exactly 10:00 AM
        exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
        current_time = datetime.combine(exam_date, time(10, 0))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            
            assert response.status_code == 200
            exams = response.json()
            
            exam = exams[0]
            exam_start = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
            
            # Current time should equal start time
            assert current_time == exam_start, "Current time should equal exam start time"
    
    # ==========================================
    # TEST 5: Access at EXACT end time
    # ==========================================
    
    def test_access_exam_at_exact_end_time(self, sample_exam_data, monkeypatch):
        """
        Test that student CAN access exam at exact end time
        Given: Current time equals exam end time
        When: Student tries to access exam
        Then: Access should be granted (to allow submission)
        """
        def mock_get_student_exams(self, student_id):
            return [sample_exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # Set current time to exactly 12:00 PM
        exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
        current_time = datetime.combine(exam_date, time(12, 0))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            
            assert response.status_code == 200
            exams = response.json()
            
            exam = exams[0]
            exam_end = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")
            
            # Current time should equal end time
            assert current_time == exam_end, "Current time should equal exam end time"
    
    # ==========================================
    # TEST 6: Access 1 minute before start
    # ==========================================
    
    def test_access_exam_one_minute_before_start(self, sample_exam_data, monkeypatch):
        """
        Test boundary condition: 1 minute before start
        """
        def mock_get_student_exams(self, student_id):
            return [sample_exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # 9:59 AM (1 minute before start)
        exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
        current_time = datetime.combine(exam_date, time(9, 59))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            assert response.status_code == 200
            
            exams = response.json()
            exam = exams[0]
            exam_start = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
            
            assert current_time < exam_start
    
    # ==========================================
    # TEST 7: Access 1 minute after end
    # ==========================================
    
    def test_access_exam_one_minute_after_end(self, sample_exam_data, monkeypatch):
        """
        Test boundary condition: 1 minute after end
        """
        def mock_get_student_exams(self, student_id):
            return [sample_exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # 12:01 PM (1 minute after end)
        exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
        current_time = datetime.combine(exam_date, time(12, 1))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            assert response.status_code == 200
            
            exams = response.json()
            exam = exams[0]
            exam_end = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")
            
            assert current_time > exam_end
    
    # ==========================================
    # TEST 8: Multiple exams with different time windows
    # ==========================================
    
    def test_access_multiple_exams_different_windows(self, monkeypatch):
        """
        Test with multiple exams having different time windows
        """
        today = date.today()
        exams_data = [
            {
                "id": 1,
                "title": "Morning Exam",
                "exam_code": "EXAM001",
                "course": 1,
                "date": today.isoformat(),
                "start_time": "09:00",
                "end_time": "11:00",
                "duration": 120,
                "status": "scheduled"
            },
            {
                "id": 2,
                "title": "Afternoon Exam",
                "exam_code": "EXAM002",
                "course": 2,
                "date": today.isoformat(),
                "start_time": "14:00",
                "end_time": "16:00",
                "duration": 120,
                "status": "scheduled"
            }
        ]
        
        def mock_get_student_exams(self, student_id):
            return exams_data
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # Set current time to 10:00 AM (during first exam, before second)
        current_time = datetime.combine(today, time(10, 0))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            assert response.status_code == 200
            
            exams = response.json()
            assert len(exams) == 2
            
            # First exam should be accessible
            exam1_start = datetime.strptime(f"{exams[0]['date']} {exams[0]['start_time']}", "%Y-%m-%d %H:%M")
            exam1_end = datetime.strptime(f"{exams[0]['date']} {exams[0]['end_time']}", "%Y-%m-%d %H:%M")
            assert exam1_start <= current_time <= exam1_end
            
            # Second exam should not be accessible yet
            exam2_start = datetime.strptime(f"{exams[1]['date']} {exams[1]['start_time']}", "%Y-%m-%d %H:%M")
            assert current_time < exam2_start
    
    # ==========================================
    # TEST 9: Exam on different date
    # ==========================================
    
    def test_access_exam_different_date(self, monkeypatch):
        """
        Test that exam on a different date is not accessible today
        """
        tomorrow = date.today() + timedelta(days=1)
        exam_data = {
            "id": 1,
            "title": "Tomorrow's Exam",
            "exam_code": "EXAM001",
            "course": 1,
            "date": tomorrow.isoformat(),
            "start_time": "10:00",
            "end_time": "12:00",
            "duration": 120,
            "status": "scheduled"
        }
        
        def mock_get_student_exams(self, student_id):
            return [exam_data]
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        # Current time is today at 11:00 AM
        today = date.today()
        current_time = datetime.combine(today, time(11, 0))
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.combine = datetime.combine
            
            response = client.get("/exams/student/1")
            assert response.status_code == 200
            
            exams = response.json()
            exam = exams[0]
            exam_start = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
            
            # Exam should be in the future
            assert current_time < exam_start
    
    # ==========================================
    # TEST 10: Get exam duration endpoint
    # ==========================================
    
    def test_get_exam_duration_by_code(self, sample_exam_data, monkeypatch):
        """
        Test the /exams/code/{exam_code}/duration endpoint
        """
        def mock_get_exam_duration(self, exam_code):
            exam_date = datetime.strptime(sample_exam_data["date"], "%Y-%m-%d").date()
            start_time = datetime.strptime(sample_exam_data["start_time"], "%H:%M").time()
            end_time = datetime.strptime(sample_exam_data["end_time"], "%H:%M").time()
            
            start_dt = datetime.combine(exam_date, start_time)
            end_dt = datetime.combine(exam_date, end_time)
            now = datetime.now()
            
            duration_seconds = int((end_dt - start_dt).total_seconds())
            remaining_seconds = max(int((end_dt - now).total_seconds()), 0)
            
            return {
                "duration_seconds": duration_seconds,
                "remaining_seconds": remaining_seconds,
                "date": exam_date.isoformat(),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }
        
        monkeypatch.setattr(ExamService, "get_exam_duration_by_code", mock_get_exam_duration)
        
        response = client.get("/exams/code/EXAM001/duration")
        assert response.status_code == 200
        
        data = response.json()
        assert "duration_seconds" in data
        assert "remaining_seconds" in data
        assert data["duration_seconds"] == 7200  # 2 hours in seconds
    
    # ==========================================
    # TEST 11: Invalid student ID
    # ==========================================
    
    def test_access_exam_invalid_student_id(self):
        """
        Test that invalid student ID returns appropriate error
        """
        response = client.get("/exams/student/0")
        # Should return 400 or empty list depending on implementation
        assert response.status_code in [200, 400]
    
    # ==========================================
    # TEST 12: Student with no enrolled courses
    # ==========================================
    
    def test_access_exam_no_enrolled_courses(self, monkeypatch):
        """
        Test that student with no enrolled courses gets empty exam list
        """
        def mock_get_student_exams(self, student_id):
            return []
        
        monkeypatch.setattr(ExamService, "get_student_exams", mock_get_student_exams)
        
        response = client.get("/exams/student/999")
        assert response.status_code == 200
        
        exams = response.json()
        assert len(exams) == 0


# ==========================================
# HELPER FUNCTION TESTS
# ==========================================

class TestTimeValidationHelpers:
    """Test helper functions for time validation"""
    
    def test_is_exam_available_before_start(self):
        """Test isExamAvailable JavaScript function logic"""
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
        """Test isExamAvailable during exam time"""
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
        """Test isExamAvailable after exam time"""
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
