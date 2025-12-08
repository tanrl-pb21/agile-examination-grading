from fastapi import APIRouter, HTTPException
from src.services.exams_service import ExamService
from pydantic import BaseModel, field_validator, model_validator
from datetime import date, datetime, time

router = APIRouter(prefix="/exams", tags=["Exams"])
service = ExamService()


class ExamCreate(BaseModel):
    title: str
    exam_code: str
    course: str
    date: str
    start_time: str
    end_time: str
    status: str = "scheduled"

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_time_format(cls, v):
        print(f"DEBUG: Received value: {v!r}, type: {type(v)}")
        """Validate time is in HH:MM format"""
        if not v:
            raise ValueError("Time is required")

        # Convert to string if needed
        v = str(v).strip()

        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError(f"Time must be in HH:MM format, got '{v}'")
        return v

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v):
        date_obj = None
        formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"]

        # Handle if it's already a date object
        if isinstance(v, date):
            date_obj = v
        else:
            # Convert to string and try formats
            v = str(v).strip()
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(v, fmt).date()
                    break
                except ValueError:
                    continue

        if date_obj is None:
            raise ValueError(
                "Date must be in DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, or YYYY/MM/DD format"
            )

        if date_obj < date.today():
            raise ValueError("Exam date cannot be in the past")

        current_year = date.today().year
        if date_obj.year not in (current_year, current_year + 1):
            raise ValueError(f"Exam year must be {current_year} or {current_year + 1}")

        return date_obj.strftime("%Y-%m-%d")

    @model_validator(mode="after")
    def check_datetime_order_and_past(self):
        """Validate time order and that exam is not in the past"""
        date_str = self.date
        start_str = self.start_time
        end_str = self.end_time

        try:
            start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            raise ValueError(f"Error parsing datetime: {str(e)}")

        now = datetime.now()

        if end_dt <= start_dt:
            raise ValueError("End time must be after start time")

        if self.status in ["scheduled", "published"]:
            now = datetime.now()
            if start_dt < now:
                raise ValueError("Exam start time cannot be in the past")

        return self


def convert_time_to_string(exam_dict):
    """Helper function to convert time objects to strings"""
    if not exam_dict:
        return exam_dict

    if (
        "start_time" in exam_dict
        and exam_dict["start_time"]
        and not isinstance(exam_dict["start_time"], str)
    ):
        exam_dict["start_time"] = exam_dict["start_time"].strftime("%H:%M")

    if (
        "end_time" in exam_dict
        and exam_dict["end_time"]
        and not isinstance(exam_dict["end_time"], str)
    ):
        exam_dict["end_time"] = exam_dict["end_time"].strftime("%H:%M")

    return exam_dict


# IMPORTANT: GET routes should come BEFORE parameterized routes to avoid conflicts
@router.get("")
def get_all_exams():
    """Get all exams - this must be defined before /{exam_id} route"""
    try:
        print("📋 GET /exams - Fetching all exams...")
        exams = service.get_all_exams()

        if not exams:
            print("✅ No exams found, returning empty list")
            return []

        # Convert time objects to strings for all exams
        converted_exams = [convert_time_to_string(exam) for exam in exams]
        print(f"✅ Returning {len(converted_exams)} exams")
        return converted_exams

    except Exception as e:
        print(f"❌ ERROR in get_all_exams: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/student/{student_id}")
def get_student_exams(student_id: int):
    """
    Get all exams for a specific student based on their enrolled courses.
    Must be defined before the generic /{exam_id} route.
    """
    try:
        exams = service.get_student_exams(student_id)
        if not exams:
            return []
        return [convert_time_to_string(exam) for exam in exams]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/available")
def get_available_exams_for_student(student_id: int = 1):
    """
    Get exams that are currently open for student's enrolled courses.
    Filter by: start_time <= now <= end_time AND course in student's courses
    """
    try:
        exams = service.get_available_exams_for_student(student_id)
        return [convert_time_to_string(exam) for exam in exams] if exams else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
def get_upcoming_exams_for_student(student_id: int = 1):
    """
    Get exams scheduled for future for student's enrolled courses.
    Filter by: date > today OR (date = today AND start_time > now) 
    AND course in student's courses
    """
    try:
        exams = service.get_upcoming_exams_for_student(student_id)
        return [convert_time_to_string(exam) for exam in exams] if exams else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/{exam_id}")
def get_exam(exam_id: int):
    """Get a single exam by ID"""
    try:
        print(f"📋 GET /exams/{exam_id} - Fetching single exam...")
        exam = service.get_exam(exam_id)
        if not exam:
            raise HTTPException(404, "Exam not found")
        return convert_time_to_string(exam)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in get_exam: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exams/{exam_id}/open")
