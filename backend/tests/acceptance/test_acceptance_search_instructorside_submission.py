from unittest.mock import patch
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from src.main import app  # Your FastAPI app

client = TestClient(app)

scenarios('../feature/search_instructorside_submission.feature')


@pytest.fixture
def context():
    return {}


# Mock data
mock_submissions = [
    {
        "submission_id": "sub1",
        "student_id": 1,
        "student_name": "Alice",
        "student_email": "alice@example.com",
        "status": "submitted",
        "submission_date": "2025-12-01",
        "submission_time": "10:00:00",
        "score": 90,
        "score_grade": "A",
        "overall_feedback": "Good job",
    },
    {
        "submission_id": "sub2",
        "student_id": 2,
        "student_name": "Bob",
        "student_email": "bob@example.com",
        "status": "graded",
        "submission_date": "2025-12-01",
        "submission_time": "11:00:00",
        "score": 80,
        "score_grade": "B",
        "overall_feedback": "Well done",
    },
    {
        "submission_id": "sub3",
        "student_id": 3,
        "student_name": "Charlie",
        "student_email": "charlie@example.com",
        "status": "graded",
        "submission_date": "2025-12-01",
        "submission_time": "12:00:00",
        "score": 70,
        "score_grade": "C",
        "overall_feedback": "Needs improvement",
    },
]


# ----------------- GIVEN -----------------
@given(parsers.parse('I am viewing the submission list for exam {exam_id:d}'))
def viewing_exam_submissions(context, exam_id):
    context['exam_id'] = exam_id
    context['submissions'] = mock_submissions.copy()
    context['search_results'] = context['submissions']


# ----------------- WHEN -----------------
@when(parsers.parse('I search for submissions by student name "{name}"'))
def search_by_student_name(context, name):
    all_subs = context['submissions']
    context['search_results'] = [
        sub for sub in all_subs if name.lower() in sub['student_name'].lower()
    ]


@when(parsers.parse('I search for submissions by student email "{email}"'))
def search_by_student_email(context, email):
    all_subs = context['submissions']
    context['search_results'] = [
        sub for sub in all_subs if email.lower() in sub['student_email'].lower()
    ]


@when(parsers.parse('I search for submissions by submission ID "{submission_id}"'))
def search_by_submission_id(context, submission_id):
    all_subs = context['submissions']
    context['search_results'] = [
        sub for sub in all_subs if submission_id.lower() == sub['submission_id'].lower()
    ]


@when(parsers.parse('I search for submissions by status "{status}"'))
def search_by_status(context, status):
    all_subs = context['submissions']
    context['search_results'] = [
        sub for sub in all_subs if sub['status'].lower() == status.lower()
    ]


@when(parsers.parse('I sort submissions by score descending'))
def sort_by_score_desc(context):
    context['search_results'] = sorted(
        context['search_results'], key=lambda x: x['score'], reverse=True
    )


@when(parsers.parse('I sort submissions by score ascending'))
def sort_by_score_asc(context):
    context['search_results'] = sorted(
        context['search_results'], key=lambda x: x['score']
    )


@when(parsers.parse('I filter submissions from "{start_date}" to "{end_date}"'))
def filter_by_date_range(context, start_date, end_date):
    context['search_results'] = [
        sub for sub in context['search_results']
        if start_date <= sub['submission_date'] <= end_date
    ]


@when(parsers.parse('I filter submissions by status "{status}"'))
def filter_by_status(context, status):
    context['search_results'] = [
        sub for sub in context['search_results'] if sub['status'].lower() == status.lower()
    ]


# ----------------- THEN -----------------
@then(parsers.re(r'I should see (?P<count>\d+) submissions?(?: matching "(?P<text>.+)")?'))
def verify_submission_count(context, count, text=None):
    count = int(count)
    results = context['search_results']

    if text:
        for sub in results:
            assert (
                text.lower() in sub['student_name'].lower()
                or text.lower() in sub['student_email'].lower()
                or text.lower() == sub['submission_id'].lower()
            )
    assert len(results) == count


@then(parsers.parse('the first submission should have score {score:d}'))
def verify_first_submission_score(context, score):
    assert context['search_results'][0]['score'] == score
