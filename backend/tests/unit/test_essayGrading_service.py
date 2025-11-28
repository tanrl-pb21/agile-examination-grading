import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 🔧 MUST UPDATE THESE to match your DB
EXISTING_SUBMISSION_ID = 22
ESSAY_SUBMISSION_ANSWER_ID = 45


# =====================================================
# Helper: Valid base payload
# =====================================================
def valid_payload(score=5.0):
    return {
        "submission_id": EXISTING_SUBMISSION_ID,
        "essay_grades": [
            {
                "submission_answer_id": ESSAY_SUBMISSION_ANSWER_ID,
                "score": score,
                "feedback": "Good answer",
            }
        ],
        "total_score": score,
        "score_grade": "B",
        "overall_feedback": "Nice work",
    }


# =====================================================
# VALID CASE (should pass)
# =====================================================
def test_save_essay_valid_marks():
    payload = valid_payload(score=7.5)
    res = client.post("/grading/save", json=payload)
    assert res.status_code == 200
    assert res.json()["success"] is True


# =====================================================
# INVALID: submission_id does not exist
# =====================================================
def test_save_essay_invalid_submission_id():
    payload = valid_payload()
    payload["submission_id"] = 999999999

    res = client.post("/grading/save", json=payload)
    assert res.status_code == 404
