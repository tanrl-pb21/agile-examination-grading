from fastapi import APIRouter, HTTPException
from src.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])
service = CourseService()

@router.get("")
def get_all_courses():
    courses = service.get_all_courses()
    if not courses:
        return []
    return courses
