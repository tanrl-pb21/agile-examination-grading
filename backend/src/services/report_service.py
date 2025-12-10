from src.db import get_conn
from psycopg.rows import dict_row
from typing import List, Dict, Optional
import math


class ReportsService:
    """Service for generating exam performance reports and statistics"""

    def get_completed_exams(self, instructor_id: int = None) -> List[dict]:
        """
        Get all completed exams with basic statistics.
        If instructor_id is provided, only shows exams from courses assigned to that instructor.
        """
        # Base query
        sql = """
            SELECT 
                e.id,
                e.title,
                e.exam_code,
                e.date,
                c.course_name,
                c.course_code,
                COUNT(DISTINCT sc.student_id) as total_students,
                COUNT(DISTINCT CASE WHEN s.status IN ('pending', 'graded') THEN s.id END) as submitted,
                COUNT(DISTINCT CASE WHEN s.status = 'graded' THEN s.id END) as graded,
                COALESCE(AVG(CASE WHEN s.score IS NOT NULL THEN s.score END), 0) as average_score
            FROM exams e
            LEFT JOIN course c ON e.course = c.id
            LEFT JOIN "studentCourse" sc ON sc.course_id = e.course
            LEFT JOIN submission s ON s.exam_code = e.id AND s.user_id = sc.student_id
            WHERE e.status = 'completed'
        """
        
        params = []
        
        # Add instructor filter if instructor_id is provided
        if instructor_id:
            sql += """
                AND c.id IN (
                    SELECT course_id 
                    FROM "intrcutorCourse" 
                    WHERE intructor_id = %s
                )
            """
            params.append(instructor_id)
        
        sql += """
            GROUP BY e.id, e.title, e.exam_code, e.date, c.course_name, c.course_code
            ORDER BY e.date DESC
        """

        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()

            if rows:
                for row in rows:
                    row["average_score"] = round(float(row["average_score"]), 2)

            return rows if rows else []

        except Exception as e:
            print(f"ERROR in get_completed_exams: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_exam_student_scores(self, exam_id: int, instructor_id: int = None) -> List[dict]:
        """
        Get individual student scores for a specific exam.
        If instructor_id is provided, ensures instructor has access to this course.
        """
        # Base query
        sql = """
            SELECT 
                u.id as student_id,
                u.user_email,
                u.student_id as student_number,
                s.score,
                s.score_grade,
                s.status,
                s.submission_date
            FROM "studentCourse" sc
            INNER JOIN "user" u ON u.id = sc.student_id
            INNER JOIN exams e ON e.course = sc.course_id
            LEFT JOIN submission s ON s.exam_code = e.id AND s.user_id = sc.student_id
            WHERE e.id = %s
        """
        
        params = [exam_id]
        
        # Add instructor filter if instructor_id is provided
        if instructor_id:
            sql += """
                AND e.course IN (
                    SELECT course_id 
                    FROM "intrcutorCourse" 
                    WHERE intructor_id = %s
                )
            """
            params.append(instructor_id)
        
        sql += """
            ORDER BY 
                CASE WHEN s.status = 'graded' THEN 1
                     WHEN s.status = 'pending' THEN 2
                     ELSE 3 END,
                u.user_email
        """

        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()

            return rows if rows else []

        except Exception as e:
            print(f"ERROR in get_exam_student_scores: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_exam_performance_stats(self, exam_id: int, instructor_id: int = None) -> Optional[dict]:
        """
        Get detailed performance statistics for a specific exam.
        If instructor_id is provided, ensures instructor has access to this course.
        """
        try:
            # Get exam details with instructor check
            sql_exam = """
                SELECT 
                    e.id,
                    e.title,
                    e.exam_code,
                    e.date,
                    c.course_name,
                    c.course_code,
                    COALESCE(SUM(q.marks), 0) as total_points
                FROM exams e
                LEFT JOIN course c ON e.course = c.id
                LEFT JOIN question q ON q.exam_id = e.id
                WHERE e.id = %s
            """
            
            params = [exam_id]
            
            # Add instructor filter if instructor_id is provided
            if instructor_id:
                sql_exam += """
                    AND c.id IN (
                        SELECT course_id 
                        FROM "intrcutorCourse" 
                        WHERE intructor_id = %s
                    )
                """
                params.append(instructor_id)
            
            sql_exam += " GROUP BY e.id, e.title, e.exam_code, e.date, c.course_name, c.course_code"

            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql_exam, params)
                    exam = cur.fetchone()

            if not exam:
                return None  # Exam not found or instructor doesn't have access

            total_points = exam["total_points"]

            # Get statistics
            sql_stats = """
                WITH student_submissions AS (
                    SELECT 
                        sc.student_id,
                        s.score,
                        s.score_grade,
                        s.status
                    FROM "studentCourse" sc
                    INNER JOIN exams e ON e.course = sc.course_id
                    LEFT JOIN submission s ON s.exam_code = e.id AND s.user_id = sc.student_id
                    WHERE e.id = %s
                )
                SELECT 
                    COUNT(DISTINCT student_id) as total_students,
                    COUNT(CASE WHEN status IN ('pending', 'graded') THEN 1 END) as submitted,
                    COUNT(CASE WHEN status = 'graded' THEN 1 END) as graded,
                    COALESCE(AVG(CASE WHEN score IS NOT NULL THEN score END), 0) as average_score,
                    COALESCE(MAX(score), 0) as highest_score,
                    COALESCE(MIN(score), 0) as lowest_score
                FROM student_submissions
            """

            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql_stats, (exam_id,))
                    stats = cur.fetchone()

            # Get grade distribution
            sql_grades = """
                SELECT 
                    s.score_grade,
                    COUNT(*) as count
                FROM "studentCourse" sc
                INNER JOIN exams e ON e.course = sc.course_id
                INNER JOIN submission s ON s.exam_code = e.id AND s.user_id = sc.student_id
                WHERE e.id = %s 
                  AND s.status = 'graded'
                  AND s.score_grade IS NOT NULL
                GROUP BY s.score_grade
                ORDER BY 
                    CASE s.score_grade
                        WHEN 'A+' THEN 1
                        WHEN 'A' THEN 2
                        WHEN 'A-' THEN 3
                        WHEN 'B+' THEN 4
                        WHEN 'B' THEN 5
                        WHEN 'B-' THEN 6
                        WHEN 'C+' THEN 7
                        WHEN 'C' THEN 8
                        WHEN 'C-' THEN 9
                        WHEN 'D' THEN 10
                        WHEN 'F' THEN 11
                        WHEN 'Pending' THEN 12
                        ELSE 13
                    END
            """

            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql_grades, (exam_id,))
                    grade_rows = cur.fetchall()

            # Calculate pass rate
            sql_passed = """
                SELECT COUNT(*) as passed_count
                FROM "studentCourse" sc
                INNER JOIN exams e ON e.course = sc.course_id
                INNER JOIN submission s ON s.exam_code = e.id AND s.user_id = sc.student_id
                WHERE e.id = %s 
                  AND s.status = 'graded'
                  AND s.score >= %s
            """
            
            passing_threshold = total_points * 0.5 if total_points > 0 else 0
            
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql_passed, (exam_id, passing_threshold))
                    passed_result = cur.fetchone()
            
            passed_count = passed_result["passed_count"] if passed_result else 0
            pass_rate = round((passed_count / stats["graded"] * 100), 2) if stats["graded"] > 0 else 0

            # Get score ranges (percentage based)
            sql_score_ranges = """
                WITH score_percentages AS (
                    SELECT 
                        (s.score * 100.0 / NULLIF(%s, 0)) as percentage
                    FROM "studentCourse" sc
                    INNER JOIN exams e ON e.course = sc.course_id
                    INNER JOIN submission s ON s.exam_code = e.id AND s.user_id = sc.student_id
                    WHERE e.id = %s 
                      AND s.status = 'graded'
                      AND s.score IS NOT NULL
                )
                SELECT 
                    COUNT(CASE WHEN percentage BETWEEN 90 AND 100 THEN 1 END) as range_90_100,
                    COUNT(CASE WHEN percentage BETWEEN 80 AND 89.99 THEN 1 END) as range_80_89,
                    COUNT(CASE WHEN percentage BETWEEN 70 AND 79.99 THEN 1 END) as range_70_79,
                    COUNT(CASE WHEN percentage BETWEEN 60 AND 69.99 THEN 1 END) as range_60_69,
                    COUNT(CASE WHEN percentage BETWEEN 50 AND 59.99 THEN 1 END) as range_50_59,
                    COUNT(CASE WHEN percentage BETWEEN 40 AND 49.99 THEN 1 END) as range_40_49,
                    COUNT(CASE WHEN percentage BETWEEN 30 AND 39.99 THEN 1 END) as range_30_39,
                    COUNT(CASE WHEN percentage BETWEEN 20 AND 29.99 THEN 1 END) as range_20_29,
                    COUNT(CASE WHEN percentage BETWEEN 10 AND 19.99 THEN 1 END) as range_10_19,
                    COUNT(CASE WHEN percentage BETWEEN 0 AND 9.99 THEN 1 END) as range_0_9
                FROM score_percentages
            """

            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql_score_ranges, (total_points, exam_id))
                    ranges_result = cur.fetchone()

            # Build grade distribution
            grade_distribution = []
            all_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "Pending"]
            
            grade_data = {row["score_grade"]: row["count"] for row in grade_rows}
            
            for grade in all_grades:
                count = grade_data.get(grade, 0)
                percentage = round((count / stats["graded"] * 100), 2) if stats["graded"] > 0 else 0
                grade_distribution.append({
                    "grade": grade,
                    "count": count,
                    "percentage": percentage
                })

            # Build score ranges
            score_ranges = []
            range_labels = ["90-100", "80-89", "70-79", "60-69", "50-59", 
                           "40-49", "30-39", "20-29", "10-19", "0-9"]
            range_fields = ["range_90_100", "range_80_89", "range_70_79", "range_60_69", "range_50_59",
                          "range_40_49", "range_30_39", "range_20_29", "range_10_19", "range_0_9"]
            
            for label, field in zip(range_labels, range_fields):
                count = ranges_result[field] if ranges_result else 0
                percentage = round((count / stats["graded"] * 100), 2) if stats["graded"] > 0 else 0
                score_ranges.append({
                    "range": label,
                    "count": count,
                    "percentage": percentage
                })

            return {
                "exam_info": {
                    "id": exam["id"],
                    "title": exam["title"],
                    "exam_code": exam["exam_code"],
                    "date": exam["date"],
                    "course_name": exam["course_name"],
                    "course_code": exam["course_code"],
                    "total_points": total_points
                },
                "statistics": {
                    "total_students": stats["total_students"],
                    "submitted": stats["submitted"],
                    "graded": stats["graded"],
                    "average_score": round(float(stats["average_score"]), 2),
                    "highest_score": stats["highest_score"],
                    "lowest_score": stats["lowest_score"],
                    "pass_rate": pass_rate
                },
                "grade_distribution": grade_distribution,
                "score_ranges": score_ranges
            }

        except Exception as e:
            print(f"ERROR in get_exam_performance_stats: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def get_instructor_courses(self, instructor_id: int) -> List[dict]:
        """
        Get all courses assigned to an instructor.
        """
        sql = """
            SELECT 
                c.id,
                c.course_code,
                c.course_name,
                c.description,
                c.status,
                COUNT(DISTINCT sc.student_id) as student_count,
                COUNT(DISTINCT e.id) as exam_count
            FROM "intrcutorCourse" ic
            INNER JOIN course c ON ic.course_id = c.id
            LEFT JOIN "studentCourse" sc ON sc.course_id = c.id
            LEFT JOIN exams e ON e.course = c.id
            WHERE ic.intructor_id = %s
            GROUP BY c.id, c.course_code, c.course_name, c.description, c.status
            ORDER BY c.course_code
        """
        
        try:
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (instructor_id,))
                    rows = cur.fetchall()
            
            return rows if rows else []
            
        except Exception as e:
            print(f"ERROR in get_instructor_courses: {str(e)}")
            import traceback
            traceback.print_exc()
            return []