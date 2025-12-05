import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

from src.services.take_exam_service import (
    ExamRepository,
    QuestionRepository,
    SubmissionRepository,
    AnswerRepository,
    MCQAnswerGrader,
    AnswerProcessor,
    TakeExamService,
    GradeCalculator,
    TimeConverter,
    SubmissionTimeValidator,
)


# -------------------------------------------------------------------
# Fixtures for mock DB cursor + connection
# -------------------------------------------------------------------

@pytest.fixture
def mock_cursor():
    cur = MagicMock()
    return cur


@pytest.fixture
def mock_conn(mock_cursor):
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = mock_cursor
    conn.cursor.return_value.__exit__.return_value = False
    return conn


# Patch get_conn() to return mock connection
@pytest.fixture
def mock_db(mock_conn):
    with patch("src.services.take_exam_service.get_conn", return_value=mock_conn):
        yield


# -------------------------------------------------------------------
# Test ExamRepository
# -------------------------------------------------------------------

def test_exam_repository_get_exam_by_code(mock_cursor):
    repo = ExamRepository()

    mock_cursor.fetchone.return_value = {"id": 1, "date": "2025-12-01"}

    result = repo.get_exam_by_code(mock_cursor, "EX001")
    mock_cursor.execute.assert_called_once()

    assert result["id"] == 1


def test_exam_repository_get_exam_id_success(mock_cursor):
    repo = ExamRepository()

    mock_cursor.fetchone.return_value = {"id": 9}
    result = repo.get_exam_id(mock_cursor, "EXB01")

    assert result == 9


def test_exam_repository_get_exam_id_not_found(mock_cursor):
    repo = ExamRepository()

    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError):
        repo.get_exam_id(mock_cursor, "X000")


# -------------------------------------------------------------------
# Test QuestionRepository
# -------------------------------------------------------------------

def test_question_repository_get_question_by_id(mock_cursor):
    repo = QuestionRepository()
    mock_cursor.fetchone.return_value = {"id": 3, "marks": 5}

    q = repo.get_question_by_id(mock_cursor, 3, 20)
    assert q["id"] == 3


def test_question_repository_correct_option_id(mock_cursor):
    repo = QuestionRepository()
    mock_cursor.fetchone.return_value = {"id": 88}

    result = repo.get_correct_option_id(mock_cursor, 3)
    assert result == 88


def test_question_repository_options_list(mock_cursor):
    repo = QuestionRepository()

    # fake question list
    mock_cursor.fetchall.side_effect = [
        [{"id": 1, "question_text": "Q1", "question_type": "mcq", "marks": 5}],
        [{"id": 10, "option_text": "A"}, {"id": 11, "option_text": "B"}]
    ]

    res = repo.get_questions_with_options(mock_cursor, 100)
    assert len(res) == 1
    assert len(res[0]["options"]) == 2


# -------------------------------------------------------------------
# Test SubmissionRepository
# -------------------------------------------------------------------

def test_submission_repo_check_exists(mock_cursor):
    repo = SubmissionRepository()
    mock_cursor.fetchone.return_value = {"id": 5}
    assert repo.check_submission_exists(mock_cursor, 10, 1) is True


def test_submission_repo_create(mock_cursor):
    repo = SubmissionRepository()
    mock_cursor.fetchone.return_value = {"id": 99}

    result = repo.create_submission(mock_cursor, 30, 7, datetime.now())
    assert result == 99


def test_submission_repo_update_final(mock_cursor):
    repo = SubmissionRepository()
    repo.update_submission_final(mock_cursor, 5, 20, "graded", "A")

    mock_cursor.execute.assert_called()


# -------------------------------------------------------------------
# Test AnswerRepository
# -------------------------------------------------------------------

def test_answer_repo_create_answer(mock_cursor):
    repo = AnswerRepository()
    mock_cursor.fetchone.return_value = {"id": 101}

    ans_id = repo.create_submission_answer(
        mock_cursor, 1, 9, 2, 5, "Correct"
    )
    assert ans_id == 101


def test_answer_repo_save_mcq(mock_cursor):
    repo = AnswerRepository()
    repo.save_mcq_answer(mock_cursor, 20, 99)

    mock_cursor.execute.assert_called()


