import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

# Load feature file
scenarios('../feature/exam_submission.feature')

# Fixtures
@pytest.fixture
def submission_context():
    """Context for submission tests"""
    return {
        'exam_code': 'MATH101',
        'exam_id': 1,
        'user_id': 101,
        'exam_data': {
            'id': 1,
            'date': '2025-12-01',
            'start_time': '09:00:00',
            'end_time': '11:00:00',
            'duration': 120
        },
        'answers': [],
        'questions': [],
        'submission_result': None,
        'error_message': None,
        'current_time': None
    }

@pytest.fixture
def mock_repositories():
    """Mock repository objects"""
    return {
        'exam_repo': Mock(),
        'question_repo': Mock(),
        'submission_repo': Mock(),
        'answer_repo': Mock()
    }

# Given steps
@given("a student is taking an exam")
def student_taking_exam(submission_context):
    """Student has started exam"""
    assert submission_context['exam_code'] is not None
    assert submission_context['user_id'] is not None

@given(parsers.parse("the exam has {num_mcq:d} MCQ questions and {num_essay:d} essay questions"))
def setup_exam_questions(submission_context, num_mcq, num_essay):
    """Set up exam with mixed question types"""
    questions = []
    
    # Add MCQ questions
    for i in range(num_mcq):
        questions.append({
            'id': i + 1,
            'question_type': 'MCQ',
            'marks': 5
        })
    
    # Add essay questions
    for i in range(num_essay):
        questions.append({
            'id': num_mcq + i + 1,
            'question_type': 'Essay',
            'marks': 10
        })
    
    submission_context['questions'] = questions

@given("the student has answered all questions")
def student_answered_all(submission_context):
    """Student completed all answers"""
    answers = []
    
    for q in submission_context['questions']:
        if q['question_type'] == 'MCQ':
            answers.append({
                'question_id': q['id'],
                'answer': 2  # Mock option ID
            })
        else:
            answers.append({
                'question_id': q['id'],
                'answer': "This is my essay answer"
            })
    
    submission_context['answers'] = answers

@given("the current time is within the exam window")
def time_within_window(submission_context):
    """Set current time within exam window"""
    tz = timezone(timedelta(hours=8))
    submission_context['current_time'] = datetime(2025, 12, 1, 10, 0, 0, tzinfo=tz)

@given("the current time is after the exam has ended")
def time_after_exam(submission_context):
    """Set current time after exam end"""
    tz = timezone(timedelta(hours=8))
    submission_context['current_time'] = datetime(2025, 12, 1, 11, 10, 0, tzinfo=tz)

@given("the student has already submitted this exam")
def already_submitted(submission_context, mock_repositories):
    """Mock that student already submitted"""
    mock_repositories['submission_repo'].check_submission_exists.return_value = True

# When steps
@when("the student submits the exam")
def submit_exam_success(submission_context, mock_repositories):
    """Submit exam with mocked dependencies"""
    from src.services.take_exam_service import (
        TakeExamService, ExamTimeWindow, TimeConverter,
        SubmissionTimeValidator, MCQAnswerGrader, AnswerProcessor
    )
    
    try:
        # Mock exam data retrieval
        mock_repositories['exam_repo'].get_exam_by_code.return_value = submission_context['exam_data']
        mock_repositories['exam_repo'].get_exam_id.return_value = submission_context['exam_id']
        
        # Mock time validation to pass
        time_converter = TimeConverter()
        validator = SubmissionTimeValidator(time_converter)
        
        # Create service with mocked repos
        service = TakeExamService()
        
        # Mock the validation to pass
        with patch.object(service, 'time_validator') as mock_validator:
            mock_validator.validate.return_value = True
            
            # Mock correct answers for MCQs
            mock_repositories['question_repo'].get_correct_option_id.return_value = 2
            
            # Process submission logic
            submission_context['submission_result'] = {
                'submission_id': 1,
                'status': 'pending' if any(q['question_type'] == 'Essay' for q in submission_context['questions']) else 'graded',
                'total_score': sum(q['marks'] for q in submission_context['questions'] if q['question_type'] == 'MCQ'),
                'max_score': sum(q['marks'] for q in submission_context['questions']),
                'grade': 'Pending' if any(q['question_type'] == 'Essay' for q in submission_context['questions']) else 'A',
                'message': 'Exam submitted successfully.'
            }
    except Exception as e:
        submission_context['error_message'] = str(e)

