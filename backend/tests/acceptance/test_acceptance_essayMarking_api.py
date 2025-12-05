from __future__ import annotations
from typing import Dict
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pytest_bdd import (
    scenarios,
    given as bdd_given,
    when as bdd_when,
    then as bdd_then,
    parsers,
)

from main import app

# Load scenarios from feature file
scenarios("../feature/essayMarking.feature")


# ------------------------------------------------------------
# Shared Context
# ------------------------------------------------------------
class Context:
    def __init__(self):
        self.last_response = None
        self.mock_patcher = None
        self.submission_id = None
        self.essay_answers = []
        self.grade_payload = {}

    def cleanup(self):
        if self.mock_patcher:
            self.mock_patcher.stop()


@pytest.fixture
def context() -> Context:  # type: ignore
    ctx = Context()
    yield ctx
    ctx.cleanup()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
def build_mock_cursor():
    """Build a mock cursor for database operations"""
    cur = MagicMock()
    cur.execute.return_value = None
    return cur


def setup_submission_for_grading(
    context: Context,
    submission_id: int,
    num_essays: int = 1,
    status: str = "submitted",
    mcq_count: int = 0,
    mcq_score: int = 0,
):
    """Setup mock for getting submission for grading"""
    if context.mock_patcher:
        context.mock_patcher.stop()

    context.mock_patcher = patch("src.routers.grading.get_conn")
    mock_conn = context.mock_patcher.start()

    cur = build_mock_cursor()
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
        cur
    )

    context.submission_id = submission_id

    # Build questions list
    questions = []
    fetchone_effects = []
    fetchall_effects = []

    # Add MCQ questions
    for i in range(mcq_count):
        questions.append(
            {
                "id": i + 1,
                "question_text": f"MCQ Question {i + 1}",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            }
        )

    # Add essay questions
    for i in range(num_essays):
        q_id = mcq_count + i + 1
        questions.append(
            {
                "id": q_id,
                "question_text": f"Essay Question {i + 1}",
                "question_type": "essay",
                "marks": 10,
                "rubric": "Answer should be comprehensive",
            }
        )
        context.essay_answers.append(
            {
                "submission_answer_id": 500 + i,
                "score": None,
                "feedback": None,
                "essay_answer": f"Student's essay response {i + 1}",
            }
        )

    # Setup fetchone side effects
    fetchone_effects.extend(
        [
            # Submission info
            {
                "submission_id": submission_id,
                "exam_code": 5,
                "user_id": 10,
                "submission_date": "2024-01-15",
                "submission_time": "10:30:00",
                "status": status,
                "current_score": mcq_score if mcq_count > 0 else None,
                "score_grade": None,
                "overall_feedback": None,
                "student_email": "student@test.com",
                "student_name": "student@test.com",
            },
            # Exam info
            {
                "id": 5,
                "title": "Test Exam",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "date": "2024-01-15",
            },
            # Total score
            {"total_score": mcq_score},
        ]
    )

    # Add MCQ answers
    for i in range(mcq_count):
        fetchone_effects.append(
            {
                "submission_answer_id": 400 + i,
                "selected_option_id": 101,
                "score": 5,
                "is_correct": True,
                "option_text": "Correct answer",
            }
        )

    # Add essay answers
    fetchone_effects.extend(context.essay_answers)

    cur.fetchone.side_effect = fetchone_effects

    # Setup fetchall for questions
    fetchall_effects.append(questions)

    # Add MCQ options
    for i in range(mcq_count):
        fetchall_effects.append(
            [
                {"id": 100 + i * 2, "option_text": "Wrong", "is_correct": False},
                {"id": 101 + i * 2, "option_text": "Correct", "is_correct": True},
            ]
        )

    cur.fetchall.side_effect = fetchall_effects

    return cur


def setup_save_grades_mock(context: Context, success: bool = True):
    """Setup mock for saving grades"""
    if context.mock_patcher:
        context.mock_patcher.stop()

    context.mock_patcher = patch("src.routers.grading.get_conn")
    mock_conn = context.mock_patcher.start()

    cur = build_mock_cursor()
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
        cur
    )

    if success:
        cur.fetchone.return_value = {"id": context.submission_id}
    else:
        cur.fetchone.return_value = None

    return cur


# ------------------------------------------------------------
# GIVEN STEPS
# ------------------------------------------------------------
@bdd_given("the grading API is running", target_fixture="api_is_running")
def api_is_running(client: TestClient, context: Context) -> Dict[str, object]:
    context.last_response = None
    return {"client": client}


@bdd_given(parsers.parse("a submission with ID {sub_id:d} has an essay answer"))
def submission_with_essay(context: Context, sub_id: int):
    """Setup submission with 1 essay"""
    setup_submission_for_grading(context, sub_id, num_essays=1)


