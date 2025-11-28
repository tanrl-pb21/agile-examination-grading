from src.db import get_conn
from psycopg.rows import dict_row
from datetime import datetime, date, time,timezone,timedelta


def validate_date_obj(dt: date):
    if dt.year < 1900 or dt.year > 2100:
        raise ValueError("Year must be between 1900 and 2100")
    if dt < date.today():
        raise ValueError("Exam date cannot be in the past")
    return dt


def calculate_duration(start_time_str: str, end_time_str: str) -> int:
    """Calculate duration in minutes between two time strings (HH:MM format)"""
    start = datetime.strptime(start_time_str, "%H:%M").time()
    end = datetime.strptime(end_time_str, "%H:%M").time()
    
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    
    duration = end_minutes - start_minutes
    if duration < 0:
        raise ValueError("End time must be after start time")
    
    return duration


class ExamService:

    def add_exam(self, title, exam_code, date, start_time, end_time, status='scheduled'):
        if not title:
            raise ValueError("Title is required")
        if not exam_code:
            raise ValueError("Exam code is required")
        if not date:
            raise ValueError("Date is required")
        if not start_time or not end_time:
            raise ValueError("Start time and end time are required")
        
        # Parse date if string
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            date_obj = date
        
        # Validate date
        validate_date_obj(date_obj)
        
        # Calculate duration
        duration = calculate_duration(start_time, end_time)
        
        sql = """
            INSERT INTO exams (title, exam_code, date, start_time, end_time, duration, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, exam_code, date, start_time, end_time, duration, status;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (title, exam_code, date, start_time, end_time, duration, status))
                row = cur.fetchone()

        return row

    def update_exam(self, exam_id, title, exam_code, date, start_time, end_time, status='scheduled'):
        if not title:
            raise ValueError("Title is required")
        if not exam_code:
            raise ValueError("Exam code is required")
        if not date:
            raise ValueError("Date is required")
        if not start_time or not end_time:
            raise ValueError("Start time and end time are required")
        
        # Parse date if string
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            date_obj = date
        
        # Validate date
        validate_date_obj(date_obj)
        
        # Calculate duration
        duration = calculate_duration(start_time, end_time)
        
        sql = """
            UPDATE exams
            SET title = %s, exam_code = %s, date = %s, start_time = %s, end_time = %s, duration = %s, status = %s
            WHERE id = %s
            RETURNING id, title, exam_code, date, start_time, end_time, duration, status;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (title, exam_code, date, start_time, end_time, duration, status, exam_id))
                row = cur.fetchone()

        if not row:
            raise ValueError(f"Exam with id {exam_id} not found")
        
        return row

    def get_exam(self, exam_id: int):
        sql = """
            SELECT id, title, exam_code, date, start_time, end_time, duration, status
            FROM exams
            WHERE id = %s;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_id,))
                row = cur.fetchone()

        return row

    def get_all_exams(self):
        sql = """
            SELECT id, title, exam_code, date, start_time, end_time, duration, status
            FROM exams
            ORDER BY date, start_time;
        """
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return rows

    def delete_exam(self, exam_id: int):
        sql = "DELETE FROM exams WHERE id = %s RETURNING id;"
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_id,))
                row = cur.fetchone()
        
        if not row:
            raise ValueError(f"Exam with id {exam_id} not found")
        
        return row


    def get_exam_duration_by_code(self, exam_code: str) -> dict:
        from datetime import datetime, timedelta, timezone

        MALAYSIA_TZ = timezone(timedelta(hours=8))

        sql = """
            SELECT date, start_time, end_time, duration
            FROM exams
            WHERE exam_code = %s
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_code,))
                row = cur.fetchone()

        if not row:
            raise ValueError("Exam not found")

        # 1. Extract raw values
        exam_date = row["date"]
        start_time = row["start_time"]
        end_time = row["end_time"]
        duration_minutes = row["duration"]

        # 2. Convert to Python date/time if needed
        if isinstance(exam_date, str):
            exam_date = datetime.strptime(exam_date, "%Y-%m-%d").date()

        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()

        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%H:%M:%S").time()

        # 3. Combine into Malaysia timezone datetime
        start_dt = datetime.combine(exam_date, start_time, MALAYSIA_TZ)
        end_dt   = datetime.combine(exam_date, end_time, MALAYSIA_TZ)
        now      = datetime.now(MALAYSIA_TZ)

        # 4. Calculate
        duration_seconds = int((end_dt - start_dt).total_seconds())
        remaining_seconds = max(int((end_dt - now).total_seconds()), 0)

        return {
            "duration_seconds": duration_seconds,
            "remaining_seconds": remaining_seconds,
            "date": exam_date.isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

    def get_questions_by_exam_code(self, exam_code: str):

        sql_exam = """
            SELECT id 
            FROM exams 
            WHERE exam_code = %s
        """

        sql_questions = """
            SELECT id, question_text, question_type, marks
            FROM question
            WHERE exam_id = %s
            ORDER BY id
        """

        sql_options = """
            SELECT id, option_text
            FROM "questionOption"
            WHERE question_id = %s
            ORDER BY id
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:

                # Get exam ID
                cur.execute(sql_exam, (exam_code,))
                exam = cur.fetchone()
                if not exam:
                    raise ValueError("Exam not found")

                exam_id = exam["id"]

                # Get all questions
                cur.execute(sql_questions, (exam_id,))
                questions = cur.fetchall()

                # Get options for each question
                for q in questions:
                    cur.execute(sql_options, (q["id"],))
                    q["options"] = cur.fetchall()

        return {"questions": questions}

    def _get_exam_id_by_code(self, cursor, exam_code: str) -> int:
        """Get exam ID from exam code"""
        sql = "SELECT id FROM exams WHERE exam_code = %s"
        cursor.execute(sql, (exam_code,))
        exam = cursor.fetchone()
        if not exam:
            raise ValueError(f"Exam with code '{exam_code}' not found")
        return exam["id"]


    def _create_submission_record(self, cursor, exam_id: int, user_id: int) -> int:
        """Create initial submission record and return submission_id"""
        now = datetime.now()
        
        sql = """
            INSERT INTO submission (exam_code, user_id, submission_date, submission_time, status, score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cursor.execute(sql, (
            exam_id,
            user_id,
            now.date(),
            now.time(),
            "pending",
            0
        ))
        
        result = cursor.fetchone()
        return result["id"]


    def _get_question_details(self, cursor, question_id: int, exam_id: int) -> dict:
        """Get question type and marks"""
        sql = """
            SELECT id, question_type, marks 
            FROM question 
            WHERE id = %s AND exam_id = %s
        """
        
        cursor.execute(sql, (question_id, exam_id))
        question = cursor.fetchone()
        
        if not question:
            raise ValueError(f"Question {question_id} not found for this exam")
        
        return question


    def _get_correct_option_id(self, cursor, question_id: int) -> int:
        """Get the correct option ID for an MCQ question"""
        sql = """
            SELECT id 
            FROM "questionOption" 
            WHERE question_id = %s AND is_correct = true
        """
        
        cursor.execute(sql, (question_id,))
        correct_option = cursor.fetchone()
        
        if not correct_option:
            raise ValueError(f"No correct answer set for question {question_id}")
        
        return correct_option["id"]


    def _create_submission_answer(self, cursor, submission_id: int, question_id: int, 
                                selected_option_id: int = None, score: int = None, 
                                feedback: str = None) -> int:
        """Create submissionAnswer record and return its ID"""
        sql = """
            INSERT INTO "submissionAnswer" 
            (submission_id, question_id, selected_option_id, score, feedback)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cursor.execute(sql, (submission_id, question_id, selected_option_id, score, feedback))
        result = cursor.fetchone()
        return result["id"]


    def _save_mcq_answer(self, cursor, submission_answer_id: int, selected_option_id: int):
        """Save MCQ answer to mcqAnswer table"""
        sql = """
            INSERT INTO "mcqAnswer" (submission_answer_id, selected_option_id)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (submission_answer_id, selected_option_id))


    def _save_essay_answer(self, cursor, submission_answer_id: int, essay_text: str):
        """Save essay answer to essayAnswer table"""
        sql = """
            INSERT INTO "essayAnswer" (submission_answer_id, essay_answer)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (submission_answer_id, essay_text))


    def _process_mcq_answer(self, cursor, submission_id: int, question_id: int, 
                            selected_option_id: int, marks: int) -> dict:
        """
        Process MCQ answer: check correctness, calculate score, save to database
        Returns: dict with score, is_correct, max_score
        """
        # Get correct answer
        correct_option_id = self._get_correct_option_id(cursor, question_id)
        
        # Check if answer is correct
        is_correct = (selected_option_id == correct_option_id)
        score = marks if is_correct else 0
        feedback = "Correct" if is_correct else "Incorrect"
        
        # Create submission answer record
        submission_answer_id = self._create_submission_answer(
            cursor, submission_id, question_id, selected_option_id, score, feedback
        )
        
        # Save to mcqAnswer table
        self._save_mcq_answer(cursor, submission_answer_id, selected_option_id)
        
        return {
            "question_id": question_id,
            "type": "mcq",
            "is_correct": is_correct,
            "score": score,
            "max_score": marks
        }


    def _process_essay_answer(self, cursor, submission_id: int, question_id: int, 
                            essay_text: str, marks: int) -> dict:
        """
        Process essay answer: save to database as pending
        Returns: dict with status and max_score
        """
        # Create submission answer record (no score yet)
        submission_answer_id = self._create_submission_answer(
            cursor, submission_id, question_id, None, None, "Pending teacher review"
        )
        
        # Save to essayAnswer table
        self._save_essay_answer(cursor, submission_answer_id, essay_text)
        
        return {
            "question_id": question_id,
            "type": "essay",
            "status": "pending",
            "max_score": marks
        }


    def _calculate_grade(self, score: int, max_score: int) -> str:
        """Calculate letter grade from score"""
        if max_score == 0:
            return "N/A"
        
        percentage = (score / max_score) * 100
        
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B"
        elif percentage >= 60:
            return "C"
        elif percentage >= 50:
            return "D"
        else:
            return "F"


    def _update_submission_final(self, cursor, submission_id: int, total_score: int, 
                                has_essay: bool, grade: str):
        """Update submission with final score, status, and grade"""
        final_status = "pending" if has_essay else "graded"
        final_grade = "Pending" if has_essay else grade
        
        sql = """
            UPDATE submission 
            SET score = %s, status = %s, score_grade = %s
            WHERE id = %s
        """
        
        cursor.execute(sql, (total_score, final_status, final_grade, submission_id))


    # ===========================
    # MAIN SUBMISSION FUNCTION
    # ===========================

    def submit_exam(self, exam_code: str, user_id: int, answers: list) -> dict:
        """
        Main function to process exam submission
        
        Flow:
        1. Validate exam exists
        2. Create submission record
        3. Process each answer (MCQ or Essay)
        4. Calculate total score
        5. Update submission with final results
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                
                # Step 1: Get exam ID
                exam_id = self._get_exam_id_by_code(cur, exam_code)
                
                # Step 2: Create submission record
                submission_id = self._create_submission_record(cur, exam_id, user_id)
                
                # Step 3: Process all answers
                total_score = 0
                max_score = 0
                has_essay = False
                graded_results = []
                
                for answer_data in answers:
                    question_id = answer_data.question_id
                    answer_value = answer_data.answer
                    
                    # Get question details
                    question = self._get_question_details(cur, question_id, exam_id)
                    question_type = question["question_type"].lower()
                    marks = question["marks"]
                    max_score += marks
                    
                    # Process based on question type
                    if question_type == "mcq":
                        selected_option_id = int(answer_value)
                        result = self._process_mcq_answer(
                            cur, submission_id, question_id, selected_option_id, marks
                        )
                        total_score += result["score"]
                        graded_results.append(result)
                        
                    elif question_type == "essay":
                        has_essay = True
                        essay_text = str(answer_value)
                        result = self._process_essay_answer(
                            cur, submission_id, question_id, essay_text, marks
                        )
                        graded_results.append(result)
                
                # Step 4: Calculate grade
                grade = self._calculate_grade(total_score, max_score)
                
                # Step 5: Update submission with final results
                self._update_submission_final(cur, submission_id, total_score, has_essay, grade)
                
                # Commit transaction
                conn.commit()
        
        # Return results
        return {
            "submission_id": submission_id,
            "status": "pending" if has_essay else "graded",
            "total_score": total_score,
            "max_score": max_score,
            "grade": "Pending" if has_essay else grade,
            "message": (
                "Exam submitted successfully. Essays are pending teacher review." 
                if has_essay 
                else "Exam submitted and graded successfully."
            ),
            "results": graded_results
        }