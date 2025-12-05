import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, time as dt_time
from src.services.submission_service import SubmissionService


class TestSearchStudentSubmissions:
    """Unit tests for searching student submissions"""

    @pytest.fixture
    def service(self):
        """Create SubmissionService instance"""
        return SubmissionService()

    @pytest.fixture
    def mock_cursor(self):
        """Create a mock cursor"""
        cursor = MagicMock()
        cursor.__enter__ = Mock(return_value=cursor)
        cursor.__exit__ = Mock(return_value=False)
        return cursor

    @pytest.fixture
    def mock_conn(self, mock_cursor):
        """Create a mock connection"""
        conn = MagicMock()
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = mock_cursor
        return conn

    @pytest.fixture
    def sample_submissions(self):
        """Sample submission data - returned in the order from SQL (DESC by date)"""
        return [
            {
                "id": 5,
                "exam_code": 104,
                "submission_date": date(2024, 2, 15),
                "submission_time": dt_time(16, 20, 0),
                "score": 95,
                "score_grade": None,
                "status": "graded",
                "exam_title": "Python Advanced",
                "exam_id": "EXAM-104"
            },
            {
                "id": 4,
                "exam_code": 103,
                "submission_date": date(2024, 2, 10),
                "submission_time": dt_time(11, 45, 0),
                "score": None,
                "score_grade": None,
                "status": "pending",
                "exam_title": "Machine Learning",
                "exam_id": "EXAM-103"
            },
            {
                "id": 3,
                "exam_code": 102,
                "submission_date": date(2024, 2, 1),
                "submission_time": dt_time(9, 0, 0),
                "score": 78,
                "score_grade": None,
                "status": "graded",
                "exam_title": "Algorithms Final",
                "exam_id": "EXAM-102"
            },
            {
                "id": 2,
                "exam_code": 101,
                "submission_date": date(2024, 1, 20),
                "submission_time": dt_time(14, 15, 0),
                "score": 90,
                "score_grade": None,
                "status": "graded",
                "exam_title": "Data Structures",
                "exam_id": "EXAM-101"
            },
            {
                "id": 1,
                "exam_code": 100,
                "submission_date": date(2024, 1, 15),
                "submission_time": dt_time(10, 30, 0),
                "score": 85,
                "score_grade": None,
                "status": "graded",
                "exam_title": "Python Basics",
                "exam_id": "EXAM-100"
            }
        ]

    @pytest.fixture
    def total_marks_map(self):
        """Total marks mapping for exams"""
        return {
            100: 100,
            101: 100,
            102: 100,
            103: 100,
            104: 100
        }

    # ===== POSITIVE SCENARIOS =====

    def test_get_all_submissions_success(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test successfully retrieving all submissions"""
        # Arrange
        user_id = 1
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            result = service.get_student_submissions(user_id)

        # Assert
        assert len(result) == 5
        # Now ordered by date DESC, so sub5 (most recent) comes first
        assert result[0]["submission_id"] == "sub5"
        assert result[0]["exam_title"] == "Python Advanced"
        assert result[0]["score"] == "95/100"
        assert result[0]["percentage"] == "95.0%"
        assert result[0]["status"] == "graded"

    def test_search_by_exact_submission_id(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching by exact submission ID"""
        # Arrange
        user_id = 1
        search_id = "sub1"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if s["submission_id"] == search_id]

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["submission_id"] == "sub1"
        assert result[0]["exam_title"] == "Python Basics"

    def test_search_by_submission_id_case_insensitive(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching by submission ID is case insensitive"""
        # Arrange
        user_id = 1
        search_id = "SUB2"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if s["submission_id"].lower() == search_id.lower()]

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == 2
        assert result[0]["exam_title"] == "Data Structures"

    def test_search_by_partial_submission_id(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching by partial submission ID"""
        # Arrange
        user_id = 1
        search_term = "sub"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if search_term.lower() in s["submission_id"].lower()]

        # Assert
        assert len(result) == 5
        for submission in result:
            assert submission["submission_id"].lower().startswith(search_term.lower())

    def test_search_by_exact_exam_title(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching by exact exam title"""
        # Arrange
        user_id = 1
        search_title = "Machine Learning"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if s["exam_title"] == search_title]

        # Assert
        assert len(result) == 1
        assert result[0]["exam_title"] == "Machine Learning"
        assert result[0]["status"] == "pending"
        assert result[0]["score"] is None

    def test_search_by_partial_exam_title(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching by partial exam title"""
        # Arrange
        user_id = 1
        search_term = "Python"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if search_term.lower() in s["exam_title"].lower()]

        # Assert
        assert len(result) == 2
        titles = [s["exam_title"] for s in result]
        assert "Python Basics" in titles
        assert "Python Advanced" in titles

    def test_search_by_exam_title_case_insensitive(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching by exam title is case insensitive"""
        # Arrange
        user_id = 1
        search_title = "algorithms final"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if s["exam_title"].lower() == search_title.lower()]

        # Assert
        assert len(result) == 1
        assert result[0]["exam_title"] == "Algorithms Final"

    def test_submission_has_all_required_fields(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test that submissions have all required fields"""
        # Arrange
        user_id = 1
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            result = service.get_student_submissions(user_id)

        # Assert
        assert len(result) > 0
        submission = result[0]
        assert "id" in submission
        assert "submission_id" in submission
        assert "exam_title" in submission
        assert "exam_id" in submission
        assert "date" in submission
        assert "time" in submission
        assert "score" in submission
        assert "percentage" in submission
        assert "status" in submission

    def test_submissions_ordered_by_date_descending(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test that submissions are ordered by date descending"""
        # Arrange
        user_id = 1
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            result = service.get_student_submissions(user_id)

        # Assert
        # Submissions should be ordered from newest to oldest based on submission_date
        # sample_submissions are already ordered: id 5 (02/15) -> id 4 (02/10) -> id 3 (02/01) -> id 2 (01/20) -> id 1 (01/15)
        assert result[0]["id"] == 5  # Most recent: 02/15/2024
        assert result[0]["date"] == "02/15/2024"
        assert result[-1]["id"] == 1  # Oldest: 01/15/2024
        assert result[-1]["date"] == "01/15/2024"

    def test_calculate_percentage_correctly(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test percentage calculation"""
        # Arrange
        user_id = 1
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            result = service.get_student_submissions(user_id)

        # Assert
        # Submissions are ordered by date desc: id 5 (95/100), id 4 (None), id 3 (78/100), id 2 (90/100), id 1 (85/100)
        assert result[0]["id"] == 5
        assert result[0]["percentage"] == "95.0%"  # id 5: 95/100
        assert result[0]["score"] == "95/100"
        
        assert result[2]["id"] == 3
        assert result[2]["percentage"] == "78.0%"  # id 3: 78/100
        assert result[2]["score"] == "78/100"
        
        assert result[3]["id"] == 2
        assert result[3]["percentage"] == "90.0%"  # id 2: 90/100
        assert result[3]["score"] == "90/100"
        
        assert result[4]["id"] == 1
        assert result[4]["percentage"] == "85.0%"  # id 1: 85/100
        assert result[4]["score"] == "85/100"

    def test_pending_submission_no_score(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test pending submission has no score or percentage"""
        # Arrange
        user_id = 1
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            result = service.get_student_submissions(user_id)
            pending_submission = [s for s in result if s["status"] == "pending"][0]

        # Assert
        assert pending_submission["score"] is None
        assert pending_submission["percentage"] is None
        assert pending_submission["exam_title"] == "Machine Learning"

    # ===== NEGATIVE SCENARIOS =====

    def test_search_no_matching_submission_id(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching with no matching submission ID"""
        # Arrange
        user_id = 1
        search_id = "sub999"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if s["submission_id"] == search_id]

        # Assert
        assert len(result) == 0

    def test_search_no_matching_exam_title(self, service, mock_conn, mock_cursor, sample_submissions, total_marks_map):
        """Test searching with no matching exam title"""
        # Arrange
        user_id = 1
        search_title = "Nonexistent Exam"
        
        mock_cursor.fetchall.side_effect = [
            sample_submissions,
            [{"exam_id": k, "total_marks": v} for k, v in total_marks_map.items()]
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            all_submissions = service.get_student_submissions(user_id)
            result = [s for s in all_submissions if search_title.lower() in s["exam_title"].lower()]

        # Assert
        assert len(result) == 0

    def test_user_with_no_submissions(self, service, mock_conn, mock_cursor):
        """Test user with no submissions"""
        # Arrange
        user_id = 999
        mock_cursor.fetchall.side_effect = [
            [],  # No submissions
            []   # No total marks
        ]

        with patch("src.services.submission_service.get_conn", return_value=mock_conn):
            # Act
            result = service.get_student_submissions(user_id)

        # Assert
        assert len(result) == 0

    def test_calculate_percentage_with_none_score(self, service):
        """Test percentage calculation with None score"""
        # Act
        result = service.calculate_percentage(None, 100)

        # Assert
        assert result is None

    def test_calculate_percentage_with_zero_total(self, service):
        """Test percentage calculation with zero total marks"""
        # Act
        result = service.calculate_percentage(50, 0)

        # Assert
        assert result is None

    def test_calculate_percentage_with_negative_total(self, service):
        """Test percentage calculation with negative total marks"""
        # Act
        result = service.calculate_percentage(50, -100)

        # Assert
        assert result is None

    def test_resolve_status_graded(self, service):
        """Test status resolution for graded"""
        # Act
        result = service.resolve_status("GRADED")

        # Assert
        assert result == "graded"

    def test_resolve_status_pending(self, service):
        """Test status resolution for pending"""
        # Act
        result = service.resolve_status("PENDING")

        # Assert
        assert result == "pending"

    def test_resolve_status_submitted(self, service):
        """Test status resolution for submitted"""
        # Act
        result = service.resolve_status("SUBMITTED")

        # Assert
        assert result == "submitted"

    def test_resolve_status_none(self, service):
        """Test status resolution for None"""
        # Act
        result = service.resolve_status(None)

        # Assert
        assert result == "submitted"

    def test_resolve_status_empty_string(self, service):
        """Test status resolution for empty string"""
        # Act
        result = service.resolve_status("")

        # Assert
        assert result == "submitted"

    def test_format_submission_id(self, service):
        """Test submission ID formatting"""
        # Act
        result = service.format_submission_id(123)

        # Assert
        assert result == "sub123"

    def test_format_date(self, service):
        """Test date formatting"""
        # Act
        result = service.format_date(date(2024, 3, 15))

        # Assert
        assert result == "03/15/2024"

    def test_format_date_none(self, service):
        """Test date formatting with None"""
        # Act
        result = service.format_date(None)

        # Assert
        assert result is None

    def test_format_time(self, service):
        """Test time formatting"""
        # Act
        result = service.format_time(dt_time(14, 30, 45))

        # Assert
        assert result == "14:30:45"

    def test_format_time_none(self, service):
        """Test time formatting with None"""
        # Act
        result = service.format_time(None)

        # Assert
        assert result is None