from fastapi import APIRouter, HTTPException
from src.services.exams_service import ExamService

router = APIRouter(prefix="/exams", tags=["Exams"])
service = ExamService()


@router.post("", status_code=201)
def add_exam(exam: dict):
    try:
        return service.add_exam(exam["title"], exam["start_time"], exam["end_time"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{exam_id}")
def get_exam(exam_id: int):
    exam = service.get_exam(exam_id)
    if not exam:
        raise HTTPException(404, "Exam not found")
    return exam

