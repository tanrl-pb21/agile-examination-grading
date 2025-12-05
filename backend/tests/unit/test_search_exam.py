# tests/unit/test_exams_service_search.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import time
from src.services.exams_service import ExamService


class TestExamSearchByTitle(unittest.TestCase):
    def setUp(self):
        self.service = ExamService()

        # Sample exams with time objects
        self.mock_exams = [
            {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "CS101-MID",
                "course": 1,
                "date": "2025-12-15",
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "duration": 120,
                "status": "scheduled",
            },
            {
                "id": 2,
                "title": "Final Exam",
                "exam_code": "CS101-FIN",
                "course": 1,
                "date": "2025-12-20",
                "start_time": time(14, 0),
                "end_time": time(16, 0),
                "duration": 120,
                "status": "scheduled",
            },
            {
                "id": 3,
                "title": "Mathematics Quiz",
                "exam_code": "MATH101-QZ",
                "course": 2,
                "date": "2025-12-18",
                "start_time": time(10, 30),
                "end_time": time(11, 30),
                "duration": 60,
                "status": "scheduled",
            },
        ]

    @patch("src.services.exams_service.get_conn")
    def test_search_title_found(self, mock_get_conn):
        """Test searching exam by title - result found"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_exams_by_title("Midterm")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Midterm Exam")
        self.assertEqual(results[0]["exam_code"], "CS101-MID")

    @patch("src.services.exams_service.get_conn")
    def test_search_title_not_found(self, mock_get_conn):
        """Test searching exam by title - no results"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_exams_by_title("NonExistent")

        self.assertEqual(len(results), 0)

    @patch("src.services.exams_service.get_conn")
    def test_search_title_case_insensitive(self, mock_get_conn):
        """Test searching exam by title - case insensitive"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_exams_by_title("MIDTERM")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Midterm Exam")

    @patch("src.services.exams_service.get_conn")
    def test_search_title_partial_match(self, mock_get_conn):
        """Test searching exam by partial title"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            self.mock_exams[0],
            self.mock_exams[1],
        ]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_exams_by_title("Exam")

        self.assertEqual(len(results), 2)

    def test_search_title_empty_string(self):
        """Test searching with empty string raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.search_exams_by_title("")

        self.assertIn("Search term is required", str(context.exception))

    def test_search_title_whitespace_only(self):
        """Test searching with whitespace only raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.search_exams_by_title("   ")

        self.assertIn("Search term is required", str(context.exception))


class TestExamSearchByCode(unittest.TestCase):
    def setUp(self):
        self.service = ExamService()

        self.mock_exams = [
            {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "CS101-MID",
                "course": 1,
                "date": "2025-12-15",
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "duration": 120,
                "status": "scheduled",
            },
            {
                "id": 2,
                "title": "Final Exam",
                "exam_code": "CS101-FIN",
                "course": 1,
                "date": "2025-12-20",
                "start_time": time(14, 0),
                "end_time": time(16, 0),
                "duration": 120,
                "status": "scheduled",
            },
        ]

    @patch("src.services.exams_service.get_conn")
    def test_search_code_found(self, mock_get_conn):
        """Test searching exam by code - result found"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_exams_by_code("CS101-MID")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["exam_code"], "CS101-MID")
        self.assertEqual(results[0]["title"], "Midterm Exam")

    @patch("src.services.exams_service.get_conn")
    def test_search_code_not_found(self, mock_get_conn):
        """Test searching exam by code - no results"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_exams_by_code("INVALID-CODE")

        self.assertEqual(len(results), 0)

    @patch("src.services.exams_service.get_conn")
    def test_search_code_case_insensitive(self, mock_get_conn):
        """Test searching exam by code - case insensitive"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_exams_by_code("cs101-mid")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["exam_code"], "CS101-MID")

    def test_search_code_empty_string(self):
        """Test searching with empty code raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.search_exams_by_code("")

        self.assertIn("Search term is required", str(context.exception))


class TestExamSearchByCourse(unittest.TestCase):
    def setUp(self):
        self.service = ExamService()

        self.mock_exams = [
            {
                "id": 1,
                "title": "Calculus Midterm",
                "exam_code": "MATH101-MID",
                "course": 1,
                "course_name": "Mathematics",
                "course_code": "MATH101",
                "date": "2025-12-15",
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "duration": 120,
                "status": "scheduled",
            },
            {
                "id": 2,
                "title": "Programming Final",
                "exam_code": "CS101-FIN",
                "course": 2,
                "course_name": "Computer Science",
                "course_code": "CS101",
                "date": "2025-12-20",
                "start_time": time(14, 0),
                "end_time": time(16, 0),
                "duration": 120,
                "status": "scheduled",
            },
        ]

    @patch("src.services.exams_service.get_conn")
    def test_search_student_course_found(self, mock_get_conn):
        """Test searching student's exams by course - result found"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_student_exams_by_course(1, "Mathematics")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["course_name"], "Mathematics")

    @patch("src.services.exams_service.get_conn")
    def test_search_student_course_not_found(self, mock_get_conn):
        """Test searching student's exams by course - no results"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_student_exams_by_course(1, "Physics")

        self.assertEqual(len(results), 0)

    @patch("src.services.exams_service.get_conn")
    def test_search_student_course_case_insensitive(self, mock_get_conn):
        """Test searching student's exams by course - case insensitive"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_student_exams_by_course(1, "MATHEMATICS")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["course_name"], "Mathematics")

    @patch("src.services.exams_service.get_conn")
    def test_search_student_course_partial_match(self, mock_get_conn):
        """Test searching student's exams by partial course name"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[1]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.search_student_exams_by_course(1, "Computer")

        self.assertEqual(len(results), 1)

    def test_search_student_course_empty_string(self):
        """Test searching with empty course name raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.search_student_exams_by_course(1, "")

        self.assertIn("Course name is required", str(context.exception))

    def test_search_student_course_invalid_student_id(self):
        """Test searching with invalid student ID raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.search_student_exams_by_course(0, "Mathematics")

        self.assertIn("Valid student ID is required", str(context.exception))


