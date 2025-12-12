import pytest
from unittest.mock import patch, MagicMock, call
from datetime import date, time, datetime, timedelta
from services.exams_service import (
    ExamService,
    validate_date_obj,
    validate_exam_code,
    validate_title,
    calculate_duration,
    time_overlap
)


# ============================================================================
# VALIDATION FUNCTION TESTS
# ============================================================================

class TestValidationFunctions:
    """Test standalone validation functions"""
    
    def test_validate_date_obj_valid_date(self):
        """Test valid date passes validation"""
        future_date = date.today() + timedelta(days=30)
        result = validate_date_obj(future_date)
        assert result == future_date
    
    def test_validate_date_obj_year_too_old(self):
        """Test year before 1900 raises ValueError"""
        old_date = date(1899, 1, 1)
        with pytest.raises(ValueError, match="Year must be between 1900 and 2100"):
            validate_date_obj(old_date)
    
    def test_validate_date_obj_year_too_far(self):
        """Test year after 2100 raises ValueError"""
        far_date = date(2101, 1, 1)
        with pytest.raises(ValueError, match="Year must be between 1900 and 2100"):
            validate_date_obj(far_date)
    
    def test_validate_date_obj_past_date(self):
        """Test past date raises ValueError"""
        past_date = date.today() - timedelta(days=1)
        with pytest.raises(ValueError, match="Exam date cannot be in the past"):
            validate_date_obj(past_date)
    
    def test_validate_exam_code_valid(self):
        """Test valid exam code"""
        assert validate_exam_code("EXAM123") == "EXAM123"
        assert validate_exam_code("exam-code_1") == "exam-code_1"
    
    def test_validate_exam_code_empty(self):
        """Test empty exam code raises ValueError"""
        with pytest.raises(ValueError, match="Exam code is required"):
            validate_exam_code("")
        with pytest.raises(ValueError, match="Exam code is required"):
            validate_exam_code("   ")
    
    def test_validate_exam_code_too_long(self):
        """Test exam code over 50 chars raises ValueError"""
        long_code = "A" * 51
        with pytest.raises(ValueError, match="Exam code must be 50 characters or less"):
            validate_exam_code(long_code)
    
    def test_validate_exam_code_invalid_chars(self):
        """Test exam code with invalid characters"""
        with pytest.raises(ValueError, match="can only contain letters, numbers, hyphens, and underscores"):
            validate_exam_code("exam@123")
        with pytest.raises(ValueError, match="can only contain"):
            validate_exam_code("exam code")
    
    def test_validate_title_valid(self):
        """Test valid title"""
        assert validate_title("Math Final Exam") == "Math Final Exam"
    
    def test_validate_title_empty(self):
        """Test empty title raises ValueError"""
        with pytest.raises(ValueError, match="Title is required"):
            validate_title("")
        with pytest.raises(ValueError, match="Title is required"):
            validate_title("   ")
    
    def test_validate_title_too_long(self):
        """Test title over 255 chars raises ValueError"""
        long_title = "A" * 256
        with pytest.raises(ValueError, match="Title must be 255 characters or less"):
            validate_title(long_title)
    
    def test_validate_title_strips_whitespace(self):
        """Test title strips whitespace"""
        assert validate_title("  Math Exam  ") == "Math Exam"
    
    def test_calculate_duration_valid(self):
        """Test valid duration calculation"""
        duration = calculate_duration("09:00", "11:00")
        assert duration == 120
    
    def test_calculate_duration_end_before_start(self):
        """Test end time before start time raises ValueError"""
        with pytest.raises(ValueError, match="End time must be after start time"):
            calculate_duration("11:00", "09:00")
    
    def test_calculate_duration_zero(self):
        """Test zero duration raises ValueError"""
        with pytest.raises(ValueError, match="Exam duration must be greater than 0 minutes"):
            calculate_duration("09:00", "09:00")
    
    def test_time_overlap_with_overlap(self):
        """Test time ranges that overlap"""
        assert time_overlap("09:00", "11:00", "10:00", "12:00") is True
        assert time_overlap("09:00", "12:00", "10:00", "11:00") is True
    
    def test_time_overlap_no_overlap(self):
        """Test time ranges that don't overlap"""
        assert time_overlap("09:00", "10:00", "11:00", "12:00") is False
        assert time_overlap("11:00", "12:00", "09:00", "10:00") is False
    
    def test_time_overlap_adjacent(self):
        """Test adjacent time ranges (no overlap)"""
        assert time_overlap("09:00", "10:00", "10:00", "11:00") is False
    
    def test_time_overlap_with_time_objects(self):
        """Test time overlap with time objects"""
        start1 = time(9, 0)
        end1 = time(11, 0)
        start2 = time(10, 0)
        end2 = time(12, 0)
        assert time_overlap(start1, end1, start2, end2) is True


