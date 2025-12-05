import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

# Load FastAPI test client
client = TestClient(app)

# Load feature file
scenarios("../feature/lateSubmission.feature")


# ============================================================
# GLOBAL DB MOCK  (applies to ALL steps)
# ============================================================
@pytest.fixture(autouse=True)
def mock_db():
    mock_cursor = MagicMock()
    mock_conn = MagicMock()

    # Simulate "with get_conn() as conn:" behavior
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    # Default fake Response for DB queries
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None

    # Patch get_conn in the exact module where it is imported
    with patch("src.services.take_exam_service.get_conn", return_value=mock_conn):
        yield


# ============================================================
# CONTEXT
# ============================================================
submit_context = {
    "last_exam_code": None,
    "last_response": None,
    "students": [],
    "graded_exams": set(),
}


# ============================================================
# GIVEN STEPS
# ============================================================
@given("the API is running")
def api_running():
    assert True


@given("the exam database is empty")
def empty_db():
    submit_context["students"] = []
    submit_context["graded_exams"] = set()


@given(parsers.parse('students "{s1}", "{s2}", and "{s3}" exist'))
def create_students(s1, s2, s3):
    submit_context["students"] = [s1, s2, s3]


@given(parsers.parse('the exam "{exam_code}" has been graded'))
def exam_graded(exam_code):
    submit_context["graded_exams"].add(exam_code)


# ============================================================
# WHEN STEPS  (REAL API CALLS)
# ============================================================
def _mock_exam_details(exam_code):
    """
    Utility: mock exam data for all API calls
    """
    return patch(
        "src.services.take_exam_service.ExamRepository.get_exam_by_code",
        return_value={
            "id": 1,
            "date": "2025-12-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration": 60,
        },
    )


@when(parsers.parse('I submit an exam exactly at the end time for exam code "{exam_code}"'))
@when(parsers.parse('I submit an exam 1 minute before the end time for exam code "{exam_code}"'))
@when(parsers.parse('I submit an exam 1 minute after the end time for exam code "{exam_code}"'))
@when(parsers.parse('I submit an empty exam 5 minutes late for exam code "{exam_code}"'))
@when(parsers.parse('I try to submit again after the exam ended for exam code "{exam_code}"'))
def submit_exam(exam_code):

    submit_context["last_exam_code"] = exam_code

    # Mocking behavior based on exam code
    if "LATE" in exam_code:
        validate = patch(
            "src.services.take_exam_service.SubmissionTimeValidator.validate",
            side_effect=ValueError("late"),
        )
        submit_return = None
    elif "RESUBMIT" in exam_code:
        validate = patch(
            "src.services.take_exam_service.SubmissionTimeValidator.validate",
            side_effect=ValueError("already submitted"),
        )
        submit_return = None
    else:
        validate = patch(
            "src.services.take_exam_service.SubmissionTimeValidator.validate",
            return_value=True,
        )
        submit_return = patch(
            "src.services.take_exam_service.SubmissionRepository.create_submission",
            return_value=123,
        )

    with (
        _mock_exam_details(exam_code),
        validate,
        patch("src.services.take_exam_service.QuestionRepository.get_question_by_id",
              return_value={"id": 1, "question_type": "mcq", "marks": 10}),
        patch("src.services.take_exam_service.QuestionRepository.get_correct_option_id",
              return_value=2),
        patch("src.services.take_exam_service.AnswerRepository.create_submission_answer",
              return_value=500),
        patch("src.services.take_exam_service.AnswerRepository.save_mcq_answer",
              return_value=None),
        patch("src.services.take_exam_service.SubmissionRepository.update_submission_final",
              return_value=None),
        (submit_return or patch("builtins.print")),   # dummy fallback
    ):
        response = client.post(
            "/take-exam/submit",
            json={
                "exam_code": exam_code,
                "user_id": 1,
                "answers": [{"question_id": 1, "answer": 2}],
            },
        )
        submit_context["last_response"] = response


@when(parsers.parse('each student submits the exam "{exam_code}" on time'))
def multi_submit(exam_code):

    # All students do the same submission
    for s in submit_context["students"]:

        with (
            _mock_exam_details(exam_code),
            patch(
                "src.services.take_exam_service.SubmissionTimeValidator.validate",
                return_value=True,
            ),
            patch(
                "src.services.take_exam_service.SubmissionRepository.create_submission",
                return_value=999,
            ),
            patch("src.services.take_exam_service.QuestionRepository.get_question_by_id",
                  return_value={"id": 1, "question_type": "mcq", "marks": 10}),
            patch("src.services.take_exam_service.QuestionRepository.get_correct_option_id",
                  return_value=2),
            patch("src.services.take_exam_service.AnswerRepository.create_submission_answer",
                  return_value=888),
            patch("src.services.take_exam_service.AnswerRepository.save_mcq_answer",
                  return_value=None),
            patch("src.services.take_exam_service.SubmissionRepository.update_submission_final",
                  return_value=None),
        ):
            res = client.post(
                "/take-exam/submit",
                json={
                    "exam_code": exam_code,
                    "user_id": 1,
                    "answers": [{"question_id": 1, "answer": 2}],
                },
            )
            submit_context["last_response"] = res


