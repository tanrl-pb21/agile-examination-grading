# tests/unit/test_submission_time_validator.py
"""
Unit tests for SubmissionTimeValidator class
Tests submission timing validation logic
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.services.take_exam_service import SubmissionTimeValidator, TimeConverter
from unittest.mock import patch, MagicMock


class TestSubmissionTimeValidator:
    """Test suite for submission time validation"""
    
    @pytest.fixture
    def time_converter(self):
        """Create time converter instance"""
        return TimeConverter()
    
    @pytest.fixture
    def validator(self, time_converter):
        """Create validator instance"""
        return SubmissionTimeValidator(time_converter)
    
    @pytest.fixture
    def exam_data(self):
        """Standard exam data (9 AM - 11 AM)"""
        return {
            'id': 1,
            'date': '2025-12-01',
            'start_time': '09:00:00',
            'end_time': '11:00:00',
            'duration': 120
        }
    
    # ==================
    # Valid Submissions
    # ==================
    
    def test_submission_at_start_time_valid(self, validator, exam_data):
        """Test submission at exact start time is valid"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 9, 0, 0, tzinfo=tz)
        
        result = validator.validate(exam_data, current_time)
        assert result is True
    
    def test_submission_during_exam_valid(self, validator, exam_data):
        """Test submission during exam is valid"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 0, 0, tzinfo=tz)
        
        result = validator.validate(exam_data, current_time)
        assert result is True
    
    def test_submission_at_end_time_valid(self, validator, exam_data):
        """Test submission at exact end time is valid"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 0, 0, tzinfo=tz)
        
        result = validator.validate(exam_data, current_time)
        assert result is True
    
    def test_submission_near_end_valid(self, validator, exam_data):
        """Test submission near end time is valid"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 59, 0, tzinfo=tz)
        
        result = validator.validate(exam_data, current_time)
        assert result is True
    
    # ==================
    # Before Start - Invalid
    # ==================
    
    def test_submission_before_start_raises_error(self, validator, exam_data):
        """Test submission before start time raises error"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 8, 30, 0, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        error_msg = str(exc_info.value)
        assert "Cannot submit exam before start time" in error_msg
        assert "09:00" in error_msg
    
    def test_submission_one_minute_before_start_raises_error(self, validator, exam_data):
        """Test submission 1 minute before start raises error"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 8, 59, 0, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        assert "Cannot submit exam before start time" in str(exc_info.value)
    
    # ==================
    # After End - Invalid
    # ==================
    
    def test_submission_after_end_raises_error(self, validator, exam_data):
        """Test submission after end time raises error"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 30, 0, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        error_msg = str(exc_info.value)
        assert "Submission rejected" in error_msg
        assert "ended at 11:00" in error_msg
        assert "30 minute(s) late" in error_msg
    
    def test_submission_one_minute_late_raises_error(self, validator, exam_data):
        """Test submission 1 minute late raises error"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 1, 0, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        error_msg = str(exc_info.value)
        assert "1 minute(s) late" in error_msg
    
    def test_submission_five_minutes_late_raises_error(self, validator, exam_data):
        """Test submission 5 minutes late raises error"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 5, 0, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        error_msg = str(exc_info.value)
        assert "5 minute(s) late" in error_msg
    
    # ==================
    # Edge Cases
    # ==================
    
    def test_submission_one_second_after_end_raises_error(self, validator, exam_data):
        """Test submission 1 second after end raises error"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 0, 1, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        # Should be 0 minutes late (rounds down)
        error_msg = str(exc_info.value)
        assert "Submission rejected" in error_msg
    
    def test_different_exam_times(self, validator):
        """Test validation with different exam times"""
        tz = timezone(timedelta(hours=8))
        
        # Afternoon exam: 2 PM - 4 PM
        exam_data = {
            'date': '2025-12-01',
            'start_time': '14:00:00',
            'end_time': '16:00:00',
        }
        
        # Valid: 3 PM
        current_time = datetime(2025, 12, 1, 15, 0, 0, tzinfo=tz)
        assert validator.validate(exam_data, current_time) is True
        
        # Invalid: 1 PM (before)
        current_time = datetime(2025, 12, 1, 13, 0, 0, tzinfo=tz)
        with pytest.raises(ValueError):
            validator.validate(exam_data, current_time)
        
        # Invalid: 5 PM (after)
        current_time = datetime(2025, 12, 1, 17, 0, 0, tzinfo=tz)
        with pytest.raises(ValueError):
            validator.validate(exam_data, current_time)
    
    # ==================
    # Error Message Content
    # ==================
    
    def test_before_start_error_message_format(self, validator, exam_data):
        """Test error message format for before-start submissions"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 8, 0, 0, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        error_msg = str(exc_info.value)
        assert "Cannot submit exam before start time" in error_msg
        assert "Exam starts at 09:00" in error_msg
        assert "2025-12-01" in error_msg
    
    def test_late_submission_error_message_format(self, validator, exam_data):
        """Test error message format for late submissions"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 15, 0, tzinfo=tz)
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(exam_data, current_time)
        
        error_msg = str(exc_info.value)
        assert "Submission rejected" in error_msg
        assert "exam ended at 11:00" in error_msg
        assert "15 minute(s) late" in error_msg
        assert "Late submissions are not accepted" in error_msg
    
    # ==================
    # Parametrized Tests
    # ==================
    
    @pytest.mark.parametrize("hour,minute,should_pass", [
        (8, 30, False),   # Before start
        (8, 59, False),   # 1 min before
        (9, 0, True),     # At start
        (9, 30, True),    # During exam
        (10, 0, True),    # Midpoint
        (10, 30, True),   # During exam
        (11, 0, True),    # At end
        (11, 1, False),   # 1 min late
        (11, 30, False),  # 30 min late
    ])
    def test_various_submission_times(self, validator, exam_data, hour, minute, should_pass):
        """Test validation with various submission times"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, hour, minute, 0, tzinfo=tz)
        
        if should_pass:
            result = validator.validate(exam_data, current_time)
            assert result is True
        else:
            with pytest.raises(ValueError):
                validator.validate(exam_data, current_time)

