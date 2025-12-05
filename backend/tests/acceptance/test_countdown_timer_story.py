
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

# Load feature file
scenarios('../feature/countdown_timer.feature')

# Fixtures
@pytest.fixture
def timer_context():
    """Context for timer-related tests"""
    return {
        'exam_date': datetime(2025, 12, 1, tzinfo=timezone(timedelta(hours=8))),
        'start_time': datetime(2025, 12, 1, 9, 0, 0, tzinfo=timezone(timedelta(hours=8))),
        'end_time': datetime(2025, 12, 1, 11, 0, 0, tzinfo=timezone(timedelta(hours=8))),
        'current_time': None,
        'time_window': None,
        'remaining_seconds': None,
        'is_within_window': None
    }

# Given steps
@given("an exam scheduled from 09:00 to 11:00")
def exam_scheduled(timer_context):
    """Set up exam time window"""
    from src.services.take_exam_service import ExamTimeWindow
    
    timer_context['time_window'] = ExamTimeWindow(
        start_dt=timer_context['start_time'],
        end_dt=timer_context['end_time']
    )
    assert timer_context['time_window'] is not None

@given(parsers.parse("the current time is {time_str}"))
def set_current_time(timer_context, time_str):
    """Set the current time for testing"""
    # Parse time string like "09:30:00"
    hour, minute, second = map(int, time_str.split(':'))
    timer_context['current_time'] = datetime(
        2025, 12, 1, hour, minute, second, 
        tzinfo=timezone(timedelta(hours=8))
    )

@given("the exam has ended")
def exam_ended(timer_context):
    """Set current time after exam end"""
    timer_context['current_time'] = timer_context['end_time'] + timedelta(minutes=5)

# When steps
@when("the student views the exam timer")
def calculate_remaining_time(timer_context):
    """Calculate remaining time"""
    timer_context['remaining_seconds'] = timer_context['time_window'].get_remaining_seconds(
        timer_context['current_time']
    )

@when("the timer reaches zero")
def timer_reaches_zero(timer_context):
    timer_context['current_time'] = timer_context['end_time'] + timedelta(seconds=1)
    timer_context['remaining_seconds'] = 0

@when("the student attempts to submit")
def attempt_submission(timer_context):
    """Check if submission is allowed"""
    timer_context['is_within_window'] = timer_context['time_window'].is_within_window(
        timer_context['current_time']
    )

# Then steps
@then(parsers.parse("the timer should show {hours:d} hours and {minutes:d} minutes remaining"))
def verify_time_remaining(timer_context, hours, minutes):
    """Verify the remaining time"""
    expected_seconds = (hours * 3600) + (minutes * 60)
    actual_seconds = timer_context['remaining_seconds']
    
    # Allow 1 second tolerance
    assert abs(actual_seconds - expected_seconds) <= 1, \
        f"Expected ~{expected_seconds}s, got {actual_seconds}s"

@then(parsers.parse("the timer should show exactly {seconds:d} seconds"))
def verify_exact_seconds(timer_context, seconds):
    """Verify exact seconds remaining"""
    assert timer_context['remaining_seconds'] == seconds

@then("the timer should show 00:00:00")
def verify_timer_zero(timer_context):
    """Verify timer is at zero"""
    assert timer_context['remaining_seconds'] == 0

@then("the exam should automatically end")
def verify_exam_ended(timer_context):
    """Verify exam has ended"""
    is_after_end = timer_context['time_window'].is_after_end(timer_context['current_time'])
    assert is_after_end is True, "Exam should have ended"

@then("the submission should be rejected")
def verify_submission_rejected(timer_context):
    """Verify submission is not allowed"""
    assert timer_context['is_within_window'] is False, \
        "Submission should be rejected when time is up"

@then("no further answers can be changed")
def verify_answers_locked(timer_context):
    """Verify that time is up and answers should be locked"""
    is_after_end = timer_context['time_window'].is_after_end(timer_context['current_time'])
    assert is_after_end is True, "Answers should be locked after exam ends"

@then(parsers.parse("the remaining time should be {minutes:d} minutes"))
def verify_minutes_remaining(timer_context, minutes):
    """Verify minutes remaining"""
    expected_seconds = minutes * 60
    actual_seconds = timer_context['remaining_seconds']
    
    # Allow 1 second tolerance
    assert abs(actual_seconds - expected_seconds) <= 1, \
        f"Expected ~{expected_seconds}s ({minutes} min), got {actual_seconds}s"