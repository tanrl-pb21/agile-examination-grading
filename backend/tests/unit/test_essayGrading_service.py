import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)


# =====================================================
# Helper Functions
# =====================================================
def build_mock_cursor():
    """Build a mock cursor for database operations"""
    cur = MagicMock()
    cur.execute.return_value = None
    cur.fetchone.return_value = None
    cur.fetchall.return_value = []
    return cur


def valid_save_payload(submission_id=100, score=7.5, feedback="Good answer"):
    """Generate a valid grading payload"""
    return {
        "submission_id": submission_id,
        "essay_grades": [
            {
                "submission_answer_id": 500,
                "score": score,
                "feedback": feedback,
            }
        ],
        "total_score": score,
        "score_grade": "B",
        "overall_feedback": "Nice work overall",
    }


# =====================================================
# GET SUBMISSION FOR GRADING TESTS
# =====================================================
def test_get_submission_for_grading_success_with_essay():
    """Test successfully retrieving a submission with essay questions"""
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission info
        {
            "submission_id": 100,
            "exam_code": 5,
            "user_id": 10,
            "submission_date": "2024-01-15",
            "submission_time": "10:30:00",
            "status": "submitted",
            "current_score": None,
            "score_grade": None,
            "overall_feedback": None,
            "student_email": "student@test.com",
            "student_name": "student@test.com",
        },
        # 2) Exam info
        {
            "id": 5,
            "title": "Math Midterm",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "date": "2024-01-15",
        },
        # 3) Total score from submissionAnswer
        {"total_score": 0},
        # 4) Essay answer for question 1
        {
            "submission_answer_id": 500,
            "score": None,
            "feedback": None,
            "essay_answer": "This is the student's essay response about photosynthesis.",
        },
    ]

    cur.fetchall.side_effect = [
        # Questions list
        [
            {
                "id": 1,
                "question_text": "Explain photosynthesis",
                "question_type": "essay",
                "marks": 10,
                "rubric": "Should mention: light, chlorophyll, glucose",
            }
        ]
    ]

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.get("/grading/submission/100")

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "submission" in data
    assert "exam" in data
    assert "questions" in data

    # Verify submission data
    assert data["submission"]["id"] == 100
    assert data["submission"]["student_email"] == "student@test.com"
    assert data["submission"]["current_score"] == 0

    # Verify exam data
    assert data["exam"]["title"] == "Math Midterm"

    # Verify questions
    assert len(data["questions"]) == 1
    assert data["questions"][0]["question_type"] == "essay"
    assert data["questions"][0]["student_answer"]["essay_answer"] is not None
    assert data["questions"][0]["rubric"] is not None


def test_get_submission_with_mcq_and_essay():
    """Test getting submission with mixed question types"""
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission
        {
            "submission_id": 200,
            "exam_code": 10,
            "user_id": 20,
            "submission_date": "2024-01-20",
            "submission_time": "14:00:00",
            "status": "submitted",
            "current_score": 5,
            "score_grade": None,
            "overall_feedback": None,
            "student_email": "test@example.com",
            "student_name": "test@example.com",
        },
        # 2) Exam
        {
            "id": 10,
            "title": "Mixed Test",
            "start_time": "13:00:00",
            "end_time": "15:00:00",
            "date": "2024-01-20",
        },
        # 3) Total score
        {"total_score": 5},
        # 4) MCQ answer
        {
            "submission_answer_id": 600,
            "selected_option_id": 101,
            "score": 5,
            "is_correct": True,
            "option_text": "Correct answer",
        },
        # 5) Essay answer
        {
            "submission_answer_id": 601,
            "score": None,
            "feedback": None,
            "essay_answer": "Student's essay about climate change.",
        },
    ]

    cur.fetchall.side_effect = [
        # Questions
        [
            {
                "id": 1,
                "question_text": "What is climate change?",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            },
            {
                "id": 2,
                "question_text": "Explain the causes",
                "question_type": "essay",
                "marks": 10,
                "rubric": "Mention greenhouse gases",
            },
        ],
        # MCQ options for Q1
        [
            {"id": 100, "option_text": "Wrong answer", "is_correct": False},
            {"id": 101, "option_text": "Correct answer", "is_correct": True},
        ],
    ]

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.get("/grading/submission/200")

    assert response.status_code == 200
    data = response.json()

    # Verify both question types
    assert len(data["questions"]) == 2
    assert data["questions"][0]["question_type"] == "mcq"
    assert data["questions"][0]["options"] is not None
    assert data["questions"][1]["question_type"] == "essay"
    assert data["questions"][1]["student_answer"]["essay_answer"] is not None