# ============================================================================
# EXAM SERVICE TESTS
# ============================================================================

class TestExamService:
    """Test ExamService class methods"""
    
    @pytest.fixture
    def service(self):
        """Create ExamService instance"""
        return ExamService()
    
    @pytest.fixture
    def mock_conn(self):
        """Create mock database connection"""
        mock = MagicMock()
        mock.__enter__ = MagicMock(return_value=mock)
        mock.__exit__ = MagicMock(return_value=False)
        return mock
    
    @pytest.fixture
    def mock_cursor(self):
        """Create mock cursor"""
        mock = MagicMock()
        mock.__enter__ = MagicMock(return_value=mock)
        mock.__exit__ = MagicMock(return_value=False)
        return mock
    
    # ========================================================================
    # search_exams_by_title TESTS
    # ========================================================================
    
    def test_search_exams_by_title_empty_term(self, service):
        """Test search with empty term raises ValueError"""
        with pytest.raises(ValueError, match="Search term is required"):
            service.search_exams_by_title("")
        with pytest.raises(ValueError, match="Search term is required"):
            service.search_exams_by_title("   ")
    
    @patch('services.exams_service.get_conn')
    def test_search_exams_by_title_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successful exam search by title"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Math Final",
                "exam_code": "MATH101",
                "course": 1,
                "date": date(2026, 6, 15),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "scheduled"
            }
        ]
        
        results = service.search_exams_by_title("Math")
        
        assert len(results) == 1
        assert results[0]["title"] == "Math Final"
        assert results[0]["start_time"] == "10:00"
        assert results[0]["end_time"] == "12:00"
        mock_cursor.execute.assert_called_once()
    
    @patch('services.exams_service.get_conn')
    def test_search_exams_by_title_no_results(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test search with no results returns empty list"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        results = service.search_exams_by_title("NonExistent")
        
        assert results == []
    
    @patch('services.exams_service.get_conn')
    def test_search_exams_by_title_exception(self, mock_get_conn, service, mock_conn):
        """Test search handles exceptions gracefully"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")
        
        results = service.search_exams_by_title("Math")
        
        assert results == []
    
    # ========================================================================
    # get_available_exams_for_student TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_get_available_exams_for_student_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test getting available exams for student"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Math Exam",
                "exam_code": "MATH101",
                "course": 1,
                "course_name": "Mathematics",
                "course_code": "MATH",
                "date": date.today(),
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "duration": 120,
                "status": "published"
            }
        ]
        
        results = service.get_available_exams_for_student(1)
        
        assert len(results) == 1
        assert results[0]["title"] == "Math Exam"
        assert results[0]["status"] == "published"
    
    @patch('services.exams_service.get_conn')
    def test_get_available_exams_for_student_empty(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test getting available exams returns empty list"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        results = service.get_available_exams_for_student(1)
        
        assert results == []
    
    @patch('services.exams_service.get_conn')
    def test_get_available_exams_for_student_exception(self, mock_get_conn, service, mock_conn):
        """Test exception handling in get_available_exams"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")
        
        results = service.get_available_exams_for_student(1)
        
        assert results == []
    
    # ========================================================================
    # get_upcoming_exams_for_student TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_get_upcoming_exams_for_student_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test getting upcoming exams for student"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=7)
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Future Exam",
                "exam_code": "FUT101",
                "course": 1,
                "course_name": "Future Course",
                "course_code": "FUT",
                "date": future_date,
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "published"
            }
        ]
        
        results = service.get_upcoming_exams_for_student(1)
        
        assert len(results) == 1
        assert results[0]["title"] == "Future Exam"
    
    @patch('services.exams_service.get_conn')
    def test_get_upcoming_exams_for_student_empty(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test no upcoming exams returns empty list"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        results = service.get_upcoming_exams_for_student(1)
        
        assert results == []
    
    # ========================================================================
    # exam_code_exists TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_exam_code_exists_true(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test exam code exists returns True"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"id": 1}
        
        result = service.exam_code_exists("MATH101")
        
        assert result is True
    
    @patch('services.exams_service.get_conn')
    def test_exam_code_exists_false(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test exam code doesn't exist returns False"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        result = service.exam_code_exists("NONEXIST")
        
        assert result is False
    
    @patch('services.exams_service.get_conn')
    def test_exam_code_exists_with_exclusion(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test exam code exists with exclusion"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        result = service.exam_code_exists("MATH101", exclude_exam_id=1)
        
        assert result is False
        # Verify SQL includes exclusion
        call_args = mock_cursor.execute.call_args
        assert "AND id != %s" in call_args[0][0]
    
    # ========================================================================
    # check_exam_conflicts TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_check_exam_conflicts_no_students(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test no conflict when course has no students"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        # Should not raise exception
        service.check_exam_conflicts(1, date.today(), "10:00", "12:00")
    
    @patch('services.exams_service.get_conn')
    def test_check_exam_conflicts_no_conflict(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test no conflict when students have no overlapping exams"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # First call returns students, second returns no conflicts
        mock_cursor.fetchall.side_effect = [
            [{"student_id": 1}],  # Students in course
        ]
        mock_cursor.fetchone.return_value = None  # No conflicts
        
        # Should not raise exception
        service.check_exam_conflicts(1, date.today(), "10:00", "12:00")
    
    @patch('services.exams_service.get_conn')
    def test_check_exam_conflicts_with_conflict(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test raises ValueError when conflict detected"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [{"student_id": 1}]
        mock_cursor.fetchone.return_value = {
            "id": 2,
            "course": 2,
            "start_time": time(9, 0),
            "end_time": time(11, 0),
            "course_code": "CS101",
            "course_name": "Computer Science"
        }
        
        with pytest.raises(ValueError, match="Scheduling conflict"):
            service.check_exam_conflicts(1, date.today(), "10:00", "12:00")
    
    @patch('services.exams_service.get_conn')
    def test_check_exam_conflicts_exception_handling(self, mock_get_conn, service, mock_conn):
        """Test exception handling in check_exam_conflicts"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")
        
        # Should not raise exception, just log warning
        service.check_exam_conflicts(1, date.today(), "10:00", "12:00")
    
    # ========================================================================
    # add_exam TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_add_exam_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully adding an exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=30)
        
        # Mock exam_code_exists to return False
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts'):
                mock_cursor.fetchone.return_value = {
                    "id": 1,
                    "title": "Math Final",
                    "exam_code": "MATH101",
                    "course": 1,
                    "date": future_date,
                    "start_time": time(10, 0),
                    "end_time": time(12, 0),
                    "duration": 120,
                    "status": "scheduled",
                    "created_by": 1
                }
                
                result = service.add_exam(
                    title="Math Final",
                    exam_code="MATH101",
                    course=1,
                    date=future_date,
                    start_time="10:00",
                    end_time="12:00",
                    created_by=1
                )
                
                assert result["id"] == 1
                assert result["title"] == "Math Final"
                assert result["created_by"] == 1
    
    def test_add_exam_missing_title(self, service):
        """Test add_exam with missing title"""
        with pytest.raises(ValueError, match="Title is required"):
            service.add_exam(
                title="",
                exam_code="TEST",
                course=1,
                date=date.today() + timedelta(days=30),
                start_time="10:00",
                end_time="12:00",
                created_by=1
            )
    
    def test_add_exam_missing_exam_code(self, service):
        """Test add_exam with missing exam code"""
        with pytest.raises(ValueError, match="Exam code is required"):
            service.add_exam(
                title="Test",
                exam_code="",
                course=1,
                date=date.today() + timedelta(days=30),
                start_time="10:00",
                end_time="12:00",
                created_by=1
            )
    
    def test_add_exam_missing_course(self, service):
        """Test add_exam with missing course"""
        with pytest.raises(ValueError, match="Course is required"):
            service.add_exam(
                title="Test",
                exam_code="TEST",
                course=None,
                date=date.today() + timedelta(days=30),
                start_time="10:00",
                end_time="12:00",
                created_by=1
            )
    
    def test_add_exam_missing_times(self, service):
        """Test add_exam with missing times"""
        with pytest.raises(ValueError, match="Start time and end time are required"):
            service.add_exam(
                title="Test",
                exam_code="TEST",
                course=1,
                date=date.today() + timedelta(days=30),
                start_time="",
                end_time="12:00",
                created_by=1
            )
    
    def test_add_exam_missing_date(self, service):
        """Test add_exam with missing date"""
        with pytest.raises(ValueError, match="Date is required"):
            service.add_exam(
                title="Test",
                exam_code="TEST",
                course=1,
                date=None,
                start_time="10:00",
                end_time="12:00",
                created_by=1
            )
    
    def test_add_exam_invalid_status(self, service):
        """Test add_exam with invalid status"""
        with pytest.raises(ValueError, match="Status must be one of"):
            service.add_exam(
                title="Test",
                exam_code="TEST",
                course=1,
                date=date.today() + timedelta(days=30),
                start_time="10:00",
                end_time="12:00",
                status="invalid",
                created_by=1
            )
    
    def test_add_exam_missing_created_by(self, service):
        """Test add_exam with missing created_by"""
        with pytest.raises(ValueError, match="User ID .* is required"):
            service.add_exam(
                title="Test",
                exam_code="TEST",
                course=1,
                date=date.today() + timedelta(days=30),
                start_time="10:00",
                end_time="12:00",
                created_by=None
            )
    
    def test_add_exam_duplicate_code(self, service):
        """Test add_exam with duplicate exam code"""
        with patch.object(service, 'exam_code_exists', return_value=True):
            with pytest.raises(ValueError, match="Exam code .* already exists"):
                service.add_exam(
                    title="Test",
                    exam_code="DUP",
                    course=1,
                    date=date.today() + timedelta(days=30),
                    start_time="10:00",
                    end_time="12:00",
                    created_by=1
                )
    
    def test_add_exam_past_date(self, service):
        """Test add_exam with past date"""
        with pytest.raises(ValueError, match="Exam date cannot be in the past"):
            service.add_exam(
                title="Test",
                exam_code="TEST",
                course=1,
                date=date.today() - timedelta(days=1),
                start_time="10:00",
                end_time="12:00",
                created_by=1
            )
    
    def test_add_exam_string_date(self, service):
        """Test add_exam with string date"""
        future_date = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts'):
                with patch('services.exams_service.get_conn') as mock_get_conn:
                    mock_conn = MagicMock()
                    mock_cursor = MagicMock()
                    mock_get_conn.return_value.__enter__.return_value = mock_conn
                    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
                    
                    mock_cursor.fetchone.return_value = {
                        "id": 1,
                        "title": "Test",
                        "exam_code": "TEST",
                        "course": 1,
                        "date": date.today() + timedelta(days=30),
                        "start_time": time(10, 0),
                        "end_time": time(12, 0),
                        "duration": 120,
                        "status": "scheduled",
                        "created_by": 1
                    }
                    
                    result = service.add_exam(
                        title="Test",
                        exam_code="TEST",
                        course=1,
                        date=future_date,
                        start_time="10:00",
                        end_time="12:00",
                        created_by=1
                    )
                    
                    assert result["id"] == 1
    
    # ========================================================================
    # get_exam TESTS
    # ========================================================================
    
    def test_get_exam_invalid_id(self, service):
        """Test get_exam with invalid ID"""
        with pytest.raises(ValueError, match="Exam ID must be a positive integer"):
            service.get_exam(0)
        with pytest.raises(ValueError, match="Exam ID must be a positive integer"):
            service.get_exam(-1)
    
    @patch('services.exams_service.get_conn')
    def test_get_exam_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully getting an exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "title": "Math Final",
            "exam_code": "MATH101",
            "course": 1,
            "date": date.today(),
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "duration": 120,
            "status": "scheduled",
            "created_by": 1
        }
        
        result = service.get_exam(1)
        
        assert result["id"] == 1
        assert result["title"] == "Math Final"
    
    @patch('services.exams_service.get_conn')
    def test_get_exam_not_found(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test get_exam returns None for non-existent exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        result = service.get_exam(999)
        
        assert result is None
    
    # ========================================================================
    # get_all_exams TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_get_all_exams_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully getting all exams"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Exam 1",
                "exam_code": "E1",
                "course": 1,
                "date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "scheduled"
            }
        ]
        
        results = service.get_all_exams()
        
        assert len(results) == 1
        assert results[0]["start_time"] == "10:00"
    
    @patch('services.exams_service.get_conn')
    def test_get_all_exams_empty(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test get_all_exams with no exams"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        results = service.get_all_exams()
        
        assert results == []
    
    @patch('services.exams_service.get_conn')
    def test_get_all_exams_exception(self, mock_get_conn, service, mock_conn):
        """Test get_all_exams handles exception"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")
        
        results = service.get_all_exams()
        
        assert results == []
    
    # ========================================================================
    # get_teacher_exams TESTS
    # ========================================================================
    
    def test_get_teacher_exams_invalid_id(self, service):
        """Test get_teacher_exams with invalid ID"""
        with pytest.raises(ValueError, match="Teacher ID must be a positive integer"):
            service.get_teacher_exams(0)
    
    @patch('services.exams_service.get_conn')
    def test_get_teacher_exams_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully getting teacher exams"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Math Exam",
                "exam_code": "MATH",
                "course": 1,
                "date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "scheduled",
                "created_by": 1
            }
        ]
        
        results = service.get_teacher_exams(1)
        
        assert len(results) == 1
        assert results[0]["created_by"] == 1
    
    # ========================================================================
    # get_student_exams TESTS
    # ========================================================================
    
    def test_get_student_exams_invalid_id(self, service):
        """Test get_student_exams with invalid ID"""
        with pytest.raises(ValueError, match="Student ID must be a positive integer"):
            service.get_student_exams(0)
    
    @patch('services.exams_service.get_conn')
    def test_get_student_exams_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully getting student exams"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Math Exam",
                "exam_code": "MATH",
                "course": 1,
                "course_name": "Mathematics",
                "course_code": "MATH101",
                "date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "published"
            }
        ]
        
        results = service.get_student_exams(1)
        
        assert len(results) == 1
        assert results[0]["course_name"] == "Mathematics"
    
    @patch('services.exams_service.get_conn')
    def test_get_student_exams_exception(self, mock_get_conn, service, mock_conn):
        """Test get_student_exams handles exception"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")
        
        results = service.get_student_exams(1)
        
        assert results == []
    
    # ========================================================================
    # delete_exam TESTS
    # ========================================================================
    
    def test_delete_exam_invalid_id(self, service):
        """Test delete_exam with invalid ID"""
        with pytest.raises(ValueError, match="Exam ID must be a positive integer"):
            service.delete_exam(0)
    
    @patch('services.exams_service.get_conn')
    def test_delete_exam_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully deleting an exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {"id": 1}
        
        result = service.delete_exam(1)
        
        assert result["id"] == 1
    
    @patch('services.exams_service.get_conn')
    def test_delete_exam_not_found(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test delete_exam raises error for non-existent exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        with pytest.raises(ValueError, match="Exam with id .* not found"):
            service.delete_exam(999)
    
    # ========================================================================
    # search_exams_by_code TESTS
    # ========================================================================
    
    def test_search_exams_by_code_empty_term(self, service):
        """Test search by code with empty term"""
        with pytest.raises(ValueError, match="Search term is required"):
            service.search_exams_by_code("")
    
    @patch('services.exams_service.get_conn')
    def test_search_exams_by_code_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully searching by exam code"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Math Final",
                "exam_code": "MATH101",
                "course": 1,
                "date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "scheduled"
            }
        ]
        
        results = service.search_exams_by_code("MATH101")
        
        assert len(results) == 1
        assert results[0]["exam_code"] == "MATH101"
    
    @patch('services.exams_service.get_conn')
    def test_search_exams_by_code_exception(self, mock_get_conn, service, mock_conn):
        """Test search by code handles exception"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")
        
        results = service.search_exams_by_code("TEST")
        
        assert results == []
    
    # ========================================================================
    # search_student_exams_by_course TESTS
    # ========================================================================
    
    def test_search_student_exams_by_course_empty_name(self, service):
        """Test search with empty course name"""
        with pytest.raises(ValueError, match="Course name is required"):
            service.search_student_exams_by_course(1, "")
    
    def test_search_student_exams_by_course_invalid_student_id(self, service):
        """Test search with invalid student ID"""
        with pytest.raises(ValueError, match="Valid student ID is required"):
            service.search_student_exams_by_course(0, "Math")
    
    @patch('services.exams_service.get_conn')
    def test_search_student_exams_by_course_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully searching student exams by course"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Math Exam",
                "exam_code": "MATH",
                "course": 1,
                "course_name": "Mathematics",
                "course_code": "MATH101",
                "date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "published"
            }
        ]
        
        results = service.search_student_exams_by_course(1, "Math")
        
        assert len(results) == 1
        assert "Mathematics" in results[0]["course_name"]
    
    # ========================================================================
    # filter_exams_by_status TESTS
    # ========================================================================
    
    def test_filter_exams_by_status_invalid(self, service):
        """Test filter with invalid status"""
        with pytest.raises(ValueError, match="Status must be one of"):
            service.filter_exams_by_status("invalid")
    
    def test_filter_exams_by_status_empty(self, service):
        """Test filter with empty status"""
        with pytest.raises(ValueError, match="Status must be one of"):
            service.filter_exams_by_status("")
    
    @patch('services.exams_service.get_conn')
    def test_filter_exams_by_status_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully filtering by status"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Scheduled Exam",
                "exam_code": "SCH1",
                "course": 1,
                "date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "scheduled"
            }
        ]
        
        results = service.filter_exams_by_status("scheduled")
        
        assert len(results) == 1
        assert results[0]["status"] == "scheduled"
    
    @patch('services.exams_service.get_conn')
    def test_filter_exams_by_status_case_insensitive(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test filter is case insensitive"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        results = service.filter_exams_by_status("SCHEDULED")
        
        assert results == []
        # Verify the SQL used lowercase
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == ("scheduled",)
    
    # ========================================================================
    # filter_student_exams_by_status TESTS
    # ========================================================================
    
    def test_filter_student_exams_by_status_invalid_student_id(self, service):
        """Test filter with invalid student ID"""
        with pytest.raises(ValueError, match="Valid student ID is required"):
            service.filter_student_exams_by_status(0, "scheduled")
    
    def test_filter_student_exams_by_status_invalid_status(self, service):
        """Test filter with invalid status"""
        with pytest.raises(ValueError, match="Status must be one of"):
            service.filter_student_exams_by_status(1, "invalid")
    
    @patch('services.exams_service.get_conn')
    def test_filter_student_exams_by_status_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully filtering student exams by status"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "title": "Completed Exam",
                "exam_code": "COMP1",
                "course": 1,
                "course_name": "Math",
                "course_code": "MATH101",
                "date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration": 120,
                "status": "completed"
            }
        ]
        
        results = service.filter_student_exams_by_status(1, "completed")
        
        assert len(results) == 1
        assert results[0]["status"] == "completed"
    
    # ========================================================================
    # can_publish_exam TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_can_publish_exam_not_found(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test can_publish_exam with non-existent exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        result = service.can_publish_exam(999)
        
        assert result["can_publish"] is False
        assert "not found" in result["message"]
    
    @patch('services.exams_service.get_conn')
    def test_can_publish_exam_past_date(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test can_publish_exam with past date"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        past_date = date.today() - timedelta(days=1)
        
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "date": past_date,
                "start_time": time(10, 0),
                "status": "scheduled"
            },
            None  # question count
        ]
        
        result = service.can_publish_exam(1)
        
        assert result["can_publish"] is False
        assert "already passed" in result["message"]
    
    @patch('services.exams_service.get_conn')
    def test_can_publish_exam_no_questions(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test can_publish_exam with no questions"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=7)
        
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "date": future_date,
                "start_time": time(10, 0),
                "status": "scheduled"
            },
            {"question_count": 0}
        ]
        
        result = service.can_publish_exam(1)
        
        assert result["can_publish"] is False
        assert "at least 1 question" in result["message"]
    
    @patch('services.exams_service.get_conn')
    def test_can_publish_exam_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test can_publish_exam success"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=7)
        
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "date": future_date,
                "start_time": time(10, 0),
                "status": "scheduled"
            },
            {"question_count": 5}
        ]
        
        result = service.can_publish_exam(1)
        
        assert result["can_publish"] is True
        assert result["question_count"] == 5
    
    @patch('services.exams_service.get_conn')
    def test_can_publish_exam_with_string_time(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test can_publish_exam with string start_time"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=7)
        
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "date": future_date,
                "start_time": "10:00",  # String format
                "status": "scheduled"
            },
            {"question_count": 3}
        ]
        
        result = service.can_publish_exam(1)
        
        assert result["can_publish"] is True
    
    # ========================================================================
    # update_exam TESTS
    # ========================================================================
    
    def test_update_exam_invalid_id(self, service):
        """Test update_exam with invalid ID"""
        with pytest.raises(ValueError, match="Exam ID must be a positive integer"):
            service.update_exam(0)
    
    @patch('services.exams_service.get_conn')
    def test_update_exam_not_found(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test update_exam with non-existent exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        with pytest.raises(ValueError, match="Exam with id .* not found"):
            service.update_exam(999, title="New Title")
    
    @patch('services.exams_service.get_conn')
    def test_update_exam_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully updating an exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=30)
        
        existing_exam = {
            "id": 1,
            "title": "Old Title",
            "exam_code": "OLD",
            "course": 1,
            "date": future_date,
            "start_time": "10:00",
            "end_time": "12:00",
            "status": "scheduled"
        }
        
        updated_exam = existing_exam.copy()
        updated_exam["title"] = "New Title"
        updated_exam["created_by"] = 1
        
        mock_cursor.fetchone.side_effect = [existing_exam, updated_exam]
        
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts'):
                result = service.update_exam(1, title="New Title")
                
                assert result["title"] == "New Title"
    
    @patch('services.exams_service.get_conn')
    def test_update_exam_duplicate_code(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test update_exam with duplicate exam code"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=30)
        
        existing_exam = {
            "id": 1,
            "title": "Test",
            "exam_code": "OLD",
            "course": 1,
            "date": future_date,
            "start_time": "10:00",
            "end_time": "12:00",
            "status": "scheduled"
        }
        
        mock_cursor.fetchone.return_value = existing_exam
        
        with patch.object(service, 'exam_code_exists', return_value=True):
            with pytest.raises(ValueError, match="Exam code .* already exists"):
                service.update_exam(1, exam_code="DUPLICATE")
    
    @patch('services.exams_service.get_conn')
    def test_update_exam_partial_update(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test updating only some fields"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        future_date = date.today() + timedelta(days=30)
        
        existing_exam = {
            "id": 1,
            "title": "Old Title",
            "exam_code": "TEST",
            "course": 1,
            "date": future_date,
            "start_time": "10:00",
            "end_time": "12:00",
            "status": "scheduled"
        }
        
        updated_exam = existing_exam.copy()
        updated_exam["title"] = "New Title"
        updated_exam["created_by"] = 1
        
        mock_cursor.fetchone.side_effect = [existing_exam, updated_exam]
        
        with patch.object(service, 'exam_code_exists', return_value=False):
            with patch.object(service, 'check_exam_conflicts'):
                # Only update title, keep rest the same
                result = service.update_exam(1, title="New Title")
                
                assert result["title"] == "New Title"
                assert result["exam_code"] == "TEST"
    
    # ========================================================================
    # publish_exam TESTS
    # ========================================================================
    
    @patch('services.exams_service.get_conn')
    def test_publish_exam_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully publishing an exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "title": "Test Exam",
            "exam_code": "TEST",
            "course": 1,
            "date": date.today(),
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "duration": 120,
            "status": "published"
        }
        
        with patch.object(service, 'can_publish_exam', return_value={"can_publish": True, "message": "OK", "question_count": 5}):
            result = service.publish_exam(1)
            
            assert result["status"] == "published"
    
    def test_publish_exam_validation_fails(self, service):
        """Test publish_exam when validation fails"""
        with patch.object(service, 'can_publish_exam', return_value={"can_publish": False, "message": "No questions", "question_count": 0}):
            with pytest.raises(ValueError, match="No questions"):
                service.publish_exam(1)
    
    @patch('services.exams_service.get_conn')
    def test_publish_exam_not_found(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test publish_exam with non-existent exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        with patch.object(service, 'can_publish_exam', return_value={"can_publish": True, "message": "OK", "question_count": 5}):
            with pytest.raises(ValueError, match="Exam with id .* not found"):
                service.publish_exam(999)
    
    # ========================================================================
    # update_exam_status TESTS
    # ========================================================================
    
    def test_update_exam_status_invalid_id(self, service):
        """Test update_exam_status with invalid ID"""
        with pytest.raises(ValueError, match="Exam ID must be a positive integer"):
            service.update_exam_status(0, "completed")
    
    def test_update_exam_status_invalid_status(self, service):
        """Test update_exam_status with invalid status"""
        with pytest.raises(ValueError, match="Status must be one of"):
            service.update_exam_status(1, "invalid")
    
    @patch('services.exams_service.get_conn')
    def test_update_exam_status_success(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test successfully updating exam status"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "title": "Test Exam",
            "exam_code": "TEST",
            "course": 1,
            "date": date.today(),
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "duration": 120,
            "status": "completed"
        }
        
        result = service.update_exam_status(1, "completed")
        
        assert result["status"] == "completed"
    
    @patch('services.exams_service.get_conn')
    def test_update_exam_status_not_found(self, mock_get_conn, service, mock_conn, mock_cursor):
        """Test update_exam_status with non-existent exam"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        with pytest.raises(ValueError, match="Exam with id .* not found"):
            service.update_exam_status(999, "completed")
    
    @patch('services.exams_service.get_conn')
    def test_update_exam_status_exception(self, mock_get_conn, service, mock_conn):
        """Test update_exam_status handles exception"""
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            service.update_exam_status(1, "completed")