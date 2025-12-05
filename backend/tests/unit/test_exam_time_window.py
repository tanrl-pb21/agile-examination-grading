# tests/unit/test_exam_time_window.py
"""
Unit tests for ExamTimeWindow class
Tests time-based logic for exam availability and countdown
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.services.take_exam_service import ExamTimeWindow


class TestExamTimeWindow:
    """Test suite for exam time window functionality"""
    
    @pytest.fixture
    def exam_time_window(self):
        """Create a standard exam time window (9:00 AM - 11:00 AM)"""
        tz = timezone(timedelta(hours=8))  # Malaysia timezone
        start_dt = datetime(2025, 12, 1, 9, 0, 0, tzinfo=tz)
        end_dt = datetime(2025, 12, 1, 11, 0, 0, tzinfo=tz)
        return ExamTimeWindow(start_dt, end_dt)
    
    # ==================
    # Initialization Tests
    # ==================
    
    def test_initialization(self, exam_time_window):
        """Test that time window initializes correctly"""
        assert exam_time_window.start_dt is not None
        assert exam_time_window.end_dt is not None
        assert exam_time_window.end_dt > exam_time_window.start_dt
    
    # ==================
    # is_before_start Tests
    # ==================
    
    def test_is_before_start_true(self, exam_time_window):
        """Test time before exam start"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 8, 30, 0, tzinfo=tz)  # 8:30 AM
        assert exam_time_window.is_before_start(current_time) is True
    
    def test_is_before_start_false_at_start(self, exam_time_window):
        """Test time at exact exam start"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 9, 0, 0, tzinfo=tz)  # 9:00 AM
        assert exam_time_window.is_before_start(current_time) is False
    
    def test_is_before_start_false_during_exam(self, exam_time_window):
        """Test time during exam"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 0, 0, tzinfo=tz)  # 10:00 AM
        assert exam_time_window.is_before_start(current_time) is False
    
    # ==================
    # is_after_end Tests
    # ==================
    
    def test_is_after_end_true(self, exam_time_window):
        """Test time after exam end"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 30, 0, tzinfo=tz)  # 11:30 AM
        assert exam_time_window.is_after_end(current_time) is True
    
    def test_is_after_end_false_at_end(self, exam_time_window):
        """Test time at exact exam end"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 0, 0, tzinfo=tz)  # 11:00 AM
        assert exam_time_window.is_after_end(current_time) is False
    
    def test_is_after_end_false_during_exam(self, exam_time_window):
        """Test time during exam"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 0, 0, tzinfo=tz)  # 10:00 AM
        assert exam_time_window.is_after_end(current_time) is False
    
    # ==================
    # is_within_window Tests
    # ==================
    
    def test_is_within_window_true_at_start(self, exam_time_window):
        """Test at exact start time"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 9, 0, 0, tzinfo=tz)
        assert exam_time_window.is_within_window(current_time) is True
    
    def test_is_within_window_true_during_exam(self, exam_time_window):
        """Test during exam"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 30, 0, tzinfo=tz)
        assert exam_time_window.is_within_window(current_time) is True
    
    def test_is_within_window_true_at_end(self, exam_time_window):
        """Test at exact end time"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 0, 0, tzinfo=tz)
        assert exam_time_window.is_within_window(current_time) is True
    
    def test_is_within_window_false_before(self, exam_time_window):
        """Test before exam starts"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 8, 0, 0, tzinfo=tz)
        assert exam_time_window.is_within_window(current_time) is False
    
    def test_is_within_window_false_after(self, exam_time_window):
        """Test after exam ends"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 30, 0, tzinfo=tz)
        assert exam_time_window.is_within_window(current_time) is False
    
    # ==================
    # get_duration_seconds Tests
    # ==================
    
    def test_get_duration_seconds_two_hours(self, exam_time_window):
        """Test 2-hour exam duration"""
        duration = exam_time_window.get_duration_seconds()
        expected = 2 * 60 * 60  # 7200 seconds
        assert duration == expected
    
    def test_get_duration_seconds_different_duration(self):
        """Test different exam durations"""
        tz = timezone(timedelta(hours=8))
        
        # 1 hour exam
        start = datetime(2025, 12, 1, 9, 0, 0, tzinfo=tz)
        end = datetime(2025, 12, 1, 10, 0, 0, tzinfo=tz)
        window = ExamTimeWindow(start, end)
        assert window.get_duration_seconds() == 3600
        
        # 30 minute exam
        start = datetime(2025, 12, 1, 9, 0, 0, tzinfo=tz)
        end = datetime(2025, 12, 1, 9, 30, 0, tzinfo=tz)
        window = ExamTimeWindow(start, end)
        assert window.get_duration_seconds() == 1800
    
    # ==================
    # get_remaining_seconds Tests
    # ==================
    
    def test_get_remaining_seconds_at_start(self, exam_time_window):
        """Test remaining time at start"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 9, 0, 0, tzinfo=tz)
        remaining = exam_time_window.get_remaining_seconds(current_time)
        assert remaining == 7200  # 2 hours
    
    def test_get_remaining_seconds_halfway(self, exam_time_window):
        """Test remaining time halfway through"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 0, 0, tzinfo=tz)  # 1 hour in
        remaining = exam_time_window.get_remaining_seconds(current_time)
        assert remaining == 3600  # 1 hour left
    
    def test_get_remaining_seconds_near_end(self, exam_time_window):
        """Test remaining time near end"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 55, 0, tzinfo=tz)  # 5 min left
        remaining = exam_time_window.get_remaining_seconds(current_time)
        assert remaining == 300  # 5 minutes
    
    def test_get_remaining_seconds_at_end(self, exam_time_window):
        """Test remaining time at exact end"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 0, 0, tzinfo=tz)
        remaining = exam_time_window.get_remaining_seconds(current_time)
        assert remaining == 0
    
    def test_get_remaining_seconds_after_end(self, exam_time_window):
        """Test remaining time after end (should be 0)"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 30, 0, tzinfo=tz)
        remaining = exam_time_window.get_remaining_seconds(current_time)
        assert remaining == 0  # Should return 0, not negative
    
    # ==================
    # get_minutes_late Tests
    # ==================
    
    def test_get_minutes_late_not_late(self, exam_time_window):
        """Test when submission is on time"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 10, 30, 0, tzinfo=tz)
        minutes_late = exam_time_window.get_minutes_late(current_time)
        assert minutes_late == 0
    
    def test_get_minutes_late_at_end(self, exam_time_window):
        """Test at exact end time"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 0, 0, tzinfo=tz)
        minutes_late = exam_time_window.get_minutes_late(current_time)
        assert minutes_late == 0
    
    def test_get_minutes_late_5_minutes(self, exam_time_window):
        """Test 5 minutes late"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 5, 0, tzinfo=tz)
        minutes_late = exam_time_window.get_minutes_late(current_time)
        assert minutes_late == 5
    
    def test_get_minutes_late_30_minutes(self, exam_time_window):
        """Test 30 minutes late"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, 11, 30, 0, tzinfo=tz)
        minutes_late = exam_time_window.get_minutes_late(current_time)
        assert minutes_late == 30
    
    # ==================
    # Parametrized Tests
    # ==================
    
    @pytest.mark.parametrize("hour,minute,expected_remaining", [
        (9, 0, 7200),    # Start: 2 hours
        (9, 30, 5400),   # 1.5 hours
        (10, 0, 3600),   # 1 hour
        (10, 30, 1800),  # 30 minutes
        (10, 45, 900),   # 15 minutes
        (10, 55, 300),   # 5 minutes
        (11, 0, 0),      # End: 0 seconds
    ])
    def test_remaining_seconds_parametrized(self, exam_time_window, hour, minute, expected_remaining):
        """Test various times and expected remaining seconds"""
        tz = timezone(timedelta(hours=8))
        current_time = datetime(2025, 12, 1, hour, minute, 0, tzinfo=tz)
        actual_remaining = exam_time_window.get_remaining_seconds(current_time)
        assert actual_remaining == expected_remaining