# from fastapi import APIRouter, HTTPException
# from src.services.course_service import CourseService

# router = APIRouter(prefix="/courses", tags=["Courses"])
# service = CourseService()


# @router.get("")
# def get_all_courses():
#     """Get all courses"""
#     try:
#         courses = service.get_all_courses()
#         return courses
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])
service = CourseService()


# Pydantic models for request/response
class CourseCreate(BaseModel):
    course_name: str
    course_code: str
    description: Optional[str] = None
    status: str = "active"


class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CourseStatusUpdate(BaseModel):
    status: str


class InstructorAssignment(BaseModel):
    instructor_id: int


@router.get("")
def get_all_courses(status: Optional[str] = None):
    """Get all courses with optional status filter"""
    try:
        courses = service.get_all_courses(status)
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instructors")
def get_all_instructors():
    """Get all available instructors"""
    try:
        instructors = service.get_all_instructors()
        return instructors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}")
def get_course_detail(course_id: int):
    """Get detailed information about a specific course"""
    try:
        course = service.get_course_by_id(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
def create_course(course: CourseCreate):
    """Create a new course"""
    try:
        new_course = service.create_course(course.dict())
        return {"message": "Course created successfully", "course": new_course}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{course_id}")
def update_course(course_id: int, course: CourseUpdate):
    """Update an existing course"""
    try:
        updated_course = service.update_course(course_id, course.dict(exclude_unset=True))
        if not updated_course:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course updated successfully", "course": updated_course}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{course_id}/status")
def update_course_status(course_id: int, status_update: CourseStatusUpdate):
    """Activate or deactivate a course"""
    try:
        if status_update.status not in ["active", "inactive"]:
            raise HTTPException(status_code=400, detail="Status must be 'active' or 'inactive'")
        
        updated_course = service.update_course_status(course_id, status_update.status)
        if not updated_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        action = "activated" if status_update.status == "active" else "deactivated"
        return {"message": f"Course {action} successfully", "course": updated_course}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}")
def delete_course(course_id: int):
    """Delete a course (only if status is inactive)"""
    try:
        result = service.delete_course(course_id)
        if not result:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/students")
def get_course_students(course_id: int):
    """Get all students enrolled in a specific course"""
    try:
        students = service.get_course_students(course_id)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/exams")
def get_course_exams(course_id: int):
    """Get all exams for a specific course"""
    try:
        exams = service.get_course_exams(course_id)
        return exams
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/instructors")
def get_course_instructors(course_id: int):
    """Get the instructor(s) for a specific course"""
    try:
        instructors = service.get_course_instructors(course_id)
        return instructors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{course_id}/instructors")
def assign_instructor_to_course(course_id: int, assignment: InstructorAssignment):
    """Assign an instructor to a course"""
    try:
        result = service.assign_instructor(course_id, assignment.instructor_id)
        return {"message": "Instructor assigned successfully", "assignment": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}/instructors/{instructor_id}")
def remove_instructor_from_course(course_id: int, instructor_id: int):
    """Remove an instructor from a course"""
    try:
        result = service.remove_instructor(course_id, instructor_id)
        if not result:
            raise HTTPException(status_code=404, detail="Instructor assignment not found")
        return {"message": "Instructor removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))