import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# -------------------------------------------------------
# SUCCESS: Submission 22 belongs to user 2 + is graded
# -------------------------------------------------------


def test_review_submission_success():
    response = client.get("/submissions/22/review?user_id=2")

    assert response.status_code == 200
    data = response.json()

    # API returns string "sub22"
    assert data["submissionId"] == "sub22"
    assert "questions" in data
    assert len(data["questions"]) > 0


# -------------------------------------------------------
# NOT GRADED: Submission 37 belongs to user 1 but status != graded
# -------------------------------------------------------


def test_review_submission_not_graded():
    response = client.get("/submissions/37/review?user_id=1")

    assert response.status_code == 404

    # API returns: "Submission is not graded yet. You cannot review the answers."
    assert "not graded" in response.json()["detail"].lower()


# -------------------------------------------------------
# WRONG USER: Submission 22 belongs to user 2, not 1
# -------------------------------------------------------


def test_review_wrong_user():
    response = client.get("/submissions/22/review?user_id=1")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# -------------------------------------------------------
# INVALID ID: Submission does NOT exist
# -------------------------------------------------------


def test_review_invalid_submission_id():
    response = client.get("/submissions/9999/review?user_id=1")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
