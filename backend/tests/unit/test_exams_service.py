import pytest
from src.services.exams_service import ExamService


# ------------------------------------------------------------------
# Fake Cursor for mocking psycopg cursor behavior
# ------------------------------------------------------------------
class FakeCursor:
    def __init__(self):
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def execute(self, sql, params):
        self.params = params

    def fetchone(self):
        return {
            "id": 1,
            "title": self.params[0],
            "start_time": self.params[1],
            "end_time": self.params[2],
        }


# ------------------------------------------------------------------
# Fake Connection for mocking psycopg connection
# ------------------------------------------------------------------
class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def cursor(self, row_factory=None):
        # psycopg provides row_factory argument, so FakeConn should accept it
        return FakeCursor()


# Factory function for monkeypatching
def fake_get_conn():
    return FakeConn()


# ------------------------------------------------------------------
# Unit Tests
# ------------------------------------------------------------------
def test_add_exam(monkeypatch):
    # Replace real DB connection with FakeConn
    monkeypatch.setattr("src.services.exams_service.get_conn", lambda: fake_get_conn())

    service = ExamService()

    exam = service.add_exam("Midterm", "2025-01-01", "2025-01-01")

    assert exam["title"] == "Midterm"
    assert exam["id"] == 1


def test_add_exam_missing_title():
    service = ExamService()

    with pytest.raises(ValueError):
        service.add_exam("", "2025-01-01", "2025-01-01")