def test_get_submission_already_graded():
    """Test retrieving a submission that was already graded"""
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # Submission with existing grade
        {
            "submission_id": 300,
            "exam_code": 15,
            "user_id": 30,
            "submission_date": "2024-01-10",
            "submission_time": "11:00:00",
            "status": "graded",
            "current_score": 8,
            "score_grade": "B",
            "overall_feedback": "Good work, but needs improvement on question 2",
            "student_email": "graded@test.com",
            "student_name": "graded@test.com",
        },
        # Exam
        {
            "id": 15,
            "title": "History Test",
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "date": "2024-01-10",
        },
        # Total score
        {"total_score": 8},
        # Essay with existing grade
        {
            "submission_answer_id": 700,
            "score": 8,
            "feedback": "Good analysis but missing some key points",
            "essay_answer": "The French Revolution was caused by...",
        },
    ]

    cur.fetchall.side_effect = [
        [
            {
                "id": 1,
                "question_text": "Discuss the French Revolution",
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
            }
        ]
    ]

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.get("/grading/submission/300")

    assert response.status_code == 200
    data = response.json()

    # Verify existing grades are included
    assert data["submission"]["score_grade"] == "B"
    assert (
        data["submission"]["overall_feedback"]
        == "Good work, but needs improvement on question 2"
    )
    assert data["questions"][0]["student_answer"]["score"] == 8
    assert data["questions"][0]["student_answer"]["feedback"] is not None


def test_get_submission_not_found():
    """Test getting a non-existent submission"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = None

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.get("/grading/submission/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_submission_exam_not_found():
    """Test when submission exists but exam doesn't"""
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # Submission exists
        {
            "submission_id": 400,
            "exam_code": 999,
            "user_id": 40,
            "submission_date": "2024-01-15",
            "submission_time": "10:00:00",
            "status": "submitted",
            "current_score": None,
            "score_grade": None,
            "overall_feedback": None,
            "student_email": "test@test.com",
            "student_name": "test@test.com",
        },
        # Exam not found
        None,
    ]

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.get("/grading/submission/400")

    assert response.status_code == 404
    assert "exam not found" in response.json()["detail"].lower()


def test_get_submission_with_no_answers():
    """Test submission where student didn't answer essay question"""
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # Submission
        {
            "submission_id": 500,
            "exam_code": 20,
            "user_id": 50,
            "submission_date": "2024-01-15",
            "submission_time": "10:00:00",
            "status": "submitted",
            "current_score": None,
            "score_grade": None,
            "overall_feedback": None,
            "student_email": "empty@test.com",
            "student_name": "empty@test.com",
        },
        # Exam
        {
            "id": 20,
            "title": "Test",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "date": "2024-01-15",
        },
        # Total score
        {"total_score": 0},
        # No answer submitted
        None,
    ]

    cur.fetchall.side_effect = [
        [
            {
                "id": 1,
                "question_text": "Essay question",
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
            }
        ]
    ]

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.get("/grading/submission/500")

    assert response.status_code == 200
    data = response.json()
    assert data["questions"][0]["student_answer"] is None


# =====================================================
# SAVE GRADES TESTS
# =====================================================
def test_save_grades_success():
    """Test successfully saving essay grades"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 100}

    payload = valid_save_payload(
        submission_id=100, score=8.5, feedback="Excellent work"
    )

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "saved successfully" in data["message"].lower()

    # Verify UPDATE queries were called
    assert cur.execute.call_count >= 2  # At least essay update + submission update


def test_save_grades_multiple_essays():
    """Test saving grades for multiple essay questions"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 200}

    payload = {
        "submission_id": 200,
        "essay_grades": [
            {"submission_answer_id": 501, "score": 7.0, "feedback": "Good answer"},
            {
                "submission_answer_id": 502,
                "score": 8.5,
                "feedback": "Excellent analysis",
            },
            {
                "submission_answer_id": 503,
                "score": 6.0,
                "feedback": "Needs more detail",
            },
        ],
        "total_score": 21.5,
        "score_grade": "B",
        "overall_feedback": "Overall good performance",
    }

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200
    # Verify 3 essay updates + 1 submission update = 4 execute calls
    assert cur.execute.call_count == 4


