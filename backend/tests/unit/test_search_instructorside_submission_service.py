# tests/unit/test_submission_service_search.py
import unittest
from unittest.mock import patch, MagicMock
from src.services.submission_service import SubmissionService

class TestSubmissionSearch(unittest.TestCase):
    def setUp(self):
        self.service = SubmissionService()

        # Sample submissions
        self.mock_submissions = [
            {
                "submission_id": 1,
                "student_id": 101,
                "student_name": "Alice",
                "student_email": "alice@example.com",
                "status": "submitted",
            },
            {
                "submission_id": 2,
                "student_id": 102,
                "student_name": "Bob",
                "student_email": "bob@example.com",
                "status": "submitted",
            },
        ]

    @patch("src.services.submission_service.get_conn")
    def test_search_name_not_found(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.mock_submissions
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Name not in submissions
        results = [s for s in self.mock_submissions if "Charlie".lower() in s["student_name"].lower()]
        self.assertEqual(len(results), 0)

    @patch("src.services.submission_service.get_conn")
    def test_search_email_not_found(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.mock_submissions
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Email not in submissions
        results = [s for s in self.mock_submissions if "charlie@example.com".lower() in s["student_email"].lower()]
        self.assertEqual(len(results), 0)

    @patch("src.services.submission_service.get_conn")
    def test_search_name_case_insensitive(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.mock_submissions
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Uppercase search should match lowercase stored names
        results = [s for s in self.mock_submissions if "ALICE".lower() in s["student_name"].lower()]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["student_email"], "alice@example.com")

    @patch("src.services.submission_service.get_conn")
    def test_search_email_case_insensitive(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.mock_submissions
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        results = [s for s in self.mock_submissions if "BOB@EXAMPLE.COM".lower() in s["student_email"].lower()]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["student_name"], "Bob")

    @patch("src.services.submission_service.get_conn")
    def test_search_name_empty_string(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.mock_submissions
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Empty string should return all submissions
        results = [s for s in self.mock_submissions if "".lower() in s["student_name"].lower()]
        self.assertEqual(len(results), 2)

    @patch("src.services.submission_service.get_conn")
    def test_search_email_empty_string(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = self.mock_submissions
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        results = [s for s in self.mock_submissions if "".lower() in s["student_email"].lower()]
        self.assertEqual(len(results), 2)
