from fastapi import APIRouter, HTTPException
from src.services.exams_service import ExamService
from pydantic import BaseModel, field_validator,model_validator
from datetime import date, datetime, time

router = APIRouter(prefix="/exams", tags=["Exams"])
service = ExamService()

class ExamCreate(BaseModel):
    title: str
    exam_code: str
    date: str
    start_time: str
    end_time: str
    status: str = "scheduled"

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        date_obj = None
        formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"]
        
        # Try multiple date formats
        for fmt in formats:
            try:
                date_obj = datetime.strptime(v, fmt).date()
                break
            except ValueError:
                continue
        
        # If no format matched, raise error
        if date_obj is None:
            raise ValueError("Date must be in DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, or YYYY/MM/DD format")
        
        
        # Check if date is in the past
        if date_obj < date.today():
            raise ValueError("Exam date cannot be in the past")
        
        current_year = date.today().year
        if date_obj.year not in (current_year, current_year + 1):
            raise ValueError(f"Exam year must be {current_year} or {current_year + 1}")
        
        # Return the standardized date string (YYYY-MM-DD) for storage
        return date_obj.strftime("%Y-%m-%d")

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
        return v
    
    @model_validator(mode='before')
    def check_datetime_order_and_past(cls, values):
        date_str = values.get('date')
        start_str = values.get('start_time')
        end_str = values.get('end_time')

        if not date_str or not start_str or not end_str:
            return values  # skip if any missing; field validators handle missing values

        # Parse date back to date object
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Combine date with start_time and end_time to get full datetime objects
        start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")

        now = datetime.now()

        if end_dt <= start_dt:
            raise ValueError("End time must be after start time")

        if start_dt < now:
            raise ValueError("Exam start time cannot be in the past")

        return values


@router.post("", status_code=201)
def add_exam(exam: ExamCreate):
    try:
        result = service.add_exam(
            title=exam.title,
            exam_code=exam.exam_code,
            date=exam.date,
            start_time=exam.start_time,
            end_time=exam.end_time,
            status=exam.status
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{exam_id}")
def update_exam(exam_id: int, exam: ExamCreate):
    try:
        result = service.update_exam(
            exam_id=exam_id,
            title=exam.title,
            exam_code=exam.exam_code,
            date=exam.date,
            start_time=exam.start_time,
            end_time=exam.end_time,
            status=exam.status
        )
        if not result:
            raise HTTPException(status_code=404, detail="Exam not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{exam_id}")
def get_exam(exam_id: int):
    exam = service.get_exam(exam_id)
    if not exam:
        raise HTTPException(404, "Exam not found")
    return exam


@router.get("")
def get_all_exams():
    exams = service.get_all_exams()
    if not exams:
        return []
    return exams


@router.delete("/{exam_id}")
def delete_exam(exam_id: int):
    try:
        service.delete_exam(exam_id)
        return {"message": "Exam deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))