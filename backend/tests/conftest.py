import sys
import os
import types
from typing import Any, Dict, List

# backend root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

#  backend added to python search path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ------------------------------------------------------------
# Test double for missing TakeExamService (used by routers)
# ------------------------------------------------------------
class FakeTakeExamService:
    """Lightweight in-memory replacement to keep API tests runnable."""

    def __init__(self):
        self.questions = [
            {
                "id": 101,
                "question_type": "MCQ",
                "question_text": "What is 2 + 2?",
                "marks": 1,
                "options": [
                    {"id": 201, "option_text": "3"},
                    {"id": 202, "option_text": "4"},
                ],
                "correct_option_id": 202,
            },
            {
                "id": 102,
                "question_type": "Essay",
                "question_text": "Explain the Pythagorean theorem.",
                "marks": 5,
                "options": [],
            },
        ]
        self.submissions: List[Dict[str, Any]] = []
        self.remaining_seconds = 900

    def get_exam_duration_by_code(self, exam_code: str) -> Dict[str, Any]:
        return {"exam_code": exam_code, "remaining_seconds": self.remaining_seconds}

    def check_exam_availability(self, exam_code: str) -> Dict[str, str]:
        return {"status": "available", "message": f"Exam {exam_code} is open"}

    def check_if_student_submitted(self, exam_code: str, user_id: int) -> bool:
        return any(
            s["exam_code"] == exam_code and s["user_id"] == user_id
            for s in self.submissions
        )

    def get_questions_by_exam_code(self, exam_code: str) -> Dict[str, Any]:
        return {"exam_code": exam_code, "questions": self.questions}

    def validate_submission_time(self, exam_code: str) -> None:
        # Always allow during tests; late scenarios can patch this method.
        return None

    def submit_exam(self, exam_code: str, user_id: int, answers: Any) -> Dict[str, Any]:
        # Support Pydantic objects or plain dicts
        def _to_dict(obj: Any) -> Dict[str, Any]:
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "__dict__") and not isinstance(obj, dict):
                return obj.__dict__
            return dict(obj)

        answers_list = [_to_dict(a) for a in answers]
        correct_map = {
            q["id"]: q["correct_option_id"]
            for q in self.questions
            if q["question_type"].lower() == "mcq"
        }

        auto_score = 0
        total_mcq = len(correct_map)
        for answer in answers_list:
            qid = answer.get("question_id")
            resp = answer.get("answer")
            if qid in correct_map and resp == correct_map[qid]:
                auto_score += 1

        submission = {
            "exam_code": exam_code,
            "user_id": user_id,
            "answers": answers_list,
            "auto_score": auto_score,
            "total_mcq": total_mcq,
        }
        self.submissions.append(submission)

        return {
            "message": "Exam submitted",
            "exam_code": exam_code,
            "user_id": user_id,
            "auto_score": auto_score,
            "total_mcq": total_mcq,
            "submitted_answers": answers_list,
        }


# Inject fake module before routers import it
fake_module = types.SimpleNamespace(TakeExamService=FakeTakeExamService)
sys.modules.setdefault("src.services.take_exam_service", fake_module)