def open_exam(exam_id: int):
    exam = service.get_exam_by_id(exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    from datetime import datetime
    now = datetime.now()

    start_dt = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M")

    if now < start_dt:
        raise HTTPException(status_code=403, detail="Exam not started yet")

    if now > end_dt:
        raise HTTPException(status_code=403, detail="Exam has ended")

    return {"message": "Exam open", "exam": exam}


@router.post("", status_code=201)
def add_exam(exam: ExamCreate):
    try:
        result = service.add_exam(
            title=exam.title,
            exam_code=exam.exam_code,
            course=exam.course,
            date=exam.date,
            start_time=exam.start_time,
            end_time=exam.end_time,
            status=exam.status,
        )
        return convert_time_to_string(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{exam_id}")
def update_exam(exam_id: int, exam: ExamCreate):
    try:
        result = service.update_exam(
            exam_id=exam_id,
            title=exam.title,
            exam_code=exam.exam_code,
            course=exam.course,
            date=exam.date,
            start_time=exam.start_time,
            end_time=exam.end_time,
            status=exam.status,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Exam not found")
        return convert_time_to_string(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{exam_id}")
def delete_exam(exam_id: int):
    try:
        service.delete_exam(exam_id)
        return {"message": "Exam deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.get("/search/title")
def search_exams_by_title(title: str):
    """
    Search exams by title (case-insensitive, partial match).
    
    Query parameters:
    - title (required): Search term to find in exam titles
    
    Example: GET /exams/search/title?title=midterm
    """
    try:
        # Check for empty or whitespace-only string
        if not title or not title.strip():
            raise HTTPException(status_code=400, detail="Search term cannot be empty")
        
        exams = service.search_exams_by_title(title)
        return [convert_time_to_string(exam) for exam in exams] if exams else []
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/code")
def search_exams_by_code(exam_code: str):
    """
    Search exams by exam code (case-insensitive, exact match).
    
    Query parameters:
    - exam_code (required): Exam code to search for
    
    Example: GET /exams/search/code?exam_code=CS101-MID
    """
    try:
        # Check for empty or whitespace-only string
        if not exam_code or not exam_code.strip():
            raise HTTPException(status_code=400, detail="Exam code cannot be empty")
        
        exams = service.search_exams_by_code(exam_code)
        return [convert_time_to_string(exam) for exam in exams] if exams else []
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/course")
def search_student_exams_by_course(student_id: int, course_name: str):
    """
    Search student's exams by course name (case-insensitive, partial match).
    
    Query parameters:
    - student_id (required): ID of the student
    - course_name (required): Course name to search for
    
    Example: GET /exams/search/course?student_id=1&course_name=mathematics
    """
    try:
        # Check for empty or whitespace-only string
        if not course_name or not course_name.strip():
            raise HTTPException(status_code=400, detail="Course name cannot be empty")
        
        if student_id <= 0:
            raise HTTPException(status_code=400, detail="Valid student ID is required")
        
        exams = service.search_student_exams_by_course(student_id, course_name)
        return [convert_time_to_string(exam) for exam in exams] if exams else []
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filter/status")
def filter_exams_by_status(status: str):
    """
    Filter exams by status (scheduled, completed, cancelled).
    
    Query parameters:
    - status (required): Status filter (scheduled, completed, or cancelled)
    
    Example: GET /exams/filter/status?status=scheduled
    """
    try:
        valid_statuses = ["scheduled", "completed", "cancelled"]
        
        # Check for empty or whitespace-only string
        if not status or not status.strip():
            raise HTTPException(
                status_code=400, 
                detail=f"Status must be one of: {', '.join(valid_statuses)}"
            )
        
        # Check if status is valid
        if status.strip().lower() not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Status must be one of: {', '.join(valid_statuses)}"
            )
        
        exams = service.filter_exams_by_status(status)
        return [convert_time_to_string(exam) for exam in exams] if exams else []
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filter/status/student")
def filter_student_exams_by_status(student_id: int, status: str):
    """
    Filter a student's exams by status (scheduled, completed, cancelled).
    
    Query parameters:
    - student_id (required): ID of the student
    - status (required): Status filter (scheduled, completed, or cancelled)
    
    Example: GET /exams/filter/status/student?student_id=1&status=scheduled
    """
    try:
        valid_statuses = ["scheduled", "completed", "cancelled"]
        
        if student_id <= 0:
            raise HTTPException(status_code=400, detail="Valid student ID is required")
        
        # Check for empty or whitespace-only string
        if not status or not status.strip():
            raise HTTPException(
                status_code=400, 
                detail=f"Status must be one of: {', '.join(valid_statuses)}"
            )
        
        # Check if status is valid
        if status.strip().lower() not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Status must be one of: {', '.join(valid_statuses)}"
            )
        
        exams = service.filter_student_exams_by_status(student_id, status)
        return [convert_time_to_string(exam) for exam in exams] if exams else []
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{exam_id}/can-publish")
def check_can_publish_exam(exam_id: int):
    """
    Check if an exam can be published without actually publishing it.
    Returns validation info.
    """
    try:
        result = service.can_publish_exam(exam_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{exam_id}/publish")
def publish_exam_route(exam_id: int):
    """
    Publish an exam (change status to 'published').
    Only works if exam has questions and date/time is in future.
    """
    try:
        exam = service.publish_exam(exam_id)
        return {
            "message": "Exam published successfully",
            "exam": convert_time_to_string(exam)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/{exam_id}/status")
def update_exam_status(exam_id: int, status: str):
    """
    Update only the exam status without validation.
    Used for auto-updating completed exams.
    
    Query parameter:
    - status: The new status (scheduled, published, completed, cancelled)
    """
    try:
        valid_statuses = ["scheduled", "published", "completed", "cancelled"]
        
        if not status or status.strip().lower() not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Status must be one of: {', '.join(valid_statuses)}"
            )
        
        status = status.strip().lower()
        
        # Call service method to update only status
        exam = service.update_exam_status(exam_id, status)
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        return convert_time_to_string(exam)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))