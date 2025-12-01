import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)


# ---------------------------------------------------------
# Utility: Builds a mock cursor and sets proper side_effect
# ---------------------------------------------------------
def build_mock_cursor():
    cur = MagicMock()
    cur.execute.return_value = None
    return cur


# =====================================================================
# 1️⃣ SUCCESS CASE – Full review with correct and incorrect answers
# =====================================================================
def test_review_submission_with_correct_and_incorrect_answers():
    """
    Test that:
    - Correct answers are marked with isCorrect=True
    - Incorrect answers are marked with isCorrect=False
    - Correct answer is shown for MCQ questions
    - Feedback is displayed for all questions
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission row
        {
            "id": 100,
            "exam_code": 5,
            "score": 5,
            "score_grade": "C",
            "overall_feedback": "Review MCQ concepts",
            "status": "graded",
            "exam_title": "Math Test",
            "exam_id": "MATH101",
        },
        # 2) Total marks
        {"total_marks": 10},
        # 3) submissionAnswer – Q1 (MCQ - INCORRECT)
        {"id": 201, "score": 0, "feedback": "Wrong answer", "selected_option_id": 301},
        # 4) submissionAnswer – Q2 (MCQ - CORRECT)
        {"id": 202, "score": 5, "feedback": "Excellent!", "selected_option_id": 402},
    ]

    cur.fetchall.side_effect = [
        # A) questions list
        [
            {
                "id": 10,
                "question_text": "What is 5+5?",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            },
            {
                "id": 11,
                "question_text": "What is 2*3?",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            },
        ],
        # B) MCQ options for Q1
        [
            {"id": 300, "option_text": "8", "is_correct": False},
            {"id": 301, "option_text": "9", "is_correct": False},  # Selected (wrong)
            {"id": 302, "option_text": "10", "is_correct": True},  # Correct answer
        ],
        # C) MCQ options for Q2
        [
            {"id": 401, "option_text": "5", "is_correct": False},
            {"id": 402, "option_text": "6", "is_correct": True},  # Selected (correct)
            {"id": 403, "option_text": "7", "is_correct": False},
        ],
    ]

    # Patch the correct module
    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/100/review?user_id=5")

    assert resp.status_code == 200
    data = resp.json()

    # Verify overall structure
    assert data["submissionId"] == "sub100"
    assert data["score"] == "5/10"
    assert data["percentage"] == "50.0%"
    assert data["overallFeedback"] == "Review MCQ concepts"
    assert len(data["questions"]) == 2

    # Verify Q1 (INCORRECT answer)
    q1 = data["questions"][0]
    assert q1["questionNumber"] == 1
    assert q1["type"] == "Multiple Choice"
    assert q1["marks"] == 5
    assert q1["earnedMarks"] == 0
    assert q1["selectedAnswer"] == "B"  # Selected wrong option (301)
    assert q1["isCorrect"] is False
    # Verify correct answer is marked in options
    correct_option = next(opt for opt in q1["options"] if opt["isCorrect"])
    assert correct_option["id"] == "C"
    assert correct_option["text"] == "10"

    # Verify Q2 (CORRECT answer)
    q2 = data["questions"][1]
    assert q2["questionNumber"] == 2
    assert q2["selectedAnswer"] == "B"  # Selected correct option (402)
    assert q2["isCorrect"] is True
    assert q2["earnedMarks"] == 5


# =====================================================================
# 2️⃣ Essay Question - Show feedback and earned marks
# =====================================================================
def test_review_essay_with_partial_marks_and_feedback():
    """
    Test that:
    - Essay answers are displayed
    - Feedback is shown for essay questions
    - Partial marks are correctly displayed
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission row
        {
            "id": 150,
            "exam_code": 8,
            "score": 7,
            "score_grade": "B",
            "overall_feedback": "Good understanding, needs more detail",
            "status": "graded",
            "exam_title": "Science Essay",
            "exam_id": "SCI201",
        },
        # 2) Total marks
        {"total_marks": 10},
        # 3) submissionAnswer – Essay with partial marks
        {
            "id": 301,
            "score": 7,
            "feedback": "Good explanation but missing key points about mitochondria",
            "selected_option_id": None,
        },
        # 4) essay content
        {
            "essay_answer": "The cell is the basic unit of life. It contains nucleus and cytoplasm."
        },
    ]

    cur.fetchall.side_effect = [
        # A) questions list
        [
            {
                "id": 20,
                "question_text": "Explain the structure of a cell.",
                "question_type": "essay",
                "marks": 10,
                "rubric": "Expected: nucleus, cytoplasm, mitochondria, cell membrane",
            }
        ]
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/150/review?user_id=8")

    assert resp.status_code == 200
    data = resp.json()

    # Verify essay question details
    q = data["questions"][0]
    assert q["type"] == "Essay Question"
    assert q["marks"] == 10
    assert q["earnedMarks"] == 7
    assert (
        q["answer"]
        == "The cell is the basic unit of life. It contains nucleus and cytoplasm."
    )
    assert q["feedback"] == "Good explanation but missing key points about mitochondria"
    assert "options" not in q  # Essay shouldn't have options


# =====================================================================
# 3️⃣ Mixed Questions - MCQ + Essay in same exam
# =====================================================================
def test_review_mixed_question_types():
    """
    Test exam with both MCQ and essay questions
    Verify correct answer display for each type
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission
        {
            "id": 200,
            "exam_code": 12,
            "score": 12,
            "score_grade": "A",
            "overall_feedback": "Excellent work",
            "status": "graded",
            "exam_title": "Comprehensive Test",
            "exam_id": "COMP301",
        },
        # 2) Total marks
        {"total_marks": 15},
        # 3) MCQ answer (correct)
        {"id": 401, "score": 5, "feedback": "Perfect!", "selected_option_id": 501},
        # 4) Essay answer
        {
            "id": 402,
            "score": 7,
            "feedback": "Great analysis",
            "selected_option_id": None,
        },
        # 5) Essay content
        {"essay_answer": "Detailed essay response about photosynthesis."},
    ]

    cur.fetchall.side_effect = [
        # A) Questions
        [
            {
                "id": 30,
                "question_text": "What is photosynthesis?",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            },
            {
                "id": 31,
                "question_text": "Explain the process in detail.",
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
            },
        ],
        # B) MCQ options
        [
            {"id": 500, "option_text": "Respiration", "is_correct": False},
            {
                "id": 501,
                "option_text": "Converting light to energy",
                "is_correct": True,
            },
            {"id": 502, "option_text": "Cell division", "is_correct": False},
        ],
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/200/review?user_id=10")

    assert resp.status_code == 200
    data = resp.json()

    assert len(data["questions"]) == 2

    # MCQ verification
    mcq = data["questions"][0]
    assert mcq["type"] == "Multiple Choice"
    assert mcq["isCorrect"] is True
    assert len(mcq["options"]) == 3

    # Essay verification
    essay = data["questions"][1]
    assert essay["type"] == "Essay Question"
    assert "answer" in essay
    assert "feedback" in essay


# =====================================================================
# 4️⃣ EDGE CASE - Student didn't answer a question (No submission answer)
# =====================================================================
def test_review_unanswered_mcq_question():
    """
    Test when student didn't answer an MCQ question at all
    Should show earnedMarks = 0, selectedAnswer = None, and isCorrect = False
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission
        {
            "id": 450,
            "exam_code": 25,
            "score": 5,
            "score_grade": "C",
            "overall_feedback": "Incomplete submission",
            "status": "graded",
            "exam_title": "Pop Quiz",
            "exam_id": "PQ001",
        },
        # 2) Total marks
        {"total_marks": 10},
        # 3) Q1 - answered
        {"id": 901, "score": 5, "feedback": "Correct", "selected_option_id": 1201},
        # 4) Q2 - not answered (None)
        None,
    ]

    cur.fetchall.side_effect = [
        # A) Questions
        [
            {
                "id": 80,
                "question_text": "Question 1",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            },
            {
                "id": 81,
                "question_text": "Question 2",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            },
        ],
        # B) Q1 options
        [
            {"id": 1200, "option_text": "Wrong", "is_correct": False},
            {"id": 1201, "option_text": "Correct", "is_correct": True},
        ],
        # C) Q2 options
        [
            {"id": 1300, "option_text": "Answer A", "is_correct": True},
            {"id": 1301, "option_text": "Answer B", "is_correct": False},
        ],
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/450/review?user_id=22")

    assert resp.status_code == 200
    data = resp.json()

    # Q1 should be normal
    q1 = data["questions"][0]
    assert q1["earnedMarks"] == 5
    assert q1["isCorrect"] is True

    # Q2 should show as unanswered
    q2 = data["questions"][1]
    assert q2["earnedMarks"] == 0
    assert q2["selectedAnswer"] is None
    assert q2["isCorrect"] is False


# =====================================================================
# 5️⃣ EDGE CASE - Essay with no answer submitted
# =====================================================================
def test_review_essay_no_answer_submitted():
    """
    Test essay question where student submitted nothing
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission
        {
            "id": 500,
            "exam_code": 28,
            "score": 0,
            "score_grade": "F",
            "overall_feedback": "No answers provided",
            "status": "graded",
            "exam_title": "Essay Test",
            "exam_id": "ESSAY001",
        },
        # 2) Total marks
        {"total_marks": 20},
        # 3) No submission answer for this question
        None,
    ]

    cur.fetchall.side_effect = [
        # A) Question
        [
            {
                "id": 90,
                "question_text": "Write an essay",
                "question_type": "essay",
                "marks": 20,
                "rubric": None,
            }
        ]
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/500/review?user_id=25")

    assert resp.status_code == 200
    data = resp.json()

    q = data["questions"][0]
    assert q["earnedMarks"] == 0
    assert q["answer"] == "No answer provided"
    assert q["feedback"] is None


# =====================================================================
# 6️⃣ Score Display - Verify score formatting
# =====================================================================
def test_review_score_formatting():
    """
    Test that scores are displayed in correct format: "X/Y"
    And percentage is calculated correctly
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        # 1) Submission with 13 out of 20
        {
            "id": 600,
            "exam_code": 32,
            "score": 13,
            "score_grade": "B",
            "overall_feedback": None,
            "status": "graded",
            "exam_title": "Test",
            "exam_id": "T001",
        },
        # 2) Total marks
        {"total_marks": 20},
        # 3) Answer
        {"id": 1101, "score": 13, "feedback": None, "selected_option_id": None},
        # 4) Essay
        {"essay_answer": "Answer"},
    ]

    cur.fetchall.side_effect = [
        [
            {
                "id": 110,
                "question_text": "Q",
                "question_type": "essay",
                "marks": 20,
                "rubric": None,
            }
        ]
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/600/review?user_id=30")

    assert resp.status_code == 200
    data = resp.json()

    # Verify score format
    assert data["score"] == "13/20"
    # Verify percentage: 13/20 = 65%
    assert data["percentage"] == "65.0%"


# =====================================================================
# 7️⃣ SECURITY - Cannot view other student's submission
# =====================================================================
def test_review_wrong_user_access_denied():
    """
    Test that student cannot view another student's submission
    """
    cur = build_mock_cursor()
    cur.fetchone.side_effect = [None]  # No submission found for this user

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/100/review?user_id=999")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# =====================================================================
# 8️⃣ AUTHORIZATION - Cannot review ungraded submission
# =====================================================================
def test_review_pending_submission_blocked():
    """
    Test that student cannot review submission that's still pending grading
    """
    cur = build_mock_cursor()
    cur.fetchone.side_effect = [
        {
            "id": 800,
            "exam_code": 40,
            "score": None,
            "score_grade": None,
            "overall_feedback": None,
            "status": "pending",
            "exam_title": "Pending Exam",
            "exam_id": "PEND001",
        }
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/800/review?user_id=40")

    assert resp.status_code == 404
    assert "not graded" in resp.json()["detail"].lower()


# =====================================================================
# 9️⃣ AUTHORIZATION - Cannot review submitted but not graded
# =====================================================================
def test_review_submitted_not_graded_blocked():
    """
    Test that student cannot review submission with 'submitted' status
    Only 'graded' status allows review
    """
    cur = build_mock_cursor()
    cur.fetchone.side_effect = [
        {
            "id": 850,
            "exam_code": 42,
            "score": None,
            "score_grade": None,
            "overall_feedback": None,
            "status": "submitted",
            "exam_title": "Recent Submission",
            "exam_id": "SUB001",
        }
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/850/review?user_id=42")

    assert resp.status_code == 404
    assert "not graded" in resp.json()["detail"].lower()


# =====================================================================
# 🔟 MCQ with no selected option (student skipped)
# =====================================================================
def test_review_mcq_with_null_selected_option():
    """
    Test MCQ where selected_option_id is None
    Should show selectedAnswer = None and isCorrect = False
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        {
            "id": 22,
            "exam_code": 10,
            "score": 0,
            "score_grade": None,
            "overall_feedback": None,
            "status": "graded",
            "exam_title": "Exam",
            "exam_id": "EX10",
        },
        {"total_marks": 5},
        {"id": 701, "score": 0, "feedback": None, "selected_option_id": None},
    ]

    cur.fetchall.side_effect = [
        [
            {
                "id": 1,
                "question_text": "What is 2+3?",
                "question_type": "mcq",
                "marks": 5,
                "rubric": None,
            }
        ],
        [
            {"id": 500, "option_text": "4", "is_correct": False},
            {"id": 501, "option_text": "5", "is_correct": True},
        ],
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/22/review?user_id=2")

    assert resp.status_code == 200
    q = resp.json()["questions"][0]

    assert q["selectedAnswer"] is None
    assert q["isCorrect"] is False
    assert q["earnedMarks"] == 0


# =====================================================================
# 1️⃣1️⃣ Essay with no essayAnswer row
# =====================================================================
def test_review_essay_no_answer_row():
    """
    Test essay with submissionAnswer but no essayAnswer record
    """
    cur = build_mock_cursor()

    cur.fetchone.side_effect = [
        {
            "id": 22,
            "exam_code": 10,
            "score": 2,
            "score_grade": None,
            "overall_feedback": None,
            "status": "graded",
            "exam_title": "Exam",
            "exam_id": "EX10",
        },
        {"total_marks": 10},
        {"id": 800, "score": 2, "feedback": "OK", "selected_option_id": None},
        None,  # essayAnswer missing
    ]

    cur.fetchall.side_effect = [
        [
            {
                "id": 1,
                "question_text": "Describe water cycle.",
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
            }
        ]
    ]

    with patch("src.services.submission_service.get_conn") as mock_conn:
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            cur
        )
        resp = client.get("/submissions/22/review?user_id=2")

    assert resp.status_code == 200
    q = resp.json()["questions"][0]

    assert q["answer"] == "No answer provided"
    assert q["feedback"] == "OK"  # Feedback still available from submissionAnswer
    assert q["earnedMarks"] == 2

