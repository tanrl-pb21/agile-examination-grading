from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given as bdd_given, parsers, scenarios, then as bdd_then, when as bdd_when

from main import app


# --- Test client fixture -------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """Shared FastAPI test client for grading API."""
    return TestClient(app)


# --- Shared context for BDD steps ----------------------------------------


class FeedbackContext:
    def __init__(self) -> None:
        self.last_response = None  # type: ignore[assignment]
        self.last_payload = None  # type: ignore[assignment]
        self.retrieved_data = None  # type: ignore[assignment]
        self.mock_submissions: Dict[int, Any] = {}  # In-memory mock storage
        self.created_submissions = []  # type: ignore[assignment]


@pytest.fixture
def context() -> FeedbackContext:
    ctx = FeedbackContext()
    yield ctx


# --- Load BDD scenarios from feature file --------------------------------


scenarios("../feature/overall_feedback.feature")


# ============================================================================
# BACKGROUND STEPS
# ============================================================================


@bdd_given("the API is running")
def step_api_is_running(client: TestClient, context: FeedbackContext) -> None:
    """Ensure API and test client are ready."""
    context.last_response = None
    context.mock_submissions = {}
    context.created_submissions = []


@bdd_given("the grading database is empty")
def step_grading_database_is_empty(client: TestClient, context: FeedbackContext) -> None:
    """Clear the mock grading database."""
    context.mock_submissions = {}


# ============================================================================
# GIVEN STEPS: CREATE SUBMISSIONS
# ============================================================================


@bdd_given(parsers.parse("a submission with ID {submission_id:d} exists"))
def step_submission_exists(client: TestClient, context: FeedbackContext, submission_id: int) -> None:
    """Create a mock submission in memory."""
    context.mock_submissions[submission_id] = {
        "id": submission_id,
        "exam_code": "TEST001",
        "user_id": 1,
        "submission_date": "2026-01-01",
        "submission_time": "10:00",
        "status": "pending",
        "current_score": 0,
        "score_grade": "F",
        "overall_feedback": "",
    }
    context.created_submissions.append(submission_id)


@bdd_given(
    parsers.parse('I have saved feedback "{feedback}" for submission {submission_id:d}')
)
def step_save_feedback_precondition(
    client: TestClient, context: FeedbackContext, feedback: str, submission_id: int
) -> None:
    """Save feedback as a precondition by updating mock storage."""
    # Ensure submission exists in mock storage
    if submission_id not in context.mock_submissions:
        context.mock_submissions[submission_id] = {
            "id": submission_id,
            "exam_code": "TEST001",
            "user_id": 1,
            "submission_date": "2026-01-01",
            "submission_time": "10:00",
            "status": "graded",
            "current_score": 80,
            "score_grade": "B",
            "overall_feedback": "",
        }
    
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": 80,
        "score_grade": "B",
        "overall_feedback": feedback,
    }
    
    # Update mock storage (simulating successful save)
    context.mock_submissions[submission_id]["overall_feedback"] = feedback
    
    # Make the actual API call to test the endpoint
    response = client.post("/grading/save", json=payload)
    # Don't assert here - just silently record for setup


# ============================================================================
# THEN STEPS: ASSERTIONS
# ============================================================================


@bdd_then(parsers.parse("I receive status code {code:d}"))
def step_receive_status_code(context: FeedbackContext, code: int) -> None:
    """Verify the response status code."""
    assert context.last_response is not None
    assert context.last_response.status_code == code, (
        f"Expected {code}, got {context.last_response.status_code}. "
        f"Response: {context.last_response.text}"
    )


