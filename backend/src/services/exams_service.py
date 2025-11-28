from src.db import get_conn
from psycopg.rows import dict_row
from datetime import datetime, date, time
import re


def validate_date_obj(dt: date):
    if dt.year < 1900 or dt.year > 2100:
        raise ValueError("Year must be between 1900 and 2100")
    if dt < date.today():
        raise ValueError("Exam date cannot be in the past")
    return dt


def validate_exam_code(exam_code: str):
    """Validate exam code format and length"""
    if not exam_code or len(exam_code.strip()) == 0:
        raise ValueError("Exam code is required")
    if len(exam_code) > 50:
        raise ValueError("Exam code must be 50 characters or less")
    if not re.match(r"^[A-Za-z0-9\-_]+$", exam_code):
        raise ValueError(
            "Exam code can only contain letters, numbers, hyphens, and underscores"
        )
    return exam_code.strip()


def validate_title(title: str):
    """Validate exam title"""
    if not title or len(title.strip()) == 0:
        raise ValueError("Title is required")
    if len(title) > 255:
        raise ValueError("Title must be 255 characters or less")
    return title.strip()


def calculate_duration(start_time_str: str, end_time_str: str) -> int:
    """Calculate duration in minutes between two time strings (HH:MM format)"""
    start = datetime.strptime(start_time_str, "%H:%M").time()
    end = datetime.strptime(end_time_str, "%H:%M").time()

    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute

    duration = end_minutes - start_minutes
    if duration < 0:
        raise ValueError("End time must be after start time")
    if duration == 0:
        raise ValueError("Exam duration must be greater than 0 minutes")

    return duration


def time_overlap(start1, end1, start2, end2):
    """Check if two time ranges overlap. Times can be strings 'HH:MM' or time objects"""

    # Convert time objects to HH:MM strings if needed
    if not isinstance(start1, str):
        start1 = (
            start1.strftime("%H:%M") if hasattr(start1, "strftime") else str(start1)
        )
    if not isinstance(end1, str):
        end1 = end1.strftime("%H:%M") if hasattr(end1, "strftime") else str(end1)
    if not isinstance(start2, str):
        start2 = (
            start2.strftime("%H:%M") if hasattr(start2, "strftime") else str(start2)
        )
    if not isinstance(end2, str):
        end2 = end2.strftime("%H:%M") if hasattr(end2, "strftime") else str(end2)

    # Now parse as datetime strings
    start1_dt = datetime.strptime(start1, "%H:%M")
    end1_dt = datetime.strptime(end1, "%H:%M")
    start2_dt = datetime.strptime(start2, "%H:%M")
    end2_dt = datetime.strptime(end2, "%H:%M")

    # Times overlap if: max(start1, start2) < min(end1, end2)
    return max(start1_dt, start2_dt) < min(end1_dt, end2_dt)