def test_answer_repo_save_essay(mock_cursor):
    repo = AnswerRepository()
    repo.save_essay_answer(mock_cursor, 20, "my essay")

    mock_cursor.execute.assert_called()


# -------------------------------------------------------------------
# Test MCQAnswerGrader
# -------------------------------------------------------------------

def test_mcq_grader_correct():
    grader = MCQAnswerGrader()
    result = grader.grade(3, 3, 5)

    assert result["score"] == 5
    assert result["is_correct"] is True


def test_mcq_grader_wrong():
    grader = MCQAnswerGrader()
    result = grader.grade(1, 3, 5)

    assert result["score"] == 0
    assert result["is_correct"] is False


# -------------------------------------------------------------------
# Test GradeCalculator
# -------------------------------------------------------------------

@pytest.mark.parametrize("score,max_score,expected", [
    (95, 100, "A+"),
    (85, 100, "A"),
    (75, 100, "B"),
    (65, 100, "C"),
    (55, 100, "D"),
    (20, 100, "F"),
    (10, 0, "N/A"),
])
def test_grade_calculator(score, max_score, expected):
    calc = GradeCalculator()
    assert calc.calculate(score, max_score) == expected


# -------------------------------------------------------------------
# Test AnswerProcessor
# -------------------------------------------------------------------

def test_answer_processor_mcq_path(mock_cursor):
    question_repo = MagicMock()
    answer_repo = MagicMock()
    mcq_grader = MCQAnswerGrader()

    question_repo.get_correct_option_id.return_value = 5
    answer_repo.create_submission_answer.return_value = 111

    processor = AnswerProcessor(question_repo, answer_repo, mcq_grader)

    result = processor.process_mcq(mock_cursor, 10, 1, 5, 4)

    assert result["is_correct"] is True
    assert result["score"] == 4
    answer_repo.save_mcq_answer.assert_called_once()


def test_answer_processor_essay_path(mock_cursor):
    question_repo = MagicMock()
    answer_repo = MagicMock()
    grader = MCQAnswerGrader()

    processor = AnswerProcessor(question_repo, answer_repo, grader)
    answer_repo.create_submission_answer.return_value = 77

    r = processor.process_essay(mock_cursor, 10, 1, "Test Essay", 6)

    assert r["status"] == "pending"
    answer_repo.save_essay_answer.assert_called_once()


# -------------------------------------------------------------------
# Test TakeExamService.submit_exam (full flow with mocks)
# -------------------------------------------------------------------

def test_take_exam_service_submit_exam_full(mock_db, mock_cursor):
    service = TakeExamService()

    # ------- mock exam repo ----------
    service.exam_repo.get_exam_by_code = MagicMock(return_value={
        "id": 9,
        "date": "2025-12-01",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
    })

    # ------- mock time ----------
    fixed_now = datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone(timedelta(hours=8)))
    service.time_converter.get_current_time = MagicMock(return_value=fixed_now)

    # ------- mock create submission ----------
    service.submission_repo.create_submission = MagicMock(return_value=1001)

    # ------- mock question repo ----------
    service.question_repo.get_question_by_id = MagicMock(
        side_effect=[
            {"question_type": "mcq", "marks": 5},
            {"question_type": "essay", "marks": 10},
        ]
    )

    service.question_repo.get_correct_option_id = MagicMock(return_value=3)

    # ------- mock answer repo ----------
    service.answer_repo.create_submission_answer = MagicMock(return_value=5001)
    service.answer_repo.save_mcq_answer = MagicMock()
    service.answer_repo.save_essay_answer = MagicMock()

    # ------- mock final update ----------
    service.submission_repo.update_submission_final = MagicMock()

    # fake request answers
    class FakeAns:
        def __init__(self, qid, ans):
            self.question_id = qid
            self.answer = ans

    answers = [FakeAns(1, 3), FakeAns(2, "My essay")]

    result = service.submit_exam("EX004", 99, answers)

    assert result["submission_id"] == 1001
    assert result["status"] == "pending"
    assert result["total_score"] == 5
    assert result["max_score"] == 15
    assert len(result["results"]) == 2

    service.submission_repo.update_submission_final.assert_called_once()
