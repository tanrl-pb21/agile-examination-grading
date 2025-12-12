"""
Unit Tests for ReportService
Testing service layer with mocked database
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.report_service import ReportsService
import psycopg


class TestReportsService:
    """Unit tests for ReportsService"""
    
    @pytest.fixture
    def mock_cursor(self):
        """Mock database cursor"""
        mock_cursor = Mock()
        mock_cursor.execute = Mock()
        mock_cursor.fetchone = Mock()
        mock_cursor.fetchall = Mock()
        return mock_cursor
    
    @pytest.fixture
    def mock_conn(self, mock_cursor):
        """Mock database connection with proper context manager setup"""
        mock_conn = Mock()
        
        # Set up cursor as a context manager
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        mock_conn.cursor = Mock(return_value=cursor_context)
        
        # Set up connection as a context manager
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        return mock_conn
    
    @pytest.fixture
    def service(self):
        """Create ReportsService instance"""
        return ReportsService()
    
    # ========================
    # get_completed_exams Tests
    # ========================
    
    def test_get_completed_exams_without_instructor_id(self, service, mock_conn, mock_cursor):
        """Test getting completed exams without instructor filter"""
        # Mock data
        mock_rows = [
            {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "MT2024-001",
                "date": "2024-03-15",
                "course_name": "Mathematics 101",
                "course_code": "MATH101",
                "total_students": 30,
                "submitted": 28,
                "graded": 25,
                "average_score": 78.5678
            }
        ]
        
        # Mock cursor execution
        mock_cursor.fetchall.return_value = mock_rows
        
        # Mock get_conn to return our mock_conn
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            # Set up get_conn as a context manager
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_completed_exams()
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["title"] == "Midterm Exam"
        assert result[0]["average_score"] == 78.57  # Rounded to 2 decimals
    
    def test_get_completed_exams_with_instructor_id(self, service, mock_conn, mock_cursor):
        """Test getting completed exams with instructor filter"""
        mock_rows = [
            {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "MT2024-001",
                "date": "2024-03-15",
                "course_name": "Mathematics 101",
                "course_code": "MATH101",
                "total_students": 30,
                "submitted": 28,
                "graded": 25,
                "average_score": 78.5
            }
        ]
        
        mock_cursor.fetchall.return_value = mock_rows
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_completed_exams(instructor_id=1)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        
        # Verify SQL includes instructor filter
        call_args = mock_cursor.execute.call_args
        assert len(call_args[0]) == 2  # SQL and params
        assert len(call_args[0][1]) == 1  # One parameter (instructor_id)
        assert call_args[0][1][0] == 1
    
    def test_get_completed_exams_empty(self, service, mock_conn, mock_cursor):
        """Test getting completed exams when none exist"""
        mock_cursor.fetchall.return_value = []
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_completed_exams()
        
        assert result == []
    
    def test_get_completed_exams_none_result(self, service, mock_conn, mock_cursor):
        """Test getting completed exams when fetchall returns None"""
        mock_cursor.fetchall.return_value = None
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_completed_exams()
        
        assert result == []
    
    def test_get_completed_exams_database_error(self, service, mock_conn, mock_cursor):
        """Test getting completed exams when database error occurs"""
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_completed_exams()
        
        assert result == []
    
    def test_get_completed_exams_rounding(self, service, mock_conn, mock_cursor):
        """Test that average scores are properly rounded"""
        mock_rows = [
            {
                "id": 1,
                "title": "Test",
                "exam_code": "T001",
                "date": "2024-03-15",
                "course_name": "Test",
                "course_code": "TEST",
                "total_students": 10,
                "submitted": 8,
                "graded": 5,
                "average_score": 78.567891234
            }
        ]
        
        mock_cursor.fetchall.return_value = mock_rows
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_completed_exams()
        
        assert result[0]["average_score"] == 78.57
    
    # ========================
    # get_exam_student_scores Tests
    # ========================
    
    def test_get_exam_student_scores_success(self, service, mock_conn, mock_cursor):
        """Test getting student scores successfully"""
        mock_rows = [
            {
                "student_id": 101,
                "user_email": "student1@example.com",
                "student_number": "S001",
                "score": 95,
                "score_grade": "A",
                "status": "graded",
                "submission_date": "2024-03-16T10:30:00"
            },
            {
                "student_id": 102,
                "user_email": "student2@example.com",
                "student_number": "S002",
                "score": 85,
                "score_grade": "B",
                "status": "graded",
                "submission_date": "2024-03-16T11:15:00"
            }
        ]
        
        mock_cursor.fetchall.return_value = mock_rows
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_student_scores(1)
        
        assert len(result) == 2
        assert result[0]["student_id"] == 101
        assert result[0]["score"] == 95
        assert result[0]["score_grade"] == "A"
        assert result[1]["student_id"] == 102
        assert result[1]["score"] == 85
    
    def test_get_exam_student_scores_with_instructor_id(self, service, mock_conn, mock_cursor):
        """Test getting student scores with instructor filter"""
        mock_rows = [
            {
                "student_id": 101,
                "user_email": "student1@example.com",
                "student_number": "S001",
                "score": 95,
                "score_grade": "A",
                "status": "graded",
                "submission_date": "2024-03-16"
            }
        ]
        
        mock_cursor.fetchall.return_value = mock_rows
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_student_scores(1, instructor_id=1)
        
        assert len(result) == 1
        assert result[0]["student_id"] == 101
        
        # Verify instructor_id was passed
        call_args = mock_cursor.execute.call_args
        assert len(call_args[0][1]) == 2  # exam_id and instructor_id
        assert call_args[0][1][1] == 1
    
    def test_get_exam_student_scores_empty(self, service, mock_conn, mock_cursor):
        """Test getting student scores when none exist"""
        mock_cursor.fetchall.return_value = []
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_student_scores(1)
        
        assert result == []
    
    def test_get_exam_student_scores_none_result(self, service, mock_conn, mock_cursor):
        """Test getting student scores when fetchall returns None"""
        mock_cursor.fetchall.return_value = None
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_student_scores(1)
        
        assert result == []
    
    def test_get_exam_student_scores_with_pending_submissions(self, service, mock_conn, mock_cursor):
        """Test getting student scores including pending submissions"""
        mock_rows = [
            {
                "student_id": 101,
                "user_email": "student1@example.com",
                "student_number": "S001",
                "score": None,
                "score_grade": None,
                "status": "pending",
                "submission_date": None
            }
        ]
        
        mock_cursor.fetchall.return_value = mock_rows
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_student_scores(1)
        
        assert len(result) == 1
        assert result[0]["status"] == "pending"
        assert result[0]["score"] is None
    
    def test_get_exam_student_scores_database_error(self, service, mock_conn, mock_cursor):
        """Test getting student scores when database error occurs"""
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_student_scores(1)
        
        assert result == []
    
    # ========================
    # get_exam_performance_stats Tests
    # ========================
    
    def test_get_exam_performance_stats_success(self, service, mock_conn, mock_cursor):
        """Test getting exam performance statistics successfully"""
        # Mock exam data
        mock_exam_data = {
            "id": 1,
            "title": "Midterm Exam",
            "exam_code": "MT2024-001",
            "date": "2024-03-15",
            "course_name": "Mathematics 101",
            "course_code": "MATH101",
            "total_points": 100
        }

        # Mock statistics
        mock_stats = {
            "total_students": 30,
            "submitted": 28,
            "graded": 25,
            "average_score": 78.5,
            "highest_score": 98,
            "lowest_score": 45
        }

        # Mock grade distribution
        mock_grades = [
            {"score_grade": "A", "count": 8},
            {"score_grade": "B", "count": 10}
        ]

        # Mock passed count
        mock_passed = {"passed_count": 20}

        # Mock score ranges - need ALL range fields
        mock_ranges = {
            "range_90_100": 5,
            "range_80_89": 8,
            "range_70_79": 7,
            "range_60_69": 3,
            "range_50_59": 1,
            "range_40_49": 1,
            "range_30_39": 0,
            "range_20_29": 0,
            "range_10_19": 0,
            "range_0_9": 0
        }

        mock_cursor.fetchone.side_effect = [mock_exam_data, mock_stats, mock_passed, mock_ranges]
        mock_cursor.fetchall.return_value = mock_grades

        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)

            result = service.get_exam_performance_stats(1)

        assert result is not None
        assert "exam_info" in result
        assert "statistics" in result
        assert "grade_distribution" in result
        assert "score_ranges" in result
        
        exam_info = result["exam_info"]
        assert exam_info["id"] == 1
        assert exam_info["title"] == "Midterm Exam"
        
        stats = result["statistics"]
        assert stats["total_students"] == 30
        assert stats["average_score"] == 78.5
        assert stats["pass_rate"] == 80.0  # 20/25 * 100
        
        # Check grade distribution includes all grades
        assert len(result["grade_distribution"]) == 12
        
        # Check score ranges
        assert len(result["score_ranges"]) == 10
    
    def test_get_exam_performance_stats_with_instructor_filter(self, service, mock_conn, mock_cursor):
        """Test getting performance stats with instructor filter"""
        mock_exam_data = {
            "id": 1,
            "title": "Midterm Exam",
            "exam_code": "MT2024-001",
            "date": "2024-03-15",
            "course_name": "Mathematics 101",
            "course_code": "MATH101",
            "total_points": 100
        }
        
        mock_stats = {
            "total_students": 30,
            "submitted": 28,
            "graded": 25,
            "average_score": 78.5,
            "highest_score": 98,
            "lowest_score": 45
        }
        
        mock_passed = {"passed_count": 20}
        
        mock_ranges = {
            "range_90_100": 5,
            "range_80_89": 8,
            "range_70_79": 7,
            "range_60_69": 3,
            "range_50_59": 1,
            "range_40_49": 1,
            "range_30_39": 0,
            "range_20_29": 0,
            "range_10_19": 0,
            "range_0_9": 0
        }
        
        mock_cursor.fetchone.side_effect = [mock_exam_data, mock_stats, mock_passed, mock_ranges]
        mock_cursor.fetchall.return_value = []

        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)

            result = service.get_exam_performance_stats(1, instructor_id=1)

        assert result is not None
        
        # Verify instructor_id was used in first query
        first_call = mock_cursor.execute.call_args_list[0]
        assert len(first_call[0][1]) == 2  # exam_id and instructor_id
        assert first_call[0][1][1] == 1
    
    def test_get_exam_performance_stats_exam_not_found(self, service, mock_conn, mock_cursor):
        """Test getting performance stats for non-existent exam"""
        mock_cursor.fetchone.return_value = None
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_performance_stats(999)
        
        assert result is None
    
    def test_get_exam_performance_stats_no_graded_submissions(self, service, mock_conn, mock_cursor):
        """Test getting performance stats when no submissions are graded"""
        mock_exam_data = {
            "id": 1,
            "title": "Midterm Exam",
            "exam_code": "MT2024-001",
            "date": "2024-03-15",
            "course_name": "Mathematics 101",
            "course_code": "MATH101",
            "total_points": 100
        }
        
        mock_stats = {
            "total_students": 30,
            "submitted": 0,
            "graded": 0,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0
        }
        
        mock_cursor.fetchone.side_effect = [mock_exam_data, mock_stats, {"passed_count": 0}, {}]
        mock_cursor.fetchall.return_value = []
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_performance_stats(1)
        
        assert result is not None
        stats = result["statistics"]
        assert stats["graded"] == 0
        assert stats["pass_rate"] == 0
        assert len(result["grade_distribution"]) == 12
        assert len(result["score_ranges"]) == 10
    
    def test_get_exam_performance_stats_zero_total_points(self, service, mock_conn, mock_cursor):
        """Test stats when exam has 0 total points"""
        mock_exam_data = {
            "id": 1,
            "title": "Test",
            "exam_code": "T001",
            "date": "2024-03-15",
            "course_name": "Test",
            "course_code": "TEST",
            "total_points": 0
        }
        
        mock_stats = {
            "total_students": 10,
            "submitted": 5,
            "graded": 5,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0
        }
        
        mock_cursor.fetchone.side_effect = [mock_exam_data, mock_stats, {"passed_count": 0}, {}]
        mock_cursor.fetchall.return_value = []
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_performance_stats(1)
        
        assert result is not None
        assert result["exam_info"]["total_points"] == 0
    
    def test_get_exam_performance_stats_database_error(self, service, mock_conn, mock_cursor):
        """Test getting performance stats when database error occurs"""
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_performance_stats(1)
        
        assert result is None
    
    def test_get_exam_performance_stats_all_grades(self, service, mock_conn, mock_cursor):
        """Test that all grade types are included in distribution"""
        mock_exam_data = {
            "id": 1,
            "title": "Test",
            "exam_code": "T001",
            "date": "2024-03-15",
            "course_name": "Test",
            "course_code": "TEST",
            "total_points": 100
        }
        
        mock_stats = {
            "total_students": 30,
            "submitted": 25,
            "graded": 24,
            "average_score": 75.0,
            "highest_score": 95,
            "lowest_score": 55
        }
        
        # Mock all possible grades
        mock_grades = [
            {"score_grade": "A+", "count": 2},
            {"score_grade": "A", "count": 3},
            {"score_grade": "B", "count": 5},
        ]
        
        mock_cursor.fetchone.side_effect = [mock_exam_data, mock_stats, {"passed_count": 20}, {}]
        mock_cursor.fetchall.return_value = mock_grades
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_performance_stats(1)
        
        assert result is not None
        # Should have all 12 grade types
        assert len(result["grade_distribution"]) == 12
        
        # Check that grades are in expected order
        grades = [g["grade"] for g in result["grade_distribution"]]
        expected_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "Pending"]
        assert grades == expected_grades
    
    # ========================
    # get_instructor_courses Tests
    # ========================
    
    def test_get_instructor_courses_success(self, service, mock_conn, mock_cursor):
        """Test getting instructor courses successfully"""
        mock_rows = [
            {
                "id": 101,
                "course_code": "MATH101",
                "course_name": "Mathematics 101",
                "description": "Introduction to Mathematics",
                "status": "active",
                "student_count": 30,
                "exam_count": 2
            },
            {
                "id": 102,
                "course_code": "PHYS101",
                "course_name": "Physics 101",
                "description": "Introduction to Physics",
                "status": "active",
                "student_count": 25,
                "exam_count": 1
            }
        ]
        
        mock_cursor.fetchall.return_value = mock_rows
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_instructor_courses(1)
        
        assert len(result) == 2
        assert result[0]["course_code"] == "MATH101"
        assert result[0]["student_count"] == 30
        assert result[0]["exam_count"] == 2
        assert result[1]["course_code"] == "PHYS101"
        assert result[1]["student_count"] == 25
    
    def test_get_instructor_courses_empty(self, service, mock_conn, mock_cursor):
        """Test getting instructor courses when instructor has none"""
        mock_cursor.fetchall.return_value = []
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_instructor_courses(999)
        
        assert result == []
    
    def test_get_instructor_courses_none_result(self, service, mock_conn, mock_cursor):
        """Test getting instructor courses when fetchall returns None"""
        mock_cursor.fetchall.return_value = None
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_instructor_courses(1)
        
        assert result == []
    
    def test_get_instructor_courses_database_error(self, service, mock_conn, mock_cursor):
        """Test getting instructor courses when database error occurs"""
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_instructor_courses(1)
        
        assert result == []
    
    # ========================
    # Integration and Edge Case Tests
    # ========================
    
    def test_exception_handling_in_all_methods(self, service):
        """Test that all methods handle exceptions gracefully"""
        with patch('src.services.report_service.get_conn', side_effect=Exception("Connection failed")):
            assert service.get_completed_exams() == []
            assert service.get_exam_performance_stats(1) is None
            assert service.get_exam_student_scores(1) == []
            assert service.get_instructor_courses(1) == []
    
    def test_cursor_uses_dict_row_factory(self, service, mock_conn, mock_cursor):
        """Test that cursor is created with dict_row factory"""
        mock_cursor.fetchall.return_value = []
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            with patch('src.services.report_service.dict_row') as mock_dict_row:
                service.get_completed_exams()
                
                # Verify cursor was called with row_factory
                mock_conn.cursor.assert_called()
                call_kwargs = mock_conn.cursor.call_args[1]
                assert 'row_factory' in call_kwargs
                assert call_kwargs['row_factory'] == mock_dict_row
    
    def test_get_exam_performance_stats_percentage_calculations(self, service, mock_conn, mock_cursor):
        """Test that percentages are calculated correctly"""
        mock_exam_data = {
            "id": 1,
            "title": "Test",
            "exam_code": "T001",
            "date": "2024-03-15",
            "course_name": "Test",
            "course_code": "TEST",
            "total_points": 100
        }
        
        mock_stats = {
            "total_students": 20,
            "submitted": 20,
            "graded": 10,
            "average_score": 75.5555,
            "highest_score": 95,
            "lowest_score": 55
        }
        
        mock_grades = [{"score_grade": "A", "count": 5}]
        
        mock_cursor.fetchone.side_effect = [mock_exam_data, mock_stats, {"passed_count": 8}, {}]
        mock_cursor.fetchall.return_value = mock_grades
        
        with patch('src.services.report_service.get_conn') as mock_get_conn:
            mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_conn.return_value.__exit__ = Mock(return_value=None)
            
            result = service.get_exam_performance_stats(1)
        
        # Check pass rate calculation: 8/10 * 100 = 80
        assert result["statistics"]["pass_rate"] == 80.0
        
        # Check grade percentage: 5/10 * 100 = 50
        a_grade = next(g for g in result["grade_distribution"] if g["grade"] == "A")
        assert a_grade["percentage"] == 50.0

    def test_get_completed_exams_endpoint_exception(self):
        """Test get_completed_exams endpoint exception handling"""
        from src.routers.report import get_completed_exams
        
        with patch('src.routers.report.service.get_completed_exams', side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                get_completed_exams(instructor_id=None)
            assert "Database error" in str(exc_info.value)
    
    def test_get_exam_performance_endpoint_exception(self):
        """Test get_exam_performance endpoint exception handling"""
        from src.routers.report import get_exam_performance
        
        with patch('src.routers.report.service.get_exam_performance_stats', side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                get_exam_performance(exam_id=1, instructor_id=None)
            assert "Database error" in str(exc_info.value)
    
    def test_get_exam_performance_invalid_id(self):
        """Test get_exam_performance with invalid exam ID"""
        from src.routers.report import get_exam_performance
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            get_exam_performance(exam_id=0, instructor_id=None)
        assert exc_info.value.status_code == 400
    
    def test_get_exam_performance_not_found(self):
        """Test get_exam_performance when exam not found"""
        from src.routers.report import get_exam_performance
        from fastapi import HTTPException
        
        with patch('src.routers.report.service.get_exam_performance_stats', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_exam_performance(exam_id=999, instructor_id=None)
            assert exc_info.value.status_code == 404
    
    def test_get_exam_performance_not_found_with_instructor(self):
        """Test get_exam_performance when exam not found with instructor filter"""
        from src.routers.report import get_exam_performance
        from fastapi import HTTPException
        
        with patch('src.routers.report.service.get_exam_performance_stats', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_exam_performance(exam_id=999, instructor_id=1)
            assert exc_info.value.status_code == 404
            assert "don't have access" in str(exc_info.value.detail)
    
    def test_get_exam_student_scores_endpoint_exception(self):
        """Test get_exam_student_scores endpoint exception handling"""
        from src.routers.report import get_exam_student_scores
        
        with patch('src.routers.report.service.get_exam_student_scores', side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                get_exam_student_scores(exam_id=1, instructor_id=None)
            assert "Database error" in str(exc_info.value)
    
    def test_get_exam_student_scores_invalid_id(self):
        """Test get_exam_student_scores with invalid exam ID"""
        from src.routers.report import get_exam_student_scores
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            get_exam_student_scores(exam_id=-1, instructor_id=None)
        assert exc_info.value.status_code == 400
    
    def test_get_exam_student_scores_not_found(self):
        """Test get_exam_student_scores when no scores found"""
        from src.routers.report import get_exam_student_scores
        from fastapi import HTTPException
        
        with patch('src.routers.report.service.get_exam_student_scores', return_value=[]):
            with pytest.raises(HTTPException) as exc_info:
                get_exam_student_scores(exam_id=999, instructor_id=None)
            assert exc_info.value.status_code == 404
    
    def test_get_exam_student_scores_not_found_with_instructor(self):
        """Test get_exam_student_scores when no scores found with instructor filter"""
        from src.routers.report import get_exam_student_scores
        from fastapi import HTTPException
        
        with patch('src.routers.report.service.get_exam_student_scores', return_value=[]):
            with pytest.raises(HTTPException) as exc_info:
                get_exam_student_scores(exam_id=999, instructor_id=1)
            assert exc_info.value.status_code == 404
            assert "don't have access" in str(exc_info.value.detail)
    
    def test_get_my_courses_endpoint_exception(self):
        """Test get_my_courses endpoint exception handling"""
        from src.routers.report import get_my_courses
        
        with patch('src.routers.report.service.get_instructor_courses', side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                get_my_courses(instructor_id=1)
            assert "Database error" in str(exc_info.value)
    
    def test_get_my_courses_missing_instructor_id(self):
        """Test get_my_courses without instructor ID"""
        from src.routers.report import get_my_courses
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            get_my_courses(instructor_id=None)
        assert exc_info.value.status_code == 400
    
    def test_get_completed_exams_endpoint_success(self):
        """Test get_completed_exams endpoint success path"""
        from src.routers.report import get_completed_exams
        
        mock_data = [{"id": 1, "title": "Test"}]
        with patch('src.routers.report.service.get_completed_exams', return_value=mock_data):
            result = get_completed_exams(instructor_id=1)
            assert result == mock_data
    
    def test_get_completed_exams_endpoint_empty(self):
        """Test get_completed_exams endpoint with empty result"""
        from src.routers.report import get_completed_exams
        
        with patch('src.routers.report.service.get_completed_exams', return_value=None):
            result = get_completed_exams(instructor_id=1)
            assert result == []
    
    def test_get_exam_performance_endpoint_success(self):
        """Test get_exam_performance endpoint success path"""
        from src.routers.report import get_exam_performance
        
        mock_data = {"exam_info": {"id": 1}, "statistics": {}}
        with patch('src.routers.report.service.get_exam_performance_stats', return_value=mock_data):
            result = get_exam_performance(exam_id=1, instructor_id=None)
            assert result == mock_data
    
    def test_get_exam_student_scores_endpoint_success(self):
        """Test get_exam_student_scores endpoint success path"""
        from src.routers.report import get_exam_student_scores
        
        mock_data = [{"student_id": 1, "score": 95}]
        with patch('src.routers.report.service.get_exam_student_scores', return_value=mock_data):
            result = get_exam_student_scores(exam_id=1, instructor_id=None)
            assert result == mock_data
    
    def test_get_my_courses_endpoint_success(self):
        """Test get_my_courses endpoint success path"""
        from src.routers.report import get_my_courses
        
        mock_data = [{"id": 1, "course_code": "TEST101"}]
        with patch('src.routers.report.service.get_instructor_courses', return_value=mock_data):
            result = get_my_courses(instructor_id=1)
            assert result == mock_data
    
    def test_get_my_courses_endpoint_empty(self):
        """Test get_my_courses endpoint with empty result"""
        from src.routers.report import get_my_courses
        
        with patch('src.routers.report.service.get_instructor_courses', return_value=None):
            result = get_my_courses(instructor_id=1)
            assert result == []
    
    # ========================
    # Integration and Edge Case Tests
    # ========================
    
    def test_exception_handling_in_all_methods(self, service):
        """Test that all methods handle exceptions gracefully"""
        with patch('src.services.report_service.get_conn', side_effect=Exception("Connection failed")):
            assert service.get_completed_exams() == []
            assert service.get_exam_performance_stats(1) is None
            assert service.get_exam_student_scores(1) == []
            assert service.get_instructor_courses(1) == []