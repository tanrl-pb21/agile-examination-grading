from src.db import get_conn
from psycopg.rows import dict_row


class ExamService:

    def add_exam(self, title, start_time, end_time):
        if not title:
            raise ValueError("Title is required")

        sql = """
            INSERT INTO exams (title, start_time, end_time)
            VALUES (%s, %s, %s)
            RETURNING id, title, start_time, end_time;
        """

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (title, start_time, end_time))
                row = cur.fetchone()

        return row

    def get_exam(self, exam_id: int):
        sql = """
            SELECT id, title, start_time, end_time
            FROM exams
            WHERE id = %s;
        """

        with get_conn() as conn:
            row = conn.execute(sql, (exam_id,)).fetchone()

        return row
