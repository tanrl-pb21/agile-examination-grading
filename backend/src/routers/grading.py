from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.db import get_conn
from psycopg.rows import dict_row

router = APIRouter(prefix="/grading", tags=["Grading"])


class EssayGradeInput(BaseModel):
    submission_answer_id: int
    score: float
    feedback: Optional[str] = None


class SaveGradesInput(BaseModel):
    submission_id: int
    essay_grades: List[EssayGradeInput]
    total_score: float
    score_grade: Optional[str] = None
    overall_feedback: Optional[str] = None


@router.get("/submission/{submission_id}")
def get_submission_for_grading(submission_id: int):
    """
    Get complete submission data for grading including:
    - Student info
    - Exam info
    - All questions with student answers
    - MCQ auto-graded results
    - Overall feedback (if previously saved)
    """
    try:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get submission basic info - INCLUDE overall_feedback and score
                cur.execute(
                    """
                    SELECT 
                        s.id as submission_id,
                        s.exam_code,
                        s.user_id,
                        s.submission_date,
                        s.submission_time,
                        s.status,
                        s.score as current_score,
                        s.score_grade,
                        s.overall_feedback,
                        u.user_email as student_email,
                        u.user_email as student_name
                    FROM submission s
                    INNER JOIN "user" u ON s.user_id = u.id
                    WHERE s.id = %s
                """,
                    (submission_id,),
                )

                submission = cur.fetchone()
                if not submission:
                    raise HTTPException(status_code=404, detail="Submission not found")

                exam_id = submission["exam_code"]

                # Get exam info
                cur.execute(
                    """
                    SELECT id, title, start_time, end_time, date
                    FROM exams
                    WHERE id = %s
                """,
                    (exam_id,),
                )

                exam = cur.fetchone()
                if not exam:
                    raise HTTPException(status_code=404, detail="Exam not found")

                # Get all questions for this exam
                cur.execute(
                    """
                    SELECT 
                        q.id,
                        q.question_text,
                        q.question_type,
                        q.marks,
                        q.rubric
                    FROM question q
                    WHERE q.exam_id = %s
                    ORDER BY q.id
                """,
                    (exam_id,),
                )

                questions = list(cur.fetchall())

                # Calculate current total score from submissionAnswer
                cur.execute(
                    """
                    SELECT COALESCE(SUM(score), 0) as total_score
                    FROM "submissionAnswer"
                    WHERE submission_id = %s
                """,
                    (submission_id,),
                )
                score_result = cur.fetchone()
                current_total_score = score_result["total_score"] if score_result else 0

                # For each question, get options (for MCQ) and student answers
                for question in questions:
                    question_id = question["id"]

                    if question["question_type"] == "mcq":
                        # Get options
                        cur.execute(
                            """
                            SELECT id, option_text, is_correct
                            FROM "questionOption"
                            WHERE question_id = %s
                            ORDER BY id
                        """,
                            (question_id,),
                        )
                        question["options"] = list(cur.fetchall())

                        # Get student's MCQ answer
                        cur.execute(
                            """
                            SELECT 
                                sa.id as submission_answer_id,
                                sa.selected_option_id,
                                sa.score,
                                qo.is_correct,
                                qo.option_text
                            FROM "submissionAnswer" sa
                            LEFT JOIN "questionOption" qo ON sa.selected_option_id = qo.id
                            WHERE sa.submission_id = %s AND sa.question_id = %s
                        """,
                            (submission_id, question_id),
                        )

                        mcq_answer = cur.fetchone()
                        question["student_answer"] = mcq_answer

                    else:  # essay
                        question["options"] = []

                        # Get student's essay answer - JOIN with essayAnswer table
                        cur.execute(
                            """
                            SELECT 
                                sa.id as submission_answer_id,
                                sa.score,
                                sa.feedback,
                                ea.essay_answer
                            FROM "submissionAnswer" sa
                            LEFT JOIN "essayAnswer" ea ON sa.id = ea.submission_answer_id
                            WHERE sa.submission_id = %s AND sa.question_id = %s
                        """,
                            (submission_id, question_id),
                        )

                        essay_answer = cur.fetchone()
                        question["student_answer"] = essay_answer

                # Calculate total possible marks
                total_marks = sum(q["marks"] for q in questions)

                # Format response
                result = {
                    "submission": {
                        "id": submission["submission_id"],
                        "student_id": submission["user_id"],
                        "student_name": submission["student_name"],
                        "student_email": submission["student_email"],
                        "submitted_at": (
                            f"{submission['submission_date']} {submission['submission_time']}"
                            if submission["submission_date"]
                            else None
                        ),
                        "current_score": current_total_score,
                        "score_grade": submission["score_grade"],
                        "overall_feedback": submission[
                            "overall_feedback"
                        ],  # ADDED THIS
                    },
                    "exam": {
                        "id": exam["id"],
                        "title": exam["title"],
                        "date": str(exam["date"]) if exam["date"] else None,
                        "start_time": (
                            str(exam["start_time"]) if exam["start_time"] else None
                        ),
                        "end_time": str(exam["end_time"]) if exam["end_time"] else None,
                    },
                    "questions": questions,
                }

                return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR fetching submission for grading: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
def save_grades(grades: SaveGradesInput):
    """
    Save grading results for a submission
    Updates essay question scores and overall submission score
    """
    try:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Update essay answers
                for essay_grade in grades.essay_grades:
                    cur.execute(
                        """
                        UPDATE "submissionAnswer"
                        SET score = %s, feedback = %s
                        WHERE id = %s
                    """,
                        (
                            essay_grade.score,
                            essay_grade.feedback,
                            essay_grade.submission_answer_id,
                        ),
                    )

                # Update submission with status='graded' and overall feedback
                cur.execute(
                    """
                    UPDATE submission
                    SET status = 'graded',
                        score = %s,
                        score_grade = %s,
                        overall_feedback = %s
                    WHERE id = %s
                    RETURNING id
                """,
                    (
                        grades.total_score,
                        grades.score_grade,
                        grades.overall_feedback,
                        grades.submission_id,
                    ),
                )

                result = cur.fetchone()
                conn.commit()

                if not result:
                    raise HTTPException(status_code=404, detail="Submission not found")

                print(
                    f"✅ Grades saved for submission {grades.submission_id}: Score={grades.total_score}, Feedback={grades.overall_feedback}"
                )
                return {"success": True, "message": "Grades saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR saving grades: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