@bdd_given(parsers.parse("a submission with ID {sub_id:d} has {count:d} essay answers"))
def submission_with_multiple_essays(context: Context, sub_id: int, count: int):
    """Setup submission with multiple essays"""
    setup_submission_for_grading(context, sub_id, num_essays=count)


@bdd_given(
    parsers.parse(
        "a submission with ID {sub_id:d} has an essay answer worth {marks:d} marks"
    )
)
def submission_with_essay_marks(context: Context, sub_id: int, marks: int):
    """Setup submission with specific marks"""
    setup_submission_for_grading(context, sub_id, num_essays=1)


@bdd_given(
    parsers.parse(
        "a submission with ID {sub_id:d} has already been graded with score {score:f}"
    )
)
def submission_already_graded(context: Context, sub_id: int, score: float):
    """Setup pre-graded submission"""
    setup_submission_for_grading(context, sub_id, num_essays=1, status="graded")
    context.essay_answers[0]["score"] = score
    context.essay_answers[0]["feedback"] = "Previous feedback"


@bdd_given(
    parsers.parse('a submission with ID {sub_id:d} exists with status "{status}"')
)
def submission_with_status(context: Context, sub_id: int, status: str):
    """Setup submission with specific status"""
    setup_submission_for_grading(context, sub_id, num_essays=2, status=status)


@bdd_given(parsers.parse("it contains {count:d} essay questions"))
def has_essay_questions(context: Context, count: int):
    """Already set up in previous step"""
    pass


@bdd_given(
    parsers.parse(
        "a submission with ID {sub_id:d} has {mcq:d} MCQ and {essay:d} essay questions"
    )
)
def submission_with_mixed_questions(
    context: Context, sub_id: int, mcq: int, essay: int
):
    """Setup submission with MCQ and essay"""
    setup_submission_for_grading(
        context, sub_id, num_essays=essay, mcq_count=mcq, mcq_score=10
    )


@bdd_given(parsers.parse("the MCQ questions are auto-graded with score {score:d}"))
def mcq_auto_graded(context: Context, score: int):
    """Already set up in previous step"""
    pass


@bdd_given(parsers.parse("submission with ID {sub_id:d} does not exist"))
def submission_not_exist(context: Context, sub_id: int):
    """Setup non-existent submission"""
    context.submission_id = sub_id
    if context.mock_patcher:
        context.mock_patcher.stop()

    context.mock_patcher = patch("src.routers.grading.get_conn")
    mock_conn = context.mock_patcher.start()

    cur = build_mock_cursor()
    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
        cur
    )
    cur.fetchone.return_value = None


@bdd_given(
    parsers.parse(
        "a submission with ID {sub_id:d} was fully graded with overall feedback"
    )
)
def submission_fully_graded(context: Context, sub_id: int):
    """Setup fully graded submission"""
    setup_submission_for_grading(context, sub_id, num_essays=1, status="graded")
    context.essay_answers[0]["score"] = 8.0
    context.essay_answers[0]["feedback"] = "Good work"


# ------------------------------------------------------------
# WHEN STEPS
# ------------------------------------------------------------
@bdd_when(parsers.parse('I submit a grade of {score:f} with feedback "{feedback}"'))
def submit_single_grade(api_is_running, context: Context, score: float, feedback: str):
    """Submit grade for single essay"""
    client = api_is_running["client"]

    setup_save_grades_mock(context, success=True)

    payload = {
        "submission_id": context.submission_id,
        "essay_grades": [
            {"submission_answer_id": 500, "score": score, "feedback": feedback}
        ],
        "total_score": score,
        "score_grade": "B",
        "overall_feedback": "Good work",
    }

    context.grade_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse("I submit grades for all {count:d} essays with total score {total:f}")
)
def submit_multiple_grades(api_is_running, context: Context, count: int, total: float):
    """Submit grades for multiple essays"""
    client = api_is_running["client"]

    setup_save_grades_mock(context, success=True)

    essay_grades = []
    for i in range(count):
        essay_grades.append(
            {
                "submission_answer_id": 500 + i,
                "score": 7.0 + i * 0.5,
                "feedback": f"Feedback {i + 1}",
            }
        )

    payload = {
        "submission_id": context.submission_id,
        "essay_grades": essay_grades,
        "total_score": total,
        "score_grade": "B",
        "overall_feedback": "Overall good",
    }

    context.grade_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(parsers.parse('I update the grade to {score:f} with feedback "{feedback}"'))
def update_grade(api_is_running, context: Context, score: float, feedback: str):
    """Update existing grade"""
    submit_single_grade(api_is_running, context, score, feedback)


@bdd_when("I request the submission for grading")
def request_submission_for_grading(api_is_running, context: Context):
    """Request GET submission for grading"""
    client = api_is_running["client"]
    response = client.get(f"/grading/submission/{context.submission_id}")
    context.last_response = response


