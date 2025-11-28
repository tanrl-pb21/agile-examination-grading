from fastapi import APIRouter, HTTPException
from src.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Submissions"])
service = SubmissionService()


# ========== INSTRUCTOR ROUTES ==========


@router.get("/exam/{exam_id}")
def get_exam_submissions(exam_id: int):
    """Get all submissions for an exam (Instructor view)"""
    try:
        submissions = service.get_exam_submissions(exam_id)
        return submissions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/exam/{exam_id}/summary")
def get_submission_summary(exam_id: int):
    """Get submission summary statistics for an exam"""
    try:
        summary = service.get_submission_summary(exam_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========== STUDENT ROUTES ==========


@router.get("/student/{user_id}")
def get_student_submissions(user_id: int):
    """Get all submissions for a student"""
    try:
        submissions = service.get_student_submissions(user_id)
        return submissions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{submission_id}/review")
def get_submission_review(submission_id: int, user_id: int):
    """Get detailed review of a submission"""
    try:
        review = service.get_submission_review(submission_id, user_id)
        return review
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
