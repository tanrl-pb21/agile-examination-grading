from fastapi import APIRouter, HTTPException, Query
from src.services.report_service import ReportsService
from typing import List, Optional

router = APIRouter(prefix="/reports", tags=["Reports"])
service = ReportsService()


@router.get("/completed-exams")
def get_completed_exams(
    instructor_id: Optional[int] = Query(None, description="Instructor ID for filtering")
):
    """
    Get all completed exams.
    If instructor_id is provided, only shows exams from courses assigned to that instructor.
    """
    try:
        exams = service.get_completed_exams(instructor_id)
        return exams if exams else []
    except Exception as e:
        print(f"ERROR in get_completed_exams: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam/{exam_id}/performance")
def get_exam_performance(
    exam_id: int,
    instructor_id: Optional[int] = Query(None, description="Instructor ID for access control")
):
    """
    Get performance statistics for a specific exam.
    If instructor_id is provided, ensures instructor has access to this course.
    """
    try:
        if exam_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid exam ID")

        performance_data = service.get_exam_performance_stats(exam_id, instructor_id)

        if not performance_data:
            error_msg = "Exam not found or no performance data available"
            if instructor_id:
                error_msg = "Exam not found or you don't have access to this course"
            raise HTTPException(status_code=404, detail=error_msg)

        return performance_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_exam_performance: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam/{exam_id}/student-scores")
def get_exam_student_scores(
    exam_id: int,
    instructor_id: Optional[int] = Query(None, description="Instructor ID for access control")
):
    """
    Get individual student scores for a specific exam.
    If instructor_id is provided, ensures instructor has access to this course.
    """
    try:
        if exam_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid exam ID")

        student_scores = service.get_exam_student_scores(exam_id, instructor_id)

        if not student_scores:
            error_msg = "No student scores found for this exam"
            if instructor_id:
                error_msg = "No student scores found or you don't have access to this course"
            raise HTTPException(status_code=404, detail=error_msg)

        return student_scores

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_exam_student_scores: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-courses")
def get_my_courses(
    instructor_id: Optional[int] = Query(None, description="Instructor ID")
):
    """
    Get all courses assigned to an instructor.
    """
    try:
        if not instructor_id:
            raise HTTPException(status_code=400, detail="Instructor ID is required")
            
        courses = service.get_instructor_courses(instructor_id)
        return courses if courses else []
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_my_courses: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))