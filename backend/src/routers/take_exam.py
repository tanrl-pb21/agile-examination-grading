from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src.services.take_exam_service import TakeExamService

router = APIRouter(prefix="/take-exam", tags=["Take Exam"])

take_exam_service = TakeExamService()


# ===========================
# REQUEST MODELS
# ===========================

class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer: str | int  # MCQ: option_id (int), Essay: text (str)


class SubmitExamRequest(BaseModel):
    exam_code: str
    user_id: int
    answers: List[SubmitAnswerRequest]


# ===========================
# ROUTES
# ===========================

@router.get("/duration/{exam_code}")
async def get_exam_duration(exam_code: str):
    """Get exam duration and remaining time"""
    try:
        print(f"🔍 Getting duration for exam_code: {exam_code}")
        result = take_exam_service.get_exam_duration_by_code(exam_code)
        print(f"✅ Duration result: {result}")
        return result
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting exam duration: {str(e)}")


@router.get("/availability/{exam_code}")
async def check_exam_availability(exam_code: str):
    """Check if exam is currently available for taking"""
    try:
        print(f"🔍 Checking availability for exam_code: {exam_code}")
        result = take_exam_service.check_exam_availability(exam_code)
        print(f"✅ Availability result: {result}")
        return result
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error checking exam availability: {str(e)}")


@router.get("/check-submission/{exam_code}/{user_id}")
async def check_if_submitted(exam_code: str, user_id: int):
    """Check if student already submitted this exam"""
    try:
        print(f"🔍 Checking submission for exam_code: {exam_code}, user_id: {user_id}")
        submitted = take_exam_service.check_if_student_submitted(exam_code, user_id)
        print(f"✅ Submission check result: {submitted}")
        return {"submitted": submitted}
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error checking submission status: {str(e)}")


@router.get("/questions/{exam_code}")
async def get_exam_questions(exam_code: str):
    """Get all questions for an exam"""
    try:
        print(f"🔍 Getting questions for exam_code: {exam_code}")
        result = take_exam_service.get_questions_by_exam_code(exam_code)
        print(f"✅ Questions retrieved: {len(result.get('questions', []))} questions")
        return result
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting exam questions: {str(e)}")


@router.post("/submit")
async def submit_exam(request: SubmitExamRequest):
    """Submit exam answers"""
    try:
        print(f"🔍 Submitting exam: {request.exam_code} for user: {request.user_id}")
        print(f"   Answers count: {len(request.answers)}")
        
        # First, validate submission time
        take_exam_service.validate_submission_time(request.exam_code)
        print(f"✅ Submission time validated")
        
        # If validation passes, process submission
        result = take_exam_service.submit_exam(
            exam_code=request.exam_code,
            user_id=request.user_id,
            answers=request.answers
        )
        print(f"✅ Exam submitted successfully: {result}")
        return result
    
    except ValueError as e:
        # Validation errors (late submission, exam not found, etc.)
        print(f"❌ Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Unexpected errors
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error submitting exam: {str(e)}")