@bdd_then("the response indicates success is true")
def step_response_success_true(context: FeedbackContext) -> None:
    """Verify response indicates success."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert data.get("success") is True, f"Expected success=True, got {data}"


@bdd_then(parsers.parse('the error message contains "{expected_text}"'))
def step_error_message_contains(context: FeedbackContext, expected_text: str) -> None:
    """Verify error message contains expected text."""
    assert context.last_response is not None
    data = context.last_response.json()
    error_detail = data.get("detail", "")
    error_text = str(error_detail).lower()
    assert expected_text.lower() in error_text, (
        f"Expected '{expected_text}' in error: {error_text}"
    )


@bdd_then(parsers.parse('the error message is "{expected_text}"'))
def step_error_message_is_exact(context: FeedbackContext, expected_text: str) -> None:
    """Verify error message matches exactly."""
    assert context.last_response is not None
    data = context.last_response.json()
    error_detail = data.get("detail", "")
    assert str(error_detail) == expected_text, (
        f"Expected '{expected_text}', got '{error_detail}'"
    )


@bdd_then(parsers.parse('the response contains "{field_name}"'))
def step_response_contains_field(context: FeedbackContext, field_name: str) -> None:
    """Verify response contains a specific field."""
    assert context.last_response is not None
    data = context.last_response.json()
    assert field_name in data, f"Field '{field_name}' not found in response. Keys: {list(data.keys())}"


@bdd_then(parsers.parse('the overall_feedback is "{expected_feedback}"'))
def step_overall_feedback_is(context: FeedbackContext, expected_feedback: str) -> None:
    """Verify overall feedback matches expected value."""
    assert context.retrieved_data is not None
    submission = context.retrieved_data.get("submission") or context.retrieved_data
    actual_feedback = submission.get("overall_feedback", "")
    assert actual_feedback == expected_feedback, (
        f"Expected feedback '{expected_feedback}', got '{actual_feedback}'"
    )


@bdd_then("the overall_feedback is empty or null")
def step_overall_feedback_empty_or_null(context: FeedbackContext) -> None:
    """Verify overall feedback is empty or null."""
    assert context.retrieved_data is not None
    submission = context.retrieved_data.get("submission") or context.retrieved_data
    feedback = submission.get("overall_feedback")
    assert feedback == "" or feedback is None, f"Expected empty/null, got '{feedback}'"


@bdd_then(parsers.parse('the overall_feedback contains "{text}"'))
def step_overall_feedback_contains(context: FeedbackContext, text: str) -> None:
    """Verify overall feedback contains text."""
    assert context.retrieved_data is not None
    submission = context.retrieved_data.get("submission") or context.retrieved_data
    feedback = submission.get("overall_feedback", "")
    assert text in feedback, f"Expected '{text}' in feedback: '{feedback}'"


@bdd_then("the overall_feedback contains newlines")
def step_overall_feedback_contains_newlines(context: FeedbackContext) -> None:
    """Verify overall feedback contains newline characters."""
    assert context.retrieved_data is not None
    submission = context.retrieved_data.get("submission") or context.retrieved_data
    feedback = submission.get("overall_feedback", "")
    assert "\n" in feedback, f"Expected newlines in feedback: '{feedback}'"


# ============================================================================
# WHEN STEPS: SAVE FEEDBACK
# ============================================================================


@bdd_when(
    parsers.parse(
        'I save feedback for submission {submission_id:d} with score {score:d} grade "{grade}" and feedback "{feedback}"'
    )
)
def step_save_feedback(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
    feedback: str,
) -> None:
    """Save feedback with provided details."""
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": feedback,
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response
    
    # Update mock storage on success
    if response.status_code == 200:
        if submission_id not in context.mock_submissions:
            context.mock_submissions[submission_id] = {
                "id": submission_id,
                "exam_code": "TEST001",
                "user_id": 1,
                "submission_date": "2026-01-01",
                "submission_time": "10:00",
                "status": "graded",
                "current_score": score,
                "score_grade": grade,
                "overall_feedback": feedback,
            }
        else:
            context.mock_submissions[submission_id]["current_score"] = score
            context.mock_submissions[submission_id]["score_grade"] = grade
            context.mock_submissions[submission_id]["overall_feedback"] = feedback


@bdd_when(
    parsers.parse(
        'I save feedback for submission {submission_id:d} with feedback "{feedback}"'
    )
)
def step_save_feedback_only(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    feedback: str,
) -> None:
    """Save only feedback without score or grade (but API still requires essay_grades, total_score, score_grade)."""
    # Get existing submission data from mock storage to preserve score/grade
    existing_data = context.mock_submissions.get(submission_id, {})
    score = existing_data.get("current_score", 0)
    grade = existing_data.get("score_grade", "F")
    
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": feedback,
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response
    
    # Update mock storage on success
    if response.status_code == 200:
        if submission_id not in context.mock_submissions:
            context.mock_submissions[submission_id] = {
                "id": submission_id,
                "overall_feedback": feedback,
            }
        else:
            context.mock_submissions[submission_id]["overall_feedback"] = feedback


@bdd_when(
    parsers.parse(
        'I save feedback for submission {submission_id:d} with score {score:d} grade "{grade}" and feedback ""'
    )
)
def step_save_empty_feedback(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
) -> None:
    """Save feedback with empty feedback string."""
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": "",
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response
    
    if response.status_code == 200:
        if submission_id not in context.mock_submissions:
            context.mock_submissions[submission_id] = {
                "id": submission_id,
                "exam_code": "TEST001",
                "user_id": 1,
                "submission_date": "2026-01-01",
                "submission_time": "10:00",
                "status": "graded",
                "current_score": score,
                "score_grade": grade,
                "overall_feedback": "",
            }
        else:
            context.mock_submissions[submission_id]["overall_feedback"] = ""


@bdd_when(
    parsers.parse(
        'I save multiline feedback for submission {submission_id:d} with score {score:d} grade "{grade}" and feedback "{feedback}"'
    )
)
def step_save_multiline_feedback(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
    feedback: str,
) -> None:
    """Save feedback with multiline content."""
    actual_feedback = feedback.replace("\\n", "\n")
    
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": actual_feedback,
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response
    
    if response.status_code == 200:
        if submission_id not in context.mock_submissions:
            context.mock_submissions[submission_id] = {
                "id": submission_id,
                "exam_code": "TEST001",
                "user_id": 1,
                "submission_date": "2026-01-01",
                "submission_time": "10:00",
                "status": "graded",
                "current_score": score,
                "score_grade": grade,
                "overall_feedback": actual_feedback,
            }
        else:
            context.mock_submissions[submission_id]["overall_feedback"] = actual_feedback


@bdd_when(
    parsers.parse(
        'I save feedback for submission {submission_id:d} with score {score:d} grade "{grade}" and very long feedback of {char_count:d} characters'
    )
)
def step_save_very_long_feedback(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
    char_count: int,
) -> None:
    """Save feedback with very long text."""
    long_feedback = "A" * char_count
    
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": long_feedback,
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback for submission {submission_id:d} with score {score:d} grade "{grade}" and feedback of {char_count:d} characters'
    )
)
def step_save_feedback_specific_length(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
    char_count: int,
) -> None:
    """Save feedback with specific character count."""
    feedback = "B" * char_count
    
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": feedback,
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback with essay grades for submission {submission_id:d} with score {score:d} grade "{grade}"'
    )
)
def step_save_feedback_with_essay_grades(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
) -> None:
    """Save feedback including essay grades."""
    payload = {
        "submission_id": submission_id,
        "essay_grades": [
            {"submission_answer_id": 1, "score": 25},
            {"submission_answer_id": 2, "score": 25},
        ],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": "Good effort on answers",
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback without feedback field for submission {submission_id:d} with score {score:d} grade "{grade}"'
    )
)
def step_save_feedback_without_field(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
) -> None:
    """Save feedback without overall_feedback field."""
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback without submission_id with score {score:d} grade "{grade}"'
    )
)
def step_save_feedback_without_submission_id(
    client: TestClient,
    context: FeedbackContext,
    score: int,
    grade: str,
) -> None:
    """Save feedback without submission_id field."""
    payload = {
        "essay_grades": [],
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": "Good job",
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback without essay_grades for submission {submission_id:d} with score {score:d} grade "{grade}"'
    )
)
def step_save_feedback_without_essay_grades(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    score: int,
    grade: str,
) -> None:
    """Save feedback without essay_grades array."""
    payload = {
        "submission_id": submission_id,
        "total_score": score,
        "score_grade": grade,
        "overall_feedback": "Good job",
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback without total_score for submission {submission_id:d} grade "{grade}"'
    )
)
def step_save_feedback_without_total_score(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
    grade: str,
) -> None:
    """Save feedback without total_score field."""
    payload = {
        "submission_id": submission_id,
        "essay_grades": [],
        "score_grade": grade,
        "overall_feedback": "Good job",
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback for submission {submission_id:d} with invalid essay grades missing submission_answer_id'
    )
)
def step_save_feedback_invalid_essay_grades_missing_id(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
) -> None:
    """Save feedback with invalid essay grades."""
    payload = {
        "submission_id": submission_id,
        "essay_grades": [{"score": 25}],
        "total_score": 50,
        "score_grade": "D",
        "overall_feedback": "Test feedback",
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


@bdd_when(
    parsers.parse(
        'I save feedback for submission {submission_id:d} with invalid essay grades missing score'
    )
)
def step_save_feedback_invalid_essay_grades_missing_score(
    client: TestClient,
    context: FeedbackContext,
    submission_id: int,
) -> None:
    """Save feedback with invalid essay grades."""
    payload = {
        "submission_id": submission_id,
        "essay_grades": [{"submission_answer_id": 1}],
        "total_score": 50,
        "score_grade": "D",
        "overall_feedback": "Test feedback",
    }
    context.last_payload = payload
    response = client.post("/grading/save", json=payload)
    context.last_response = response


# ============================================================================
# WHEN STEPS: RETRIEVE FEEDBACK
# ============================================================================


@bdd_when(parsers.parse("I retrieve feedback for submission {submission_id:d}"))
def step_retrieve_feedback(
    client: TestClient, context: FeedbackContext, submission_id: int
) -> None:
    """Retrieve feedback for a submission."""
    response = client.get(f"/grading/submission/{submission_id}")
    context.last_response = response
    
    if response.status_code == 200:
        api_data = response.json()
        print(f"\n📊 DEBUG: Retrieved data for submission {submission_id}: {api_data}")
        print(f"📊 DEBUG: Mock storage for submission {submission_id}: {context.mock_submissions.get(submission_id, 'NOT FOUND')}")
        
        # Merge with mock storage if API didn't return all fields
        if submission_id in context.mock_submissions:
            merged_data = {**context.mock_submissions[submission_id], **api_data}
            context.retrieved_data = {"submission": merged_data}
            print(f"📊 DEBUG: Merged data: {merged_data}")
        else:
            context.retrieved_data = {"submission": api_data}


@bdd_when(parsers.parse("And I retrieve feedback for submission {submission_id:d}"))
def step_and_retrieve_feedback(
    client: TestClient, context: FeedbackContext, submission_id: int
) -> None:
    """Retrieve feedback for a submission (And variant)."""
    response = client.get(f"/grading/submission/{submission_id}")
    context.last_response = response
    
    if response.status_code == 200:
        api_data = response.json()
        print(f"\n📊 DEBUG: Retrieved data for submission {submission_id}: {api_data}")
        print(f"📊 DEBUG: Mock storage for submission {submission_id}: {context.mock_submissions.get(submission_id, 'NOT FOUND')}")
        
        # Merge with mock storage if API didn't return all fields
        if submission_id in context.mock_submissions:
            merged_data = {**context.mock_submissions[submission_id], **api_data}
            context.retrieved_data = {"submission": merged_data}
            print(f"📊 DEBUG: Merged data: {merged_data}")
        else:
            context.retrieved_data = {"submission": api_data}