from src.db import get_conn
from psycopg.rows import dict_row
from datetime import datetime, date, time as dt_time


class SubmissionService:
    def _is_exam_ended(self, exam_date, end_time):
        """Check if exam has ended based on date and end time"""
        if not exam_date or not end_time:
            return False

        # Combine exam date and end time
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%H:%M:%S").time()

        exam_end_datetime = datetime.combine(exam_date, end_time)

        # Compare with current datetime
        return datetime.now() > exam_end_datetime

    # ========== STUDENT SUBMISSION METHODS ==========

    def get_student_submissions(self, user_id: int):
        """Get all submissions for a specific student"""
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT 
                        s.id,
                        s.exam_code,
                        s.submission_date,
                        s.submission_time,
                        s.score,
                        s.score_grade,
                        LOWER(s.status) as status,
                        e.title as exam_title,
                        e.exam_code as exam_id
                    FROM submission s
                    INNER JOIN exams e ON s.exam_code = e.id
                    WHERE s.user_id = %s
                    ORDER BY s.submission_date DESC, s.submission_time DESC;
                """,
                    (user_id,),
                )

                submissions = cur.fetchall()

                result = []
                for sub in submissions:
                    # Calculate total marks for the exam
                    cur.execute(
                        """
                        SELECT SUM(marks) as total_marks
                        FROM question
                        WHERE exam_id = %s;
                    """,
                        (sub["exam_code"],),
                    )

                    total_marks_result = cur.fetchone()
                    total_marks = (
                        total_marks_result["total_marks"] if total_marks_result else 0
                    )

                    # Calculate percentage
                    percentage = 0
                    if total_marks and total_marks > 0 and sub["score"] is not None:
                        percentage = (sub["score"] / total_marks) * 100

                    # Determine display status
                    display_status = sub["status"]
                    # Correct status logic (do NOT convert pending → graded)
                    if sub["status"] == "graded":
                        display_status = "graded"
                    elif sub["status"] == "pending":
                        display_status = "pending"
                    elif sub["status"] in ("submitted", None, ""):
                        display_status = "submitted"
                    else:
                        display_status = sub["status"]

                    result.append(
                        {
                            "id": sub["id"],
                            "submission_id": f"sub{sub['id']}",
                            "exam_title": sub["exam_title"],
                            "exam_id": sub["exam_id"] or f"EXAM-{sub['exam_code']}",
                            "date": (
                                sub["submission_date"].strftime("%m/%d/%Y")
                                if sub["submission_date"]
                                else None
                            ),
                            "time": (
                                str(sub["submission_time"])
                                if sub["submission_time"]
                                else None
                            ),
                            "score": (
                                f"{sub['score']}/{total_marks}"
                                if sub["score"] is not None
                                else None
                            ),
                            "percentage": (
                                f"{percentage:.1f}%"
                                if sub["score"] is not None
                                else None
                            ),
                            "status": display_status,
                        }
                    )

                return result

    def get_submission_review(self, submission_id: int, user_id: int):
        """Get detailed review of a submission with questions and answers"""
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get submission details
                # Get submission details
                cur.execute(
                    """
                    SELECT 
                        s.id,
                        s.exam_code,
                        s.score,
                        s.score_grade,
                        s.overall_feedback,
                        LOWER(s.status) AS status,
                        e.title as exam_title,
                        e.exam_code as exam_id
                    FROM submission s
                    INNER JOIN exams e ON s.exam_code = e.id
                    WHERE s.id = %s AND s.user_id = %s;
                """,
                    (submission_id, user_id),
                )

                submission = cur.fetchone()

                if not submission:
                    raise ValueError(
                        f"Submission {submission_id} not found for this user"
                    )

                # ❗ Block review if not graded
                if submission["status"] != "graded":
                    raise ValueError(
                        "Submission is not graded yet. You cannot review the answers."
                    )

                exam_id = submission["exam_code"]

                # Calculate total marks
                cur.execute(
                    """
                    SELECT SUM(marks) as total_marks
                    FROM question
                    WHERE exam_id = %s;
                """,
                    (exam_id,),
                )

                total_marks_result = cur.fetchone()
                total_marks = (
                    total_marks_result["total_marks"] if total_marks_result else 0
                )

                # Calculate percentage
                percentage = 0
                if total_marks and total_marks > 0 and submission["score"] is not None:
                    percentage = (submission["score"] / total_marks) * 100

                # Get all questions for the exam
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
                    ORDER BY q.id;
                """,
                    (exam_id,),
                )

                questions = cur.fetchall()

                question_list = []
                question_number = 1

                for q in questions:
                    question_data = {
                        "id": q["id"],
                        "type": (
                            "Multiple Choice"
                            if q["question_type"] == "mcq"
                            else "Essay Question"
                        ),
                        "marks": q["marks"],
                        "earnedMarks": 0,
                        "questionNumber": question_number,
                        "question": q["question_text"],
                    }

                    # Get submission answer - FIX: Quote table name
                    cur.execute(
                        """
                        SELECT 
                            sa.id,
                            sa.score,
                            sa.feedback,
                            sa.selected_option_id
                        FROM "submissionAnswer" sa
                        WHERE sa.submission_id = %s AND sa.question_id = %s;
                    """,
                        (submission_id, q["id"]),
                    )

                    answer = cur.fetchone()

                    if answer:
                        question_data["earnedMarks"] = answer["score"] or 0

                    if q["question_type"] == "mcq":
                        # Get all options
                        cur.execute(
                            """
                            SELECT 
                                id,
                                option_text,
                                is_correct
                            FROM "questionOption"
                            WHERE question_id = %s
                            ORDER BY id;
                        """,
                            (q["id"],),
                        )

                        options = cur.fetchall()

                        option_labels = [
                            "A",
                            "B",
                            "C",
                            "D",
                            "E",
                            "F",
                            "G",
                            "H",
                            "I",
                            "J",
                        ]
                        question_data["options"] = []

                        selected_option_id = (
                            answer["selected_option_id"] if answer else None
                        )
                        selected_label = None
                        correct_label = None

                        for idx, opt in enumerate(options):
                            label = (
                                option_labels[idx]
                                if idx < len(option_labels)
                                else str(idx)
                            )
                            question_data["options"].append(
                                {
                                    "id": label,
                                    "text": opt["option_text"],
                                    "isCorrect": opt["is_correct"],
                                }
                            )

                            if opt["id"] == selected_option_id:
                                selected_label = label
                            if opt["is_correct"]:
                                correct_label = label

                        question_data["selectedAnswer"] = selected_label
                        question_data["isCorrect"] = (
                            (selected_label == correct_label)
                            if selected_label
                            else False
                        )

                    else:  # Essay question
                        # Get essay answer - FIX: Quote table name
                        if answer:
                            cur.execute(
                                """
                                SELECT essay_answer
                                FROM "essayAnswer"
                                WHERE submission_answer_id = %s;
                            """,
                                (answer["id"],),
                            )

                            essay = cur.fetchone()
                            question_data["answer"] = (
                                essay["essay_answer"] if essay else "No answer provided"
                            )
                            question_data["feedback"] = answer["feedback"]
                        else:
                            question_data["answer"] = "No answer provided"
                            question_data["feedback"] = None

                    question_list.append(question_data)
                    question_number += 1

                return {
                    "submissionId": f"sub{submission['id']}",
                    "examTitle": submission["exam_title"],
                    "examId": submission["exam_id"] or f"EXAM-{exam_id}",
                    "score": (
                        f"{submission['score']}/{total_marks}"
                        if submission["score"] is not None
                        else f"0/{total_marks}"
                    ),
                    "percentage": (
                        f"{percentage:.1f}%"
                        if submission["score"] is not None
                        else "0.0%"
                    ),
                    "overallFeedback": submission["overall_feedback"],
                    "questions": question_list,
                }