class ExamService:

    def exam_code_exists(self, exam_code: str, exclude_exam_id: int = None):
        """Check if exam code already exists in database"""
        sql = "SELECT id FROM exams WHERE exam_code = %s"
        params = [exam_code]

        if exclude_exam_id:
            sql += " AND id != %s"
            params.append(exclude_exam_id)

        sql += ";"

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone() is not None

    def check_exam_conflicts(
        self, course_id, exam_date, start_time, end_time, exclude_exam_id=None
    ):
        """
        OPTIMIZED: Check if adding an exam creates scheduling conflicts.
        Uses a simpler, faster query with proper indexing support.
        """
        try:
            course_id = int(course_id)

            # Simplified conflict check with timeout protection
            # Step 1: Get students in this course
            sql_students = """
                SELECT student_id FROM "studentCourse" 
                WHERE course_id = %s
                LIMIT 1000
            """

            with get_conn() as conn:
                # Set statement timeout to prevent hanging (5 seconds)
                with conn.cursor() as cur:
                    try:
                        cur.execute(
                            "SET statement_timeout = '5000'"
                        )  # 5 second timeout
                    except:
                        pass  # Ignore if not supported

                # Get students in this course
                with conn.cursor() as cur:
                    cur.execute(sql_students, (course_id,))
                    students = cur.fetchall()

                if not students:
                    print(
                        f"DEBUG: No students enrolled in course {course_id}, skipping conflict check"
                    )
                    return

                student_ids = [s["student_id"] for s in students]

                # Step 2: Check for conflicting exams
                # Using ANY array for better performance than IN clause
                sql_conflicts = """
                    SELECT DISTINCT 
                        e.id,
                        e.course,
                        e.start_time,
                        e.end_time,
                        c.course_code,
                        c.course_name
                    FROM exams e
                    INNER JOIN course c ON e.course = c.id
                    INNER JOIN "studentCourse" sc ON sc.course_id = e.course
                    WHERE 
                        e.date = %s
                        AND e.start_time < %s
                        AND e.end_time > %s
                        AND sc.student_id = ANY(%s)
                """

                params = [exam_date, end_time, start_time, student_ids]

                if exclude_exam_id:
                    sql_conflicts += " AND e.id != %s"
                    params.append(exclude_exam_id)

                sql_conflicts += " LIMIT 1;"

                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql_conflicts, params)
                    conflict = cur.fetchone()

            if conflict:
                print(f"DEBUG: Conflict found! {conflict}")
                raise ValueError(
                    f"Scheduling conflict: Students in this course already have an exam in "
                    f"{conflict['course_code']} ({conflict['course_name']}) "
                    f"from {conflict['start_time']} to {conflict['end_time']} on {exam_date}"
                )

            print(f"DEBUG: No conflicts found for course {course_id}")

        except ValueError:
            raise
        except Exception as e:
            # Log error but don't fail the exam creation
            print(f"WARNING: Error checking exam conflicts (non-fatal): {str(e)}")
            import traceback

            traceback.print_exc()
            # Don't raise - allow exam creation to proceed
            return

    def add_exam(
        self, title, exam_code, course, date, start_time, end_time, status="scheduled"
    ):
        """Add a new exam with full validation"""
        print(f"🔍 add_exam called: {title}, {exam_code}, course={course}")

        # Validate all inputs
        title = validate_title(title)
        exam_code = validate_exam_code(exam_code)

        if not course:
            raise ValueError("Course is required")

        if not start_time or not end_time:
            raise ValueError("Start time and end time are required")

        if not date:
            raise ValueError("Date is required")

        if status not in ["scheduled", "completed", "cancelled"]:
            raise ValueError("Status must be one of: scheduled, completed, cancelled")

        # Check exam code uniqueness
        if self.exam_code_exists(exam_code):
            raise ValueError(f"Exam code '{exam_code}' already exists")

        # Parse date if string
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            date_obj = date

        # Validate date
        validate_date_obj(date_obj)

        # Calculate duration first to validate times
        duration = calculate_duration(start_time, end_time)

        # Check for exam conflicts (with timeout protection)
        try:
            self.check_exam_conflicts(course, date_obj, start_time, end_time)
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            print(f"WARNING: Conflict check failed but proceeding: {e}")

        sql = """
            INSERT INTO exams (title, exam_code, course, date, start_time, end_time, duration, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, exam_code, course, date, start_time, end_time, duration, status;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    sql,
                    (
                        title,
                        exam_code,
                        course,
                        date_obj,
                        start_time,
                        end_time,
                        duration,
                        status,
                    ),
                )
                row = cur.fetchone()
                print(f"✅ Exam created with id={row['id']}")
                return row

    def update_exam(
        self,
        exam_id,
        title,
        exam_code,
        course,
        date,
        start_time,
        end_time,
        status="scheduled",
    ):
        """Update an existing exam with full validation"""
        print(f"🔍 update_exam called: id={exam_id}, {title}")

        if not exam_id:
            raise ValueError("Exam ID is required")

        # Validate all inputs
        title = validate_title(title)
        exam_code = validate_exam_code(exam_code)

        if not course:
            raise ValueError("Course is required")

        if not start_time or not end_time:
            raise ValueError("Start time and end time are required")

        if not date:
            raise ValueError("Date is required")

        if status not in ["scheduled", "completed", "cancelled"]:
            raise ValueError("Status must be one of: scheduled, completed, cancelled")

        # Check exam code uniqueness (excluding current exam)
        if self.exam_code_exists(exam_code, exclude_exam_id=exam_id):
            raise ValueError(f"Exam code '{exam_code}' already exists")

        # Parse date if string
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            date_obj = date

        # Validate date
        validate_date_obj(date_obj)

        # Calculate duration
        duration = calculate_duration(start_time, end_time)

        # Check for exam conflicts (with timeout protection)
        try:
            self.check_exam_conflicts(
                course, date_obj, start_time, end_time, exclude_exam_id=exam_id
            )
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            print(f"WARNING: Conflict check failed but proceeding: {e}")

        sql = """
            UPDATE exams
            SET title = %s, exam_code = %s, course = %s, date = %s, start_time = %s, end_time = %s, duration = %s, status = %s
            WHERE id = %s
            RETURNING id, title, exam_code, course, date, start_time, end_time, duration, status;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    sql,
                    (
                        title,
                        exam_code,
                        course,
                        date_obj,
                        start_time,
                        end_time,
                        duration,
                        status,
                        exam_id,
                    ),
                )
                row = cur.fetchone()

        if not row:
            raise ValueError(f"Exam with id {exam_id} not found")

        print(f"✅ Exam {exam_id} updated")
        return row

    def get_exam(self, exam_id: int):
        """Get a single exam by ID"""
        if not exam_id or exam_id <= 0:
            raise ValueError("Exam ID must be a positive integer")

        sql = """
            SELECT id, title, exam_code, course, date, start_time, end_time, duration, status
            FROM exams
            WHERE id = %s;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_id,))
                row = cur.fetchone()

        return row

    def get_all_exams(self):
        """Get all exams ordered by date and start time - OPTIMIZED"""
        print("🔍 ExamService.get_all_exams() called")

        sql = """
            SELECT id, title, exam_code, course, date, start_time, end_time, duration, status
            FROM exams
            ORDER BY date DESC, start_time DESC
            LIMIT 1000;
        """

        try:
            with get_conn() as conn:
                print("✅ Database connection obtained")

                # Set statement timeout to prevent hanging
                with conn.cursor() as cur:
                    try:
                        cur.execute(
                            "SET statement_timeout = '5000'"
                        )  # 5 second timeout
                        print("✅ Statement timeout set")
                    except Exception as e:
                        print(f"⚠️ Could not set timeout: {e}")

                with conn.cursor(row_factory=dict_row) as cur:
                    print("🔍 Executing query...")
                    cur.execute(sql)
                    print("🔍 Fetching results...")
                    rows = cur.fetchall()
                    print(f"✅ Query completed. Found {len(rows) if rows else 0} exams")

            # Convert time objects to HH:MM string format
            if rows:
                for row in rows:
                    if row["start_time"] and not isinstance(row["start_time"], str):
                        row["start_time"] = row["start_time"].strftime("%H:%M")
                    if row["end_time"] and not isinstance(row["end_time"], str):
                        row["end_time"] = row["end_time"].strftime("%H:%M")

            print(f"✅ Returning {len(rows) if rows else 0} exams")
            return rows if rows else []

        except Exception as e:
            print(f"❌ ERROR in get_all_exams: {str(e)}")
            import traceback

            traceback.print_exc()
            # Return empty list instead of raising to prevent UI timeout
            return []

    def get_student_exams(self, student_id: int):
        """Get all exams for courses that a student is enrolled in."""
        if not student_id or student_id <= 0:
            raise ValueError("Student ID must be a positive integer")

        sql = """
            SELECT DISTINCT 
                e.id, 
                e.title, 
                e.exam_code, 
                e.course,
                c.course_name,
                c.course_code,
                e.date, 
                e.start_time, 
                e.end_time, 
                e.duration, 
                e.status
            FROM exams e
            INNER JOIN "studentCourse" sc ON e.course = sc.course_id
            INNER JOIN course c ON e.course = c.id
            WHERE sc.student_id = %s
            ORDER BY e.date DESC, e.start_time DESC
            LIMIT 1000;
        """

        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (student_id,))
                    rows = cur.fetchall()

            # Convert time objects to HH:MM string format
            if rows:
                for row in rows:
                    if row["start_time"] and not isinstance(row["start_time"], str):
                        row["start_time"] = row["start_time"].strftime("%H:%M")
                    if row["end_time"] and not isinstance(row["end_time"], str):
                        row["end_time"] = row["end_time"].strftime("%H:%M")

            return rows if rows else []

        except Exception as e:
            print(f"ERROR in get_student_exams: {str(e)}")
            import traceback

            traceback.print_exc()
            return []

    def delete_exam(self, exam_id: int):
        """Delete an exam by ID"""
        if not exam_id or exam_id <= 0:
            raise ValueError("Exam ID must be a positive integer")

        sql = "DELETE FROM exams WHERE id = %s RETURNING id;"

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_id,))
                row = cur.fetchone()

        if not row:
            raise ValueError(f"Exam with id {exam_id} not found")

        print(f"✅ Exam {exam_id} deleted")
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
        end_dt = datetime.combine(exam_date, end_time, MALAYSIA_TZ)
        now = datetime.now(MALAYSIA_TZ)

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
        
    def check_exam_availability(self, exam_code: str):
        from datetime import datetime, timedelta, timezone
        MALAYSIA_TZ = timezone(timedelta(hours=8))

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                sql = """
                    SELECT date, start_time, end_time
                    FROM exams
                    WHERE exam_code = %s
                """
                cur.execute(sql, (exam_code,))
                exam = cur.fetchone()

                if not exam:
                    raise ValueError("Exam not found")

                exam_date = exam["date"]
                start_time = exam["start_time"]
                end_time = exam["end_time"]

                start_dt = datetime.combine(exam_date, start_time, MALAYSIA_TZ)
                end_dt = datetime.combine(exam_date, end_time, MALAYSIA_TZ)
                now = datetime.now(MALAYSIA_TZ)

                if now < start_dt:
                    return {
                        "status": "not_started",
                        "message": f"Exam starts at {start_time.strftime('%H:%M')} on {exam_date}."
                    }

                if now > end_dt:
                    return {
                        "status": "ended",
                        "message": f"Exam ended at {end_time.strftime('%H:%M')} on {exam_date}."
                    }

                return {
                    "status": "available",
                    "message": "Exam is open."
                }

    def check_if_student_submitted(self, exam_code: str, user_id: int) -> bool:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:

                # Get exam ID first
                exam_id = self._get_exam_id_by_code(cur, exam_code)

                # Check if submission exists
                sql = """
                    SELECT id
                    FROM submission
                    WHERE exam_code = %s AND user_id = %s
                    LIMIT 1
                """
                cur.execute(sql, (exam_id, user_id))
                exists = cur.fetchone()

                return exists is not None
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

        cursor.execute(sql, (exam_id, user_id, now.date(), now.time(), "pending", 0))

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

    def _create_submission_answer(
        self,
        cursor,
        submission_id: int,
        question_id: int,
        selected_option_id: int = None,
        score: int = None,
        feedback: str = None,
    ) -> int:
        """Create submissionAnswer record and return its ID"""
        sql = """
            INSERT INTO "submissionAnswer" 
            (submission_id, question_id, selected_option_id, score, feedback)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """

        cursor.execute(
            sql, (submission_id, question_id, selected_option_id, score, feedback)
        )
        result = cursor.fetchone()
        return result["id"]

    def _save_mcq_answer(
        self, cursor, submission_answer_id: int, selected_option_id: int
    ):
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

    def _process_mcq_answer(
        self,
        cursor,
        submission_id: int,
        question_id: int,
        selected_option_id: int,
        marks: int,
    ) -> dict:
        """
        Process MCQ answer: check correctness, calculate score, save to database
        Returns: dict with score, is_correct, max_score
        """
        # Get correct answer
        correct_option_id = self._get_correct_option_id(cursor, question_id)

        # Check if answer is correct
        is_correct = selected_option_id == correct_option_id
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
            "max_score": marks,
        }

    def _process_essay_answer(
        self, cursor, submission_id: int, question_id: int, essay_text: str, marks: int
    ) -> dict:
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
            "max_score": marks,
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

    def _update_submission_final(
        self, cursor, submission_id: int, total_score: int, has_essay: bool, grade: str
    ):
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
    def validate_submission_time(self, exam_code: str):
        """
        Validate that submission is happening within exam time window.
        Raises ValueError if submission is late.
        """
        from datetime import datetime, timedelta, timezone

        MALAYSIA_TZ = timezone(timedelta(hours=8))

        sql = """
            SELECT date, start_time, end_time
            FROM exams
            WHERE exam_code = %s
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_code,))
                exam = cur.fetchone()

        if not exam:
            raise ValueError("Exam not found")

        # Extract exam date and times
        exam_date = exam["date"]
        start_time = exam["start_time"]
        end_time = exam["end_time"]

        # Convert to Python objects if needed
        if isinstance(exam_date, str):
            exam_date = datetime.strptime(exam_date, "%Y-%m-%d").date()

        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()

        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%H:%M:%S").time()

        # Create timezone-aware datetime objects
        start_dt = datetime.combine(exam_date, start_time, MALAYSIA_TZ)
        end_dt = datetime.combine(exam_date, end_time, MALAYSIA_TZ)
        now = datetime.now(MALAYSIA_TZ)

        # Check if submission is before exam start
        if now < start_dt:
            raise ValueError(
                f"Cannot submit exam before start time. "
                f"Exam starts at {start_time.strftime('%H:%M')} on {exam_date.strftime('%Y-%m-%d')}"
            )

        # Check if submission is after exam end
        if now > end_dt:
            time_over = now - end_dt
            minutes_late = int(time_over.total_seconds() / 60)
            raise ValueError(
                f"Submission rejected: The exam ended at {end_time.strftime('%H:%M')}. "
                f"You are {minutes_late} minute(s) late. Late submissions are not accepted."
            )

        # Submission is within valid time window
        print(f"✓ Submission time validated for exam {exam_code}")
        return True

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
                self._update_submission_final(
                    cur, submission_id, total_score, has_essay, grade
                )

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
            "results": graded_results,
        }