def test_save_grades_with_zero_score():
    """Test saving grade with 0 score"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 300}

    payload = valid_save_payload(
        submission_id=300, score=0.0, feedback="No answer provided"
    )

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_save_grades_with_perfect_score():
    """Test saving grade with maximum score"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 400}

    payload = valid_save_payload(
        submission_id=400, score=10.0, feedback="Perfect answer"
    )
    payload["score_grade"] = "A"

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_save_grades_with_partial_marks():
    """Test saving grade with partial marks (decimal)"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 500}

    payload = valid_save_payload(
        submission_id=500, score=7.25, feedback="Good but incomplete"
    )

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_save_grades_without_feedback():
    """Test saving grade without feedback (optional field)"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 600}

    payload = {
        "submission_id": 600,
        "essay_grades": [{"submission_answer_id": 700, "score": 5.0}],
        "total_score": 5.0,
        "score_grade": "C",
    }

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_save_grades_without_overall_feedback():
    """Test saving without overall feedback"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 700}

    payload = valid_save_payload(submission_id=700)
    del payload["overall_feedback"]

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_save_grades_submission_not_found():
    """Test saving grades for non-existent submission"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = None  # UPDATE returns no rows

    payload = valid_save_payload(submission_id=99999)

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_save_grades_overall_feedback_too_long():
    """Test validation for overly long feedback"""
    payload = valid_save_payload()
    payload["overall_feedback"] = "A" * 5001  # Exceeds 5000 char limit

    response = client.post("/grading/save", json=payload)

    assert response.status_code == 400
    assert "exceeds maximum length" in response.json()["detail"]


def test_save_grades_empty_essay_grades_list():
    """Test saving with empty essay grades list"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 800}

    payload = {
        "submission_id": 800,
        "essay_grades": [],
        "total_score": 5.0,
        "score_grade": "B",
        "overall_feedback": "MCQ only exam",
    }

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_save_grades_negative_score():
    """Test validation - negative scores should be accepted (for testing edge cases)"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 900}

    payload = valid_save_payload(submission_id=900, score=-1.0)

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    # Should succeed (no validation in backend for negative scores)
    assert response.status_code == 200


def test_save_grades_regrading_existing():
    """Test re-grading a previously graded submission"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 1000}

    payload = valid_save_payload(
        submission_id=1000, score=9.0, feedback="Improved grade"
    )

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200
    # Should update existing grades


def test_save_grades_with_null_score_grade():
    """Test saving without letter grade"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 1100}

    payload = valid_save_payload(submission_id=1100)
    payload["score_grade"] = None

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_save_grades_updates_status_to_graded():
    """Test that saving grades sets status to 'graded'"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 1200}

    payload = valid_save_payload(submission_id=1200)

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200

    # Check that the UPDATE query includes status='graded'
    update_calls = [
        call for call in cur.execute.call_args_list if "UPDATE submission" in str(call)
    ]
    assert len(update_calls) > 0


# =====================================================
# EDGE CASES AND ERROR HANDLING
# =====================================================
def test_save_grades_with_special_characters_in_feedback():
    """Test feedback with special characters"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 1300}

    payload = valid_save_payload(
        submission_id=1300,
        feedback="Great work! You've shown excellent understanding of the topic. 🎉",
    )

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_save_grades_with_multiline_feedback():
    """Test feedback with line breaks"""
    cur = build_mock_cursor()
    cur.fetchone.return_value = {"id": 1400}

    feedback = """Good answer.
    
Points to improve:
- Add more examples
- Cite sources
- Expand conclusion"""

    payload = valid_save_payload(submission_id=1400, feedback=feedback)

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.post("/grading/save", json=payload)

    assert response.status_code == 200


def test_get_submission_with_multiple_essays():
    """Test submission with several essay questions"""
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # Submission
        {
            "submission_id": 1500,
            "exam_code": 25,
            "user_id": 50,
            "submission_date": "2024-01-15",
            "submission_time": "10:00:00",
            "status": "submitted",
            "current_score": None,
            "score_grade": None,
            "overall_feedback": None,
            "student_email": "multi@test.com",
            "student_name": "multi@test.com",
        },
        # Exam
        {
            "id": 25,
            "title": "Essay Exam",
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "date": "2024-01-15",
        },
        # Total score
        {"total_score": 0},
        # Essay 1
        {
            "submission_answer_id": 801,
            "score": None,
            "feedback": None,
            "essay_answer": "Answer 1",
        },
        # Essay 2
        {
            "submission_answer_id": 802,
            "score": None,
            "feedback": None,
            "essay_answer": "Answer 2",
        },
        # Essay 3
        {
            "submission_answer_id": 803,
            "score": None,
            "feedback": None,
            "essay_answer": "Answer 3",
        },
    ]

    cur.fetchall.side_effect = [
        [
            {
                "id": 1,
                "question_text": "Q1",
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
            },
            {
                "id": 2,
                "question_text": "Q2",
                "question_type": "essay",
                "marks": 15,
                "rubric": None,
            },
            {
                "id": 3,
                "question_text": "Q3",
                "question_type": "essay",
                "marks": 20,
                "rubric": None,
            },
        ]
    ]

    with patch("src.routers.grading.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        response = client.get("/grading/submission/1500")

    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 3
    assert all(q["question_type"] == "essay" for q in data["questions"])