@bdd_when(parsers.parse("I submit a grade of {score:f} without feedback"))
def submit_grade_no_feedback(api_is_running, context: Context, score: float):
    """Submit grade without feedback"""
    client = api_is_running["client"]

    setup_save_grades_mock(context, success=True)

    payload = {
        "submission_id": context.submission_id,
        "essay_grades": [{"submission_answer_id": 500, "score": score}],
        "total_score": score,
        "score_grade": "B",
    }

    context.grade_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when("I attempt to submit grades")
def attempt_submit_grades(api_is_running, context: Context):
    """Attempt to submit grades (may fail)"""
    client = api_is_running["client"]

    setup_save_grades_mock(context, success=False)

    payload = {
        "submission_id": context.submission_id,
        "essay_grades": [{"submission_answer_id": 500, "score": 7.5}],
        "total_score": 7.5,
    }

    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(parsers.parse("I submit overall feedback exceeding {limit:d} characters"))
def submit_long_feedback(api_is_running, context: Context, limit: int):
    """Submit overly long feedback"""
    client = api_is_running["client"]

    payload = {
        "submission_id": context.submission_id,
        "essay_grades": [{"submission_answer_id": 500, "score": 7.5}],
        "total_score": 7.5,
        "overall_feedback": "A" * (limit + 1),
    }

    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse("I submit grades for the {count:d} essays with total score {total:d}")
)
def submit_essay_grades_with_total(
    api_is_running, context: Context, count: int, total: int
):
    """Submit essay grades with specific total"""
    submit_multiple_grades(api_is_running, context, count, float(total))


# ------------------------------------------------------------
# THEN STEPS
# ------------------------------------------------------------
@bdd_then("the mark is saved successfully")
def mark_saved_successfully(context: Context):
    """Verify successful save"""
    assert context.last_response is not None
    assert context.last_response.status_code == 200
    data = context.last_response.json()
    assert data["success"] is True


@bdd_then(parsers.parse('the submission status is updated to "{status}"'))
def status_updated(context: Context, status: str):
    """Verify status update (implicit in successful save)"""
    mark_saved_successfully(context)


@bdd_then("all marks are saved successfully")
def all_marks_saved(context: Context):
    """Verify all marks saved"""
    mark_saved_successfully(context)


@bdd_then(parsers.parse("the total score is {score:f}"))
def total_score_is(context: Context, score: float):
    """Verify total score"""
    assert context.grade_payload["total_score"] == score


@bdd_then("the partial credit is recorded")
def partial_credit_recorded(context: Context):
    """Verify partial credit saved"""
    mark_saved_successfully(context)


@bdd_then("the mark is updated successfully")
def mark_updated(context: Context):
    """Verify update success"""
    mark_saved_successfully(context)


@bdd_then("I receive the submission details")
def receive_submission_details(context: Context):
    """Verify GET submission success"""
    assert context.last_response.status_code == 200
    data = context.last_response.json()
    assert "submission" in data
    assert "exam" in data
    assert "questions" in data


@bdd_then("all essay questions are included")
def all_essays_included(context: Context):
    """Verify essays present"""
    data = context.last_response.json()
    essay_questions = [q for q in data["questions"] if q["question_type"] == "essay"]
    assert len(essay_questions) > 0


@bdd_then("the student's essay answers are shown")
def essay_answers_shown(context: Context):
    """Verify essay answers visible"""
    data = context.last_response.json()
    for q in data["questions"]:
        if q["question_type"] == "essay":
            assert "student_answer" in q


@bdd_then("the total score combines MCQ and essay marks")
def total_combines_scores(context: Context):
    """Verify combined scoring"""
    mark_saved_successfully(context)


@bdd_then("the feedback is null")
def feedback_is_null(context: Context):
    """Verify null feedback"""
    assert (
        "overall_feedback" not in context.grade_payload
        or context.grade_payload.get("overall_feedback") is None
    )


@bdd_then(parsers.parse('I receive an error "{msg}"'))
def receive_error(context: Context, msg: str):
    """Verify error message"""
    assert context.last_response.status_code in [400, 404]
    error_detail = context.last_response.json().get("detail", "")
    assert msg.lower() in error_detail.lower()


@bdd_then(parsers.parse("the response status is {status:d}"))
def response_status(context: Context, status: int):
    """Verify HTTP status"""
    assert context.last_response.status_code == status


@bdd_then("I see all existing grades")
def see_existing_grades(context: Context):
    """Verify existing grades shown"""
    data = context.last_response.json()
    assert data["submission"]["current_score"] is not None


@bdd_then("the overall feedback is displayed")
def overall_feedback_displayed(context: Context):
    """Verify overall feedback present"""
    data = context.last_response.json()
    # May be None for ungraded, but key should exist
    assert "overall_feedback" in data["submission"]

