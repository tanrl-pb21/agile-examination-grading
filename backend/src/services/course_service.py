from src.db import get_conn
from psycopg.rows import dict_row


class CourseService:

    def get_all_courses(self):
        sql = """
            SELECT id, course_name, course_code, description
            FROM course
            ORDER BY course_name;
        """
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql)
                courses = cur.fetchall()
        return courses