class TestExamFilterByStatus(unittest.TestCase):
    def setUp(self):
        self.service = ExamService()

        self.mock_exams = [
            {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "CS101-MID",
                "course": 1,
                "date": "2025-12-15",
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "duration": 120,
                "status": "scheduled",
            },
            {
                "id": 2,
                "title": "Final Exam",
                "exam_code": "CS101-FIN",
                "course": 1,
                "date": "2025-12-20",
                "start_time": time(14, 0),
                "end_time": time(16, 0),
                "duration": 120,
                "status": "completed",
            },
            {
                "id": 3,
                "title": "Quiz",
                "exam_code": "MATH101-QZ",
                "course": 2,
                "date": "2025-12-10",
                "start_time": time(10, 30),
                "end_time": time(11, 30),
                "duration": 60,
                "status": "cancelled",
            },
        ]

    @patch("src.services.exams_service.get_conn")
    def test_filter_status_scheduled(self, mock_get_conn):
        """Test filtering exams by scheduled status"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_exams_by_status("scheduled")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "scheduled")

    @patch("src.services.exams_service.get_conn")
    def test_filter_status_completed(self, mock_get_conn):
        """Test filtering exams by completed status"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[1]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_exams_by_status("completed")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "completed")

    @patch("src.services.exams_service.get_conn")
    def test_filter_status_cancelled(self, mock_get_conn):
        """Test filtering exams by cancelled status"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[2]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_exams_by_status("cancelled")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "cancelled")

    @patch("src.services.exams_service.get_conn")
    def test_filter_status_case_insensitive(self, mock_get_conn):
        """Test filtering exams by status - case insensitive"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_exams_by_status("SCHEDULED")

        self.assertEqual(len(results), 1)

    @patch("src.services.exams_service.get_conn")
    def test_filter_status_no_results(self, mock_get_conn):
        """Test filtering exams by status with no results"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_exams_by_status("scheduled")

        self.assertEqual(len(results), 0)

    def test_filter_status_invalid_status(self):
        """Test filtering with invalid status raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.filter_exams_by_status("invalid")

        self.assertIn("Status must be one of", str(context.exception))

    def test_filter_status_empty_string(self):
        """Test filtering with empty status raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.filter_exams_by_status("")

        self.assertIn("Status must be one of", str(context.exception))


class TestExamFilterStudentByStatus(unittest.TestCase):
    def setUp(self):
        self.service = ExamService()

        self.mock_exams = [
            {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "CS101-MID",
                "course": 1,
                "course_name": "Computer Science",
                "course_code": "CS101",
                "date": "2025-12-15",
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "duration": 120,
                "status": "scheduled",
            },
            {
                "id": 2,
                "title": "Final Exam",
                "exam_code": "MATH101-FIN",
                "course": 2,
                "course_name": "Mathematics",
                "course_code": "MATH101",
                "date": "2025-12-20",
                "start_time": time(14, 0),
                "end_time": time(16, 0),
                "duration": 120,
                "status": "completed",
            },
        ]

    @patch("src.services.exams_service.get_conn")
    def test_filter_student_status_scheduled(self, mock_get_conn):
        """Test filtering student's exams by scheduled status"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[0]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_student_exams_by_status(1, "scheduled")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "scheduled")

    @patch("src.services.exams_service.get_conn")
    def test_filter_student_status_completed(self, mock_get_conn):
        """Test filtering student's exams by completed status"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [self.mock_exams[1]]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_student_exams_by_status(1, "completed")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "completed")

    @patch("src.services.exams_service.get_conn")
    def test_filter_student_status_no_results(self, mock_get_conn):
        """Test filtering student's exams by status with no results"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        results = self.service.filter_student_exams_by_status(1, "scheduled")

        self.assertEqual(len(results), 0)

    def test_filter_student_status_invalid_student_id(self):
        """Test filtering with invalid student ID raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.filter_student_exams_by_status(0, "scheduled")

        self.assertIn("Valid student ID is required", str(context.exception))

    def test_filter_student_status_invalid_status(self):
        """Test filtering with invalid status raises error"""
        with self.assertRaises(ValueError) as context:
            self.service.filter_student_exams_by_status(1, "invalid")

        self.assertIn("Status must be one of", str(context.exception))


if __name__ == "__main__":
    unittest.main()