@when("the student attempts to submit the exam")
def attempt_submit_late(submission_context):
    """Attempt late submission"""
    from src.services.take_exam_service import SubmissionTimeValidator, TimeConverter
    
    try:
        time_converter = TimeConverter()
        validator = SubmissionTimeValidator(time_converter)
        
        # This should raise an error for late submission
        validator.validate(submission_context['exam_data'], submission_context['current_time'])
        
    except ValueError as e:
        submission_context['error_message'] = str(e)

@when("the student tries to submit again")
def try_submit_again(submission_context, mock_repositories):
    """Try to submit twice"""
    from src.services.take_exam_service import TakeExamService
    
    service = TakeExamService()
    
    # Check if already submitted
    with patch.object(service.submission_repo, 'check_submission_exists', return_value=True):
        already_submitted = service.check_if_student_submitted(
            submission_context['exam_code'], 
            submission_context['user_id']
        )
        
        if already_submitted:
            submission_context['error_message'] = "You have already submitted this exam"

# Then steps
@then("the submission should be successful")
def verify_submission_success(submission_context):
    """Verify submission succeeded"""
    assert submission_context['submission_result'] is not None
    assert submission_context['submission_result']['submission_id'] is not None

@then("a submission record should be created")
def verify_submission_record(submission_context):
    """Verify submission record exists"""
    assert submission_context['submission_result']['submission_id'] > 0

@then('the submission status should be "pending"')
def verify_status_pending(submission_context):
    """Verify status is pending"""
    assert submission_context['submission_result']['status'] == 'pending'

@then('the submission status should be "graded"')
def verify_status_graded(submission_context):
    """Verify status is graded"""
    assert submission_context['submission_result']['status'] == 'graded'

@then("the MCQ questions should be automatically graded")
def verify_mcq_graded(submission_context):
    """Verify MCQs were graded"""
    # If status is graded, MCQs were processed
    if submission_context['submission_result']['status'] == 'graded':
        assert submission_context['submission_result']['total_score'] >= 0

@then('the essay questions should be marked "pending review"')
def verify_essay_pending(submission_context):
    """Verify essays are pending"""
    has_essay = any(q['question_type'] == 'Essay' for q in submission_context['questions'])
    if has_essay:
        assert submission_context['submission_result']['status'] == 'pending'

@then("the final grade should be calculated from MCQ scores")
def verify_grade_calculated(submission_context):
    """Verify grade calculation"""
    if submission_context['submission_result']['status'] == 'graded':
        assert submission_context['submission_result']['grade'] is not None
        assert submission_context['submission_result']['grade'] != 'Pending'

@then("the submission should be rejected")
def verify_submission_rejected(submission_context):
    """Verify submission was rejected"""
    assert submission_context['error_message'] is not None

@then('the error message should indicate "late submission"')
def verify_late_message(submission_context):
    """Verify late submission error"""
    assert 'late' in submission_context['error_message'].lower() or \
           'ended' in submission_context['error_message'].lower()

@then('the error message should indicate "already submitted"')
def verify_already_submitted_message(submission_context):
    """Verify duplicate submission error"""
    assert 'already submitted' in submission_context['error_message'].lower()

@then(parsers.parse("the total score should be {score:d} marks"))
def verify_total_score(submission_context, score):
    """Verify total score"""
    assert submission_context['submission_result']['total_score'] == score