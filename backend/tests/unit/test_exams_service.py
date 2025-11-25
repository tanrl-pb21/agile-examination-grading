import pytest
from src.services.exams_service import ExamService

# Fake DB for testing
class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def execute(self, sql, params):
        self.params = params
        return self

    def fetchone(self):
        return {
            "id": 1,
            "title": self.params[0],
            "start_time": self.params[1],
            "end_time": self.params[2],
        }


def fake_get_conn():
    return FakeConn()

def fake_get_conn():
    return FakeConn()


def test_add_exam(monkeypatch):
    monkeypatch.setattr("src.services.exams_service.get_conn", lambda: fake_get_conn())
    service = ExamService()

    exam = service.add_exam("Midterm", "2025-01-01", "2025-01-01")

    assert exam["title"] == "Midterm"


def test_add_exam_missing_title():
    service = ExamService()
    with pytest.raises(ValueError):
        service.add_exam("", "2025-01-01", "2025-01-01")
