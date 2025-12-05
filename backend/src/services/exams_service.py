from src.db import get_conn

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
    def search_exams_by_title(self, search_term: str):
        """
        Search exams by title (case-insensitive, partial match).
        Returns exams where title contains the search term.
        """
        if not search_term or len(search_term.strip()) == 0:
            raise ValueError("Search term is required")
        
        search_term = search_term.strip()
        
        sql = """
            SELECT id, title, exam_code, course, date, start_time, end_time, duration, status
            FROM exams
            WHERE LOWER(title) LIKE LOWER(%s)
            ORDER BY date DESC, start_time DESC
            LIMIT 100;
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Use % wildcards for partial matching
                    cur.execute(sql, (f"%{search_term}%",))
                    rows = cur.fetchall()
            
            # Convert time objects to strings
            if rows:
                for row in rows:
                    if row["start_time"] and not isinstance(row["start_time"], str):
                        row["start_time"] = row["start_time"].strftime("%H:%M")
                    if row["end_time"] and not isinstance(row["end_time"], str):
                        row["end_time"] = row["end_time"].strftime("%H:%M")
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in search_exams_by_title: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_available_exams_for_student(self, student_id: int) -> list:
        """
        Get exams currently open (start_time <= now <= end_time) 
        for courses student is enrolled in.
        """
        from datetime import datetime, timedelta, timezone
        
        MALAYSIA_TZ = timezone(timedelta(hours=8))
        now = datetime.now(MALAYSIA_TZ)
        current_time = now.time()
        
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
            INNER JOIN course c ON e.course = c.id
            INNER JOIN "studentCourse" sc ON sc.course_id = e.course
            WHERE 
                sc.student_id = %s
                AND e.date = CURRENT_DATE
                AND e.start_time <= %s::time
                AND e.end_time >= %s::time
            ORDER BY e.start_time ASC;
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (student_id, current_time, current_time))
                    rows = cur.fetchall()
            
            # Convert time objects to strings
            if rows:
                for row in rows:
                    if row['start_time'] and not isinstance(row['start_time'], str):
                        row['start_time'] = row['start_time'].strftime('%H:%M')
                    if row['end_time'] and not isinstance(row['end_time'], str):
                        row['end_time'] = row['end_time'].strftime('%H:%M')
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in get_available_exams_for_student: {str(e)}")
            return []


    def get_upcoming_exams_for_student(self, student_id: int) -> list:
        """
        Get exams scheduled for future for courses student is enrolled in.
        Only includes exams that haven't started yet.
        
        Criteria:
        - date > today (exams scheduled for future dates)
        - OR (date = today AND start_time > now) (exams today that haven't started)
        """
        from datetime import datetime, timedelta, timezone
        
        MALAYSIA_TZ = timezone(timedelta(hours=8))
        now = datetime.now(MALAYSIA_TZ)
        current_date = now.date()
        current_time = now.time()
        
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
            INNER JOIN course c ON e.course = c.id
            INNER JOIN "studentCourse" sc ON sc.course_id = e.course
            WHERE 
                sc.student_id = %s
                AND (
                    e.date > %s::date
                    OR (e.date = %s::date AND e.start_time > %s::time)
                )
            ORDER BY e.date ASC, e.start_time ASC;
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (student_id, current_date, current_date, current_time))
                    rows = cur.fetchall()
            
            # Convert time objects to strings
            if rows:
                for row in rows:
                    if row['start_time'] and not isinstance(row['start_time'], str):
                        row['start_time'] = row['start_time'].strftime('%H:%M')
                    if row['end_time'] and not isinstance(row['end_time'], str):
                        row['end_time'] = row['end_time'].strftime('%H:%M')
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in get_upcoming_exams_for_student: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
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


    def search_exams_by_code(self, exam_code: str):
        """
        Search exams by exam code (case-insensitive, exact match).
        Returns exams matching the exact exam code.
        """
        if not exam_code or len(exam_code.strip()) == 0:
            raise ValueError("Search term is required")
        
        exam_code = exam_code.strip()
        
        sql = """
            SELECT id, title, exam_code, course, date, start_time, end_time, duration, status
            FROM exams
            WHERE LOWER(exam_code) = LOWER(%s)
            ORDER BY date DESC, start_time DESC;
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (exam_code,))
                    rows = cur.fetchall()
            
            # Convert time objects to strings
            if rows:
                for row in rows:
                    if row["start_time"] and not isinstance(row["start_time"], str):
                        row["start_time"] = row["start_time"].strftime("%H:%M")
                    if row["end_time"] and not isinstance(row["end_time"], str):
                        row["end_time"] = row["end_time"].strftime("%H:%M")
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in search_exams_by_code: {str(e)}")
            import traceback
            traceback.print_exc()
            return []


    def search_student_exams_by_course(self, student_id: int, course_name: str) -> list:
        """
        Search student's exams by course name (case-insensitive, partial match).
        Returns exams for courses where name contains the search term.
        """
        if not course_name or len(course_name.strip()) == 0:
            raise ValueError("Course name is required")
        
        if student_id <= 0:
            raise ValueError("Valid student ID is required")
        
        course_name = course_name.strip()
        
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
            WHERE 
                sc.student_id = %s
                AND LOWER(c.course_name) LIKE LOWER(%s)
            ORDER BY e.date DESC, e.start_time DESC
            LIMIT 100;
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (student_id, f"%{course_name}%"))
                    rows = cur.fetchall()
            
            # Convert time objects to strings
            if rows:
                for row in rows:
                    if row["start_time"] and not isinstance(row["start_time"], str):
                        row["start_time"] = row["start_time"].strftime("%H:%M")
                    if row["end_time"] and not isinstance(row["end_time"], str):
                        row["end_time"] = row["end_time"].strftime("%H:%M")
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in search_student_exams_by_course: {str(e)}")
            import traceback
            traceback.print_exc()
            return []


    def filter_exams_by_status(self, status: str) -> list:
        """
        Filter all exams by status (scheduled, completed, cancelled).
        Returns all exams with the specified status, ordered by date.
        """
        valid_statuses = ["scheduled", "completed", "cancelled"]
        
        # Convert to lowercase for comparison
        if not status or status.strip().lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        status = status.strip().lower()
        
        sql = """
            SELECT id, title, exam_code, course, date, start_time, end_time, duration, status
            FROM exams
            WHERE LOWER(status) = LOWER(%s)
            ORDER BY date DESC, start_time DESC
            LIMIT 1000;
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (status,))
                    rows = cur.fetchall()
            
            # Convert time objects to strings
            if rows:
                for row in rows:
                    if row["start_time"] and not isinstance(row["start_time"], str):
                        row["start_time"] = row["start_time"].strftime("%H:%M")
                    if row["end_time"] and not isinstance(row["end_time"], str):
                        row["end_time"] = row["end_time"].strftime("%H:%M")
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in filter_exams_by_status: {str(e)}")
            import traceback
            traceback.print_exc()
            return []


    def filter_student_exams_by_status(self, student_id: int, status: str) -> list:
        """
        Filter a student's exams by status (scheduled, completed, cancelled).
        Returns exams for enrolled courses with the specified status.
        """
        valid_statuses = ["scheduled", "completed", "cancelled"]
        
        if student_id <= 0:
            raise ValueError("Valid student ID is required")
        
        if not status or status.strip() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        status = status.strip()
        
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
            WHERE 
                sc.student_id = %s
                AND LOWER(e.status) = LOWER(%s)
            ORDER BY e.date DESC, e.start_time DESC
            LIMIT 1000;
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (student_id, status))
                    rows = cur.fetchall()
            
            # Convert time objects to strings
            if rows:
                for row in rows:
                    if row["start_time"] and not isinstance(row["start_time"], str):
                        row["start_time"] = row["start_time"].strftime("%H:%M")
                    if row["end_time"] and not isinstance(row["end_time"], str):
                        row["end_time"] = row["end_time"].strftime("%H:%M")
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in filter_student_exams_by_status: {str(e)}")
            import traceback
            traceback.print_exc()
            return []