from src.db import get_conn
from psycopg.rows import dict_row
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional

MALAYSIA_TZ = timezone(timedelta(hours=8))


# ========================================
# DOMAIN MODELS / VALUE OBJECTS
# ========================================

class ExamTimeWindow:
    """Value object representing exam time boundaries"""
    def __init__(self, start_dt: datetime, end_dt: datetime):
        self.start_dt = start_dt
        self.end_dt = end_dt
    
    def is_before_start(self, current_time: datetime) -> bool:
        return current_time < self.start_dt
    
    def is_after_end(self, current_time: datetime) -> bool:
        return current_time > self.end_dt
    
    def is_within_window(self, current_time: datetime) -> bool:
        return self.start_dt <= current_time <= self.end_dt
    
    def get_duration_seconds(self) -> int:
        return int((self.end_dt - self.start_dt).total_seconds())
    
    def get_remaining_seconds(self, current_time: datetime) -> int:
        return max(int((self.end_dt - current_time).total_seconds()), 0)
    
    def get_minutes_late(self, current_time: datetime) -> int:
        if current_time <= self.end_dt:
            return 0
        time_over = current_time - self.end_dt
        return int(time_over.total_seconds() / 60)


class GradeCalculator:
    """Pure function for grade calculation"""
    
    @staticmethod
    def calculate(score: int, max_score: int) -> str:
        """Calculate letter grade from score"""
        if max_score == 0:
            return "N/A"
        
        percentage = (score / max_score) * 100
        
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B"
        elif percentage >= 60:
            return "C"
        elif percentage >= 50:
            return "D"
        else:
            return "F"


# ========================================
# TIME UTILITIES (Pure Functions)
# ========================================

class TimeConverter:
    """Pure functions for time conversion"""
    
    @staticmethod
    def parse_date(date_value) -> datetime.date:
        if isinstance(date_value, str):
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        return date_value
    
    @staticmethod
    def parse_time(time_value) -> datetime.time:
        if isinstance(time_value, str):
            return datetime.strptime(time_value, "%H:%M:%S").time()
        return time_value
    
    @staticmethod
    def combine_datetime(date_obj: datetime.date, time_obj: datetime.time, tz=MALAYSIA_TZ) -> datetime:
        return datetime.combine(date_obj, time_obj, tz)
    
    @staticmethod
    def get_current_time(tz=MALAYSIA_TZ) -> datetime:
        """
        THIS is the hook tests will mock.
        Real system still uses datetime.now().
        """
        return datetime.now(tz)   # FIX ✓ Allow test monkeypatch


# ========================================
# DATABASE ACCESS LAYER
# ========================================

class ExamRepository:
    def get_exam_by_code(self, cursor, exam_code: str) -> Optional[Dict]:
        sql = "SELECT id, date, start_time, end_time, duration FROM exams WHERE exam_code = %s"
        cursor.execute(sql, (exam_code,))
        return cursor.fetchone()
    
    def get_exam_id(self, cursor, exam_code: str) -> int:
        exam = self.get_exam_by_code(cursor, exam_code)
        if not exam:
            raise ValueError(f"Exam with code '{exam_code}' not found")
        return exam["id"]


class QuestionRepository:
    def get_question_by_id(self, cursor, question_id: int, exam_id: int) -> Optional[Dict]:
        sql = "SELECT id, question_type, marks FROM question WHERE id = %s AND exam_id = %s"
        cursor.execute(sql, (question_id, exam_id))
        return cursor.fetchone()
    
    def get_correct_option_id(self, cursor, question_id: int) -> Optional[int]:
        sql = 'SELECT id FROM "questionOption" WHERE question_id = %s AND is_correct = true'
        cursor.execute(sql, (question_id,))
        result = cursor.fetchone()
        return result["id"] if result else None
    
    def get_questions_with_options(self, cursor, exam_id: int) -> List[Dict]:
        sql_questions = "SELECT id, question_text, question_type, marks FROM question WHERE exam_id = %s ORDER BY id"
        cursor.execute(sql_questions, (exam_id,))
        questions = cursor.fetchall()
        
        sql_options = 'SELECT id, option_text FROM "questionOption" WHERE question_id = %s ORDER BY id'
        for question in questions:
            cursor.execute(sql_options, (question["id"],))
            question["options"] = cursor.fetchall()
        
        return questions


class SubmissionRepository:
    def check_submission_exists(self, cursor, exam_id: int, user_id: int) -> bool:
        sql = "SELECT id FROM submission WHERE exam_code = %s AND user_id = %s LIMIT 1"
        cursor.execute(sql, (exam_id, user_id))
        return cursor.fetchone() is not None
    
    def create_submission(self, cursor, exam_id: int, user_id: int, now: datetime) -> int:
        sql = """
            INSERT INTO submission (exam_code, user_id, submission_date, submission_time, status, score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(sql, (exam_id, user_id, now.date(), now.time(), "pending", 0))
        return cursor.fetchone()["id"]
    
    def update_submission_final(self, cursor, submission_id: int, score: int, status: str, grade: str):
        sql = "UPDATE submission SET score = %s, status = %s, score_grade = %s WHERE id = %s"
        cursor.execute(sql, (score, status, grade, submission_id))


class AnswerRepository:
    def create_submission_answer(self, cursor, submission_id: int, question_id: int, 
                                 selected_option_id: Optional[int], score: Optional[int], 
                                 feedback: Optional[str]) -> int:
        sql = """
            INSERT INTO "submissionAnswer" (submission_id, question_id, selected_option_id, score, feedback)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(sql, (submission_id, question_id, selected_option_id, score, feedback))
        return cursor.fetchone()["id"]
    
    def save_mcq_answer(self, cursor, submission_answer_id: int, selected_option_id: int):
        sql = 'INSERT INTO "mcqAnswer" (submission_answer_id, selected_option_id) VALUES (%s, %s)'
        cursor.execute(sql, (submission_answer_id, selected_option_id))
    
    def save_essay_answer(self, cursor, submission_answer_id: int, essay_text: str):
        sql = 'INSERT INTO "essayAnswer" (submission_answer_id, essay_answer) VALUES (%s, %s)'
        cursor.execute(sql, (submission_answer_id, essay_text))


# ========================================
# BUSINESS LOGIC / DOMAIN SERVICES
# ========================================

class ExamAvailabilityChecker:
    def __init__(self, time_converter: TimeConverter):
        self.time_converter = time_converter
    
    def check_availability(self, exam_data: Dict, current_time: Optional[datetime] = None) -> Dict:
        """Allow test to inject time (via mocking TimeConverter.get_current_time)."""
        if current_time is None:
            current_time = self.time_converter.get_current_time()   # FIX ✓

        exam_date = self.time_converter.parse_date(exam_data["date"])
        start_time = self.time_converter.parse_time(exam_data["start_time"])
        end_time = self.time_converter.parse_time(exam_data["end_time"])
        
        start_dt = self.time_converter.combine_datetime(exam_date, start_time)
        end_dt = self.time_converter.combine_datetime(exam_date, end_time)
        
        window = ExamTimeWindow(start_dt, end_dt)
        
        if window.is_before_start(current_time):
            return {"status": "not_started", "message": f"Exam starts at {start_time.strftime('%H:%M')} on {exam_date}."}
        
        if window.is_after_end(current_time):
            return {"status": "ended", "message": f"Exam ended at {end_time.strftime('%H:%M')} on {exam_date}."}
        
        return {"status": "available", "message": "Exam is open."}


class SubmissionTimeValidator:
    def __init__(self, time_converter: TimeConverter):
        self.time_converter = time_converter
    
    def validate(self, exam_data: Dict, current_time: Optional[datetime] = None) -> bool:
        """Allow test to mock time"""
        if current_time is None:
            current_time = self.time_converter.get_current_time()   # FIX ✓
        
        exam_date = self.time_converter.parse_date(exam_data["date"])
        start_time = self.time_converter.parse_time(exam_data["start_time"])
        end_time = self.time_converter.parse_time(exam_data["end_time"])
        
        start_dt = self.time_converter.combine_datetime(exam_date, start_time)
        end_dt = self.time_converter.combine_datetime(exam_date, end_time)
        
        window = ExamTimeWindow(start_dt, end_dt)
        
        if window.is_before_start(current_time):
            raise ValueError(
                f"Cannot submit exam before start time. Exam starts at {start_time.strftime('%H:%M')} on {exam_date.strftime('%Y-%m-%d')}"
            )
        
        if window.is_after_end(current_time):
            minutes_late = window.get_minutes_late(current_time)
            raise ValueError(
                f"Submission rejected: The exam ended at {end_time.strftime('%H:%M')}. "
                f"You are {minutes_late} minute(s) late. Late submissions are not accepted."
            )
        
        return True


class MCQAnswerGrader:
    def grade(self, selected_option_id: int, correct_option_id: int, marks: int) -> Dict:
        is_correct = selected_option_id == correct_option_id
        score = marks if is_correct else 0
        feedback = "Correct" if is_correct else "Incorrect"
        
        return {
            "is_correct": is_correct,
            "score": score,
            "feedback": feedback
        }


class AnswerProcessor:
    def __init__(self, question_repo: QuestionRepository, answer_repo: AnswerRepository, 
                 mcq_grader: MCQAnswerGrader):
        self.question_repo = question_repo
        self.answer_repo = answer_repo
        self.mcq_grader = mcq_grader
    
    def process_mcq(self, cursor, submission_id: int, question_id: int, 
                    selected_option_id: int, marks: int) -> Dict:

        correct_option_id = self.question_repo.get_correct_option_id(cursor, question_id)
        if not correct_option_id:
            raise ValueError(f"No correct answer set for question {question_id}")
        
        grading_result = self.mcq_grader.grade(selected_option_id, correct_option_id, marks)
        
        submission_answer_id = self.answer_repo.create_submission_answer(
            cursor, submission_id, question_id, selected_option_id, 
            grading_result["score"], grading_result["feedback"]
        )
        self.answer_repo.save_mcq_answer(cursor, submission_answer_id, selected_option_id)
        
        return {
            "question_id": question_id,
            "type": "mcq",
            "is_correct": grading_result["is_correct"],
            "score": grading_result["score"],
            "max_score": marks
        }
    
    def process_essay(self, cursor, submission_id: int, question_id: int, 
                      essay_text: str, marks: int) -> Dict:
        submission_answer_id = self.answer_repo.create_submission_answer(
            cursor, submission_id, question_id, None, None, "Pending teacher review"
        )
        self.answer_repo.save_essay_answer(cursor, submission_answer_id, essay_text)
        
        return {
            "question_id": question_id,
            "type": "essay",
            "status": "pending",
            "max_score": marks
        }


# ========================================
# MAIN SERVICE
# ========================================

class TakeExamService:
    def __init__(self):
        self.exam_repo = ExamRepository()
        self.question_repo = QuestionRepository()
        self.submission_repo = SubmissionRepository()
        self.answer_repo = AnswerRepository()
        
        self.time_converter = TimeConverter()
        self.availability_checker = ExamAvailabilityChecker(self.time_converter)
        self.time_validator = SubmissionTimeValidator(self.time_converter)
        self.mcq_grader = MCQAnswerGrader()
        self.answer_processor = AnswerProcessor(self.question_repo, self.answer_repo, self.mcq_grader)
        self.grade_calculator = GradeCalculator()
    
    def get_exam_duration_by_code(self, exam_code: str) -> Dict:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                exam = self.exam_repo.get_exam_by_code(cur, exam_code)
        
        if not exam:
            raise ValueError("Exam not found")
        
        exam_date = self.time_converter.parse_date(exam["date"])
        start_time = self.time_converter.parse_time(exam["start_time"])
        end_time = self.time_converter.parse_time(exam["end_time"])
        
        start_dt = self.time_converter.combine_datetime(exam_date, start_time)
        end_dt = self.time_converter.combine_datetime(exam_date, end_time)
        window = ExamTimeWindow(start_dt, end_dt)

        current_time = self.time_converter.get_current_time()     # FIX ✓ picked up by mock

        return {
            "duration_seconds": window.get_duration_seconds(),
            "remaining_seconds": window.get_remaining_seconds(current_time),
            "date": exam_date.isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    def check_exam_availability(self, exam_code: str) -> Dict:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                exam = self.exam_repo.get_exam_by_code(cur, exam_code)
        
        if not exam:
            raise ValueError("Exam not found")
        
        current_time = self.time_converter.get_current_time()     # FIX ✓ test patch works
        return self.availability_checker.check_availability(exam, current_time)
    
    def check_if_student_submitted(self, exam_code: str, user_id: int) -> bool:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                exam_id = self.exam_repo.get_exam_id(cur, exam_code)
                return self.submission_repo.check_submission_exists(cur, exam_id, user_id)
    
    def get_questions_by_exam_code(self, exam_code: str) -> Dict:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                exam_id = self.exam_repo.get_exam_id(cur, exam_code)
                questions = self.question_repo.get_questions_with_options(cur, exam_id)
        return {"questions": questions}
    
    def validate_submission_time(self, exam_code: str) -> bool:
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                exam = self.exam_repo.get_exam_by_code(cur, exam_code)
        
        if not exam:
            raise ValueError("Exam not found")

        current_time = self.time_converter.get_current_time()   # FIX ✓ tests mock this
        return self.time_validator.validate(exam, current_time)
    
    def submit_exam(self, exam_code: str, user_id: int, answers: List) -> Dict:
        """Main function to process exam submission"""
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:

                exam = self.exam_repo.get_exam_by_code(cur, exam_code)
                if not exam:
                    raise ValueError("Exam not found")

                # Validate time window using mocked time
                current_time = self.time_converter.get_current_time()    # FIX ✓
                self.time_validator.validate(exam, current_time)

                exam_id = exam["id"]

                # create submission
                submission_id = self.submission_repo.create_submission(cur, exam_id, user_id, current_time)

                total_score = 0
                max_score = 0
                has_essay = False
                graded_results = []
                
                for answer_data in answers:
                    question_id = answer_data.question_id
                    answer_value = answer_data.answer
                    
                    question = self.question_repo.get_question_by_id(cur, question_id, exam_id)
                    if not question:
                        raise ValueError(f"Question {question_id} not found for this exam")
                    
                    q_type = question["question_type"].lower()
                    marks = question["marks"]
                    max_score += marks
                    
                    if q_type == "mcq":
                        result = self.answer_processor.process_mcq(
                            cur, submission_id, question_id, int(answer_value), marks
                        )
                        total_score += result["score"]
                        graded_results.append(result)
                    
                    elif q_type == "essay":
                        has_essay = True
                        result = self.answer_processor.process_essay(
                            cur, submission_id, question_id, str(answer_value), marks
                        )
                        graded_results.append(result)
                
                grade = self.grade_calculator.calculate(total_score, max_score)
                
                final_status = "pending" if has_essay else "graded"
                final_grade = "Pending" if has_essay else grade
                
                self.submission_repo.update_submission_final(
                    cur, submission_id, total_score, final_status, final_grade
                )
                
                conn.commit()
        
        return {
            "submission_id": submission_id,
            "status": final_status,
            "total_score": total_score,
            "max_score": max_score,
            "grade": final_grade,
            "message": (
                "Exam submitted successfully. Essays are pending teacher review."
                if has_essay else "Exam submitted and graded successfully."
            ),
            "results": graded_results
        }