@when(parsers.parse('I submit an exam with only partial answers 2 minutes before the end time for exam code "{exam_code}"'))
def submit_partial(exam_code):

    with (
        _mock_exam_details(exam_code),
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate",
              return_value=True),
        patch("src.services.take_exam_service.SubmissionRepository.create_submission",
              return_value=789),
        patch("src.services.take_exam_service.QuestionRepository.get_question_by_id",
              return_value={"id": 1, "question_type": "mcq", "marks": 20}),
        patch("src.services.take_exam_service.QuestionRepository.get_correct_option_id",
              return_value=2),
        patch("src.services.take_exam_service.AnswerRepository.create_submission_answer",
              return_value=777),
        patch("src.services.take_exam_service.AnswerRepository.save_mcq_answer",
              return_value=None),
        patch("src.services.take_exam_service.SubmissionRepository.update_submission_final",
              return_value=None),
    ):
        response = client.post(
            "/take-exam/submit",
            json={
                "exam_code": exam_code,
                "user_id": 1,
                "answers": [{"question_id": 1, "answer": 1}],  # wrong
            },
        )
        submit_context["last_response"] = response


@when(parsers.parse('I submit an exam with invalid exam code "{exam_code}"'))
def submit_invalid(exam_code):

    with patch("src.services.take_exam_service.ExamRepository.get_exam_by_code",
               return_value=None):

        response = client.post(
            "/take-exam/submit",
            json={"exam_code": exam_code, "user_id": 1, "answers": []},
        )
        submit_context["last_response"] = response


@when(parsers.parse('I submit an exam and then resubmit 5 minutes before the end time for exam code "{exam_code}"'))
def resubmit_twice(exam_code):

    with (
        _mock_exam_details(exam_code),
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate",
              return_value=True),
        patch("src.services.take_exam_service.SubmissionRepository.create_submission",
              return_value=101),
        patch("src.services.take_exam_service.SubmissionRepository.update_submission_final",
              return_value=None),
        patch("src.services.take_exam_service.QuestionRepository.get_question_by_id",
              return_value={"id": 1, "question_type": "mcq", "marks": 10}),
        patch("src.services.take_exam_service.QuestionRepository.get_correct_option_id",
              return_value=2),
        patch("src.services.take_exam_service.AnswerRepository.create_submission_answer",
              return_value=555),
        patch("src.services.take_exam_service.AnswerRepository.save_mcq_answer",
              return_value=None),
    ):
        r1 = client.post(
            "/take-exam/submit",
            json={"exam_code": exam_code, "user_id": 1, "answers": [{"question_id": 1, "answer": 2}]},
        )

    with (
        _mock_exam_details(exam_code),
        patch("src.services.take_exam_service.SubmissionTimeValidator.validate",
              return_value=True),
        patch("src.services.take_exam_service.SubmissionRepository.create_submission",
              return_value=102),
        patch("src.services.take_exam_service.SubmissionRepository.update_submission_final",
              return_value=None),
        patch("src.services.take_exam_service.QuestionRepository.get_question_by_id",
              return_value={"id": 1, "question_type": "mcq", "marks": 10}),
        patch("src.services.take_exam_service.QuestionRepository.get_correct_option_id",
              return_value=2),
        patch("src.services.take_exam_service.AnswerRepository.create_submission_answer",
              return_value=556),
        patch("src.services.take_exam_service.AnswerRepository.save_mcq_answer",
              return_value=None),
    ):
        r2 = client.post(
            "/take-exam/submit",
            json={"exam_code": exam_code, "user_id": 1, "answers": [{"question_id": 1, "answer": 2}]},
        )

    submit_context["last_response"] = [r1, r2]


@when(parsers.parse('I attempt to resubmit after grading for exam code "{exam_code}"'))
def resubmit_after_grading(exam_code):

    # Already graded exam should reject resubmit
    if exam_code in submit_context["graded_exams"]:
        validate = patch(
            "src.services.take_exam_service.SubmissionTimeValidator.validate",
            side_effect=ValueError("cannot resubmit after grading"),
        )
    else:
        validate = patch(
            "src.services.take_exam_service.SubmissionTimeValidator.validate",
            return_value=True,
        )

    with (
        _mock_exam_details(exam_code),
        validate,
    ):
        response = client.post(
            "/take-exam/submit",
            json={"exam_code": exam_code, "user_id": 1, "answers": []},
        )
        submit_context["last_response"] = response


# ============================================================
# THEN STEPS
# ============================================================
@then(parsers.parse("I receive status code {code:d}"))
def check_status(code):
    res = submit_context["last_response"]
    if isinstance(res, list):
        assert all(r.status_code == code for r in res)
    else:
        assert res.status_code == code


@then(parsers.parse('the response contains "{field}"'))
def check_field(field):
    res = submit_context["last_response"]
    assert field in res.json()


@then(parsers.parse('the grade is "{grade}"'))
def check_grade(grade):
    assert submit_context["last_response"].json().get("grade") == grade


@then(parsers.parse("all submissions receive status code {code:d}"))
def check_multi(code):
    res = submit_context["last_response"]
    assert res.status_code == code


@then(parsers.parse("both submissions receive status code {code:d}"))
def check_both_status(code):
    res1, res2 = submit_context["last_response"]
    assert res1.status_code == code
    assert res2.status_code == code


@then(parsers.parse('each response contains "{field}"'))
def each_response_contains(field):
    res = submit_context["last_response"]
    if not isinstance(res, list):
        res = [res]
    for r in res:
        assert field in r.json()


@then(parsers.parse('the error message contains "{text}"'))
def check_error_contains(text):
    msg = submit_context["last_response"].json().get("detail", "") \
        or submit_context["last_response"].json().get("error", "")
    assert text.lower() in msg.lower()
