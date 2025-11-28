from fastapi import APIRouter, HTTPException
from src.db import get_conn
from psycopg.rows import dict_row
from datetime import datetime

router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.get("/exam/{exam_id}/students")
def get_exam_submissions_with_students(exam_id: int):
    """
    Get all submissions for an exam, including students who are enrolled but haven't submitted
    """
    try:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # First, get the course_id for this exam
                cur.execute("""
                    SELECT course
                    FROM exams
                    WHERE id = %s
                """, (exam_id,))
                
                exam = cur.fetchone()
                if not exam:
                    raise HTTPException(status_code=404, detail="Exam not found")
                
                course_id = exam['course']
                
                # Get all students enrolled in this course
                cur.execute("""
                    SELECT 
                        sc.student_id,
                        u.user_email as student_email,
                        u.user_email as student_name
                    FROM "studentCourse" sc
                    INNER JOIN "user" u ON sc.student_id = u.id
                    WHERE sc.course_id = %s
                """, (course_id,))
                
                enrolled_students = list(cur.fetchall())
                
                # Get all submissions for this exam
                cur.execute("""
                    SELECT 
                        s.id as submission_id,
                        s.user_id as student_id,
                        s.submission_date,
                        s.submission_time,
                        s.status,
                        u.user_email as student_email,
                        u.user_email as student_name
                    FROM submission s
                    INNER JOIN "user" u ON s.user_id = u.id
                    WHERE s.exam_code = %s
                """, (exam_id,))
                
                submissions = list(cur.fetchall())
                
                # Create a set of student IDs who have submitted
                submitted_student_ids = {sub['student_id'] for sub in submissions}
                
                # Create result list
                result = []
                
                # Add all submissions
                for sub in submissions:
                    result.append({
                        'submission_id': sub['submission_id'],
                        'student_id': sub['student_id'],
                        'student_name': sub['student_name'],
                        'student_email': sub['student_email'],
                        'status': sub['status'],
                        'submission_date': sub['submission_date'],
                        'submission_time': sub['submission_time'],
                        'score': None,  # Will be calculated from submissionAnswer if needed
                        'score_grade': None,
                        'overall_feedback': None
                    })
                
                # Add enrolled students who haven't submitted as 'missed'
                for student in enrolled_students:
                    if student['student_id'] not in submitted_student_ids:
                        result.append({
                            'submission_id': None,  # No submission exists
                            'student_id': student['student_id'],
                            'student_name': student['student_name'],
                            'student_email': student['student_email'],
                            'status': 'missed',
                            'submission_date': None,
                            'submission_time': None,
                            'score': None,
                            'score_grade': None,
                            'overall_feedback': None
                        })
                
                return result
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR fetching submissions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam/{exam_id}")
def get_exam_submissions(exam_id: int):
    """
    Get all submissions for a specific exam with student details
    """
    try:
        print(f"🔍 Fetching submissions for exam {exam_id}...")
        
        sql = """
            SELECT 
                s.id as submission_id,
                s.exam_code,
                s.user_id,
                s.submission_date,
                s.submission_time,
                s.score,
                s.score_grade,
                s.overall_feedback,
                s.status,
                u.id as student_id,
                u.user_email as student_email,
                u.user_role,
                u.user_email as student_name
            FROM submission s
            INNER JOIN "user" u ON s.user_id = u.id
            WHERE s.exam_code = %s
            ORDER BY s.submission_date DESC, s.submission_time DESC;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_id,))
                submissions = cur.fetchall()
        
        # Convert time objects to strings
        for sub in submissions:
            if sub.get('submission_time') and not isinstance(sub['submission_time'], str):
                sub['submission_time'] = sub['submission_time'].strftime('%H:%M:%S')
            if sub.get('submission_date') and not isinstance(sub['submission_date'], str):
                sub['submission_date'] = str(sub['submission_date'])
        
        print(f"✅ Found {len(submissions)} submissions")
        return submissions
        
    except Exception as e:
        print(f"❌ ERROR fetching submissions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{submission_id}")
def get_submission(submission_id: int):
    """
    Get a single submission by ID with student details
    """
    try:
        sql = """
            SELECT 
                s.id as submission_id,
                s.exam_code,
                s.user_id,
                s.submission_date,
                s.submission_time,
                s.score,
                s.score_grade,
                s.overall_feedback,
                s.status,
                u.id as student_id,
                u.user_email as student_email,
                u.user_role,
                u.user_email as student_name
            FROM submission s
            INNER JOIN "user" u ON s.user_id = u.id
            WHERE s.id = %s;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (submission_id,))
                submission = cur.fetchone()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Convert time objects to strings
        if submission.get('submission_time') and not isinstance(submission['submission_time'], str):
            submission['submission_time'] = submission['submission_time'].strftime('%H:%M:%S')
        if submission.get('submission_date') and not isinstance(submission['submission_date'], str):
            submission['submission_date'] = str(submission['submission_date'])
        
        return submission
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR fetching submission: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))