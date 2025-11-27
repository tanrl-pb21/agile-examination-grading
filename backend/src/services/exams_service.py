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
        raise ValueError("Exam code can only contain letters, numbers, hyphens, and underscores")
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
        start1 = start1.strftime('%H:%M') if hasattr(start1, 'strftime') else str(start1)
    if not isinstance(end1, str):
        end1 = end1.strftime('%H:%M') if hasattr(end1, 'strftime') else str(end1)
    if not isinstance(start2, str):
        start2 = start2.strftime('%H:%M') if hasattr(start2, 'strftime') else str(start2)
    if not isinstance(end2, str):
        end2 = end2.strftime('%H:%M') if hasattr(end2, 'strftime') else str(end2)
    
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
    
    def check_exam_conflicts(self, course_id, exam_date, start_time, end_time, exclude_exam_id=None):
        """
        Check if adding an exam creates scheduling conflicts.
        
        A conflict occurs if:
        1. ANY student is enrolled in the new course
        2. That SAME student is also in another course that has an exam at the overlapping time
        
        OR: Any student in this course is taking another exam at the same time (same or different course)
        """
        try:
            # Convert course_id to int if needed
            course_id = int(course_id)
            
            # Query: Find any exams that overlap with the new exam time on the same date
            # for courses where students from this course are also enrolled
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
                WHERE 
                    e.date = %s
                    AND e.start_time < %s
                    AND e.end_time > %s
                    AND EXISTS (
                        SELECT 1 FROM "studentCourse" sc1
                        WHERE sc1.course_id = %s
                        AND sc1.student_id IN (
                            SELECT student_id FROM "studentCourse" sc2
                            WHERE sc2.course_id = e.course
                        )
                    )
            """
            
            params = [exam_date, end_time, start_time, course_id]
            
            if exclude_exam_id:
                sql_conflicts += " AND e.id != %s"
                params.append(exclude_exam_id)
            
            sql_conflicts += " LIMIT 1;"
            
            print(f"DEBUG: Checking conflicts for course {course_id} on {exam_date} from {start_time} to {end_time}")
            
            with get_conn() as conn:
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
            
            print(f"DEBUG: No conflicts found")
        
        except ValueError:
            raise
        except Exception as e:
            # Log the error but don't fail the exam creation due to conflict checking
            print(f"Error checking exam conflicts: {str(e)}")
            import traceback
            traceback.print_exc()
            return

    def add_exam(self, title, exam_code, course, date, start_time, end_time, status='scheduled'):
        """Add a new exam with full validation"""
        # Validate all inputs
        title = validate_title(title)
        exam_code = validate_exam_code(exam_code)
        
        if not course:
            raise ValueError("Course is required")
        
        if not start_time or not end_time:
            raise ValueError("Start time and end time are required")
        
        if not date:
            raise ValueError("Date is required")
        
        if status not in ['scheduled', 'completed', 'cancelled']:
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
        
        # Check for exam conflicts
        self.check_exam_conflicts(course, date_obj, start_time, end_time)
        
        sql = """
            INSERT INTO exams (title, exam_code, course, date, start_time, end_time, duration, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, exam_code, course, date, start_time, end_time, duration, status;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (title, exam_code, course, date_obj, start_time, end_time, duration, status))
                row = cur.fetchone()
                return row

    def update_exam(self, exam_id, title, exam_code, course, date, start_time, end_time, status='scheduled'):
        """Update an existing exam with full validation"""
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
        
        if status not in ['scheduled', 'completed', 'cancelled']:
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
        
        # Check for exam conflicts (excluding this exam from conflict check)
        self.check_exam_conflicts(course, date_obj, start_time, end_time, exclude_exam_id=exam_id)
        
        sql = """
            UPDATE exams
            SET title = %s, exam_code = %s, course = %s, date = %s, start_time = %s, end_time = %s, duration = %s, status = %s
            WHERE id = %s
            RETURNING id, title, exam_code, course, date, start_time, end_time, duration, status;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (title, exam_code, course, date_obj, start_time, end_time, duration, status, exam_id))
                row = cur.fetchone()

        if not row:
            raise ValueError(f"Exam with id {exam_id} not found")
        
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
        """Get all exams ordered by date and start time"""
        sql = """
            SELECT id, title, exam_code, course, date, start_time, end_time, duration, status
            FROM exams
            ORDER BY date, start_time;
        """
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        
        # Convert time objects to HH:MM string format
        if rows:
            for row in rows:
                if row['start_time'] and not isinstance(row['start_time'], str):
                    row['start_time'] = row['start_time'].strftime('%H:%M')
                if row['end_time'] and not isinstance(row['end_time'], str):
                    row['end_time'] = row['end_time'].strftime('%H:%M')
        
        return rows if rows else []

    def get_student_exams(self, student_id: int):
        """
        Get all exams for courses that a student is enrolled in.
        """
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
            ORDER BY e.date, e.start_time;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (student_id,))
                rows = cur.fetchall()
        
        # Convert time objects to HH:MM string format
        if rows:
            for row in rows:
                if row['start_time'] and not isinstance(row['start_time'], str):
                    row['start_time'] = row['start_time'].strftime('%H:%M')
                if row['end_time'] and not isinstance(row['end_time'], str):
                    row['end_time'] = row['end_time'].strftime('%H:%M')
        
        return rows if rows else []

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
        
        return row