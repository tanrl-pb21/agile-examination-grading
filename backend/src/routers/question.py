from fastapi import APIRouter, HTTPException
from src.services.question_service import QuestionService
from pydantic import BaseModel, field_validator
from typing import List, Optional

router = APIRouter(prefix="/questions", tags=["Questions"])
service = QuestionService()


class MCQQuestionCreate(BaseModel):
    exam_id: int
    question_text: str
    marks: int
    options: List[str]
    correct_option_index: int

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Question text cannot be empty")
        return v.strip()

    @field_validator("marks")
    @classmethod
    def validate_marks(cls, v):
        if v < 1:
            raise ValueError("Marks must be at least 1")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v):
        if not v or len(v) < 2:
            raise ValueError("At least 2 options are required")

        for i, opt in enumerate(v):
            if not opt or not opt.strip():
                raise ValueError(f"Option {i + 1} cannot be empty")

        return [opt.strip() for opt in v]

    @field_validator("correct_option_index")
    @classmethod
    def validate_correct_option(cls, v, info):
        options = info.data.get("options", [])
        if options and (v < 0 or v >= len(options)):
            raise ValueError(
                f"Correct option index must be between 0 and {len(options) - 1}"
            )
        return v


class MCQQuestionUpdate(BaseModel):
    question_text: str
    marks: int
    options: List[str]
    correct_option_index: int

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Question text cannot be empty")
        return v.strip()

    @field_validator("marks")
    @classmethod
    def validate_marks(cls, v):
        if v < 1:
            raise ValueError("Marks must be at least 1")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v):
        if not v or len(v) < 2:
            raise ValueError("At least 2 options are required")

        for i, opt in enumerate(v):
            if not opt or not opt.strip():
                raise ValueError(f"Option {i + 1} cannot be empty")

        return [opt.strip() for opt in v]


class EssayQuestionCreate(BaseModel):
    exam_id: int
    question_text: str
    marks: int
    rubric: Optional[str] = None
    reference_answer: Optional[str] = None

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Question text cannot be empty")
        return v.strip()

    @field_validator("marks")
    @classmethod
    def validate_marks(cls, v):
        if v < 1:
            raise ValueError("Marks must be at least 1")
        return v


class EssayQuestionUpdate(BaseModel):
    question_text: str
    marks: int
    rubric: Optional[str] = None
    reference_answer: Optional[str] = None

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Question text cannot be empty")
        return v.strip()


@router.post("/mcq", status_code=201)
def add_mcq_question(question: MCQQuestionCreate):
    try:
        result = service.add_mcq_question(
            exam_id=question.exam_id,
            question_text=question.question_text,
            marks=question.marks,
            options=question.options,
            correct_option_index=question.correct_option_index,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/mcq/{question_id}")
def update_mcq_question(question_id: int, question: MCQQuestionUpdate):
    try:
        result = service.update_mcq_question(
            question_id=question_id,
            question_text=question.question_text,
            marks=question.marks,
            options=question.options,
            correct_option_index=question.correct_option_index,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/essay", status_code=201)
def add_essay_question(question: EssayQuestionCreate):
    try:
        result = service.add_essay_question(
            exam_id=question.exam_id,
            question_text=question.question_text,
            marks=question.marks,
            rubric=question.rubric,
            word_limit=None,
            reference_answer=question.reference_answer,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/essay/{question_id}")
def update_essay_question(question_id: int, question: EssayQuestionUpdate):
    try:
        result = service.update_essay_question(
            question_id=question_id,
            question_text=question.question_text,
            marks=question.marks,
            rubric=question.rubric,
            word_limit=None,
            reference_answer=question.reference_answer,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exam/{exam_id}")
def get_exam_questions(exam_id: int):
    try:
        questions = service.get_exam_questions(exam_id)
        return questions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{question_id}")
def get_question(question_id: int):
    try:
        question = service.get_question(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{question_id}")
def delete_question(question_id: int):
    try:
        service.delete_question(question_id)
        return {"message": "Question deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/exam/{exam_id}/statistics")
def get_exam_question_statistics(exam_id: int):
    """
    Get statistics for all MCQ questions in an exam.
    Returns how many students selected each option.
    """
    try:
        sql = """
            SELECT 
                q.id as question_id,
                q.question_text,
                qo.id as option_id,
                qo.option_text,
                qo.is_correct,
                COUNT(DISTINCT sa.submission_id) as student_count
            FROM question q
            INNER JOIN "questionOption" qo ON q.id = qo.question_id
            LEFT JOIN "submissionAnswer" sa ON qo.id = sa.selected_option_id
            WHERE q.exam_id = %s 
            AND q.question_type = 'mcq'
            GROUP BY q.id, q.question_text, qo.id, qo.option_text, qo.is_correct
            ORDER BY q.id, qo.id;
        """
        
        from src.db import get_conn
        from psycopg.rows import dict_row
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (exam_id,))
                rows = cur.fetchall()
        
        # Group by question
        questions_stats = {}
        for row in rows:
            question_id = row['question_id']
            
            if question_id not in questions_stats:
                questions_stats[question_id] = {
                    'question_id': question_id,
                    'question_text': row['question_text'],
                    'options': []
                }
            
            questions_stats[question_id]['options'].append({
                'option_id': row['option_id'],
                'option_text': row['option_text'],
                'is_correct': row['is_correct'],
                'student_count': row['student_count']
            })
        
        # Convert to list
        result = list(questions_stats.values())
        
        print(f"✅ Returning statistics for {len(result)} MCQ questions in exam {exam_id}")
        return result
        
    except Exception as e:
        print(f"❌ ERROR in get_exam_question_statistics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
