from src.db import get_conn
from psycopg.rows import dict_row
from datetime import datetime, date, time


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