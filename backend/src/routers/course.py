from fastapi import APIRouter, HTTPException
from src.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])
service = CourseService()

@router.get("")
def get_all_courses():
    """Get all courses"""
    try:
        courses = service.get_all_courses()
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))