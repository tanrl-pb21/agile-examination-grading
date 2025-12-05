# tests/unit/test_mcq_grader.py
"""
Unit tests for MCQAnswerGrader class
Tests the core grading logic in isolation
"""

import pytest
from src.services.take_exam_service import MCQAnswerGrader


class TestMCQAnswerGrader:
    """Test suite for MCQ grading functionality"""
    
    @pytest.fixture
    def grader(self):
        """Create a grader instance"""
        return MCQAnswerGrader()
    
    # ==================
    # Correct Answers
    # ==================
    
    def test_correct_answer_full_marks(self, grader):
        """Test that correct answer receives full marks"""
        result = grader.grade(
            selected_option_id=2,
            correct_option_id=2,
            marks=5
        )
        
        assert result['is_correct'] is True
        assert result['score'] == 5
        assert result['feedback'] == "Correct"
    
    def test_correct_answer_different_marks(self, grader):
        """Test correct answer with different mark values"""
        # 10 marks question
        result = grader.grade(selected_option_id=1, correct_option_id=1, marks=10)
        assert result['score'] == 10
        assert result['is_correct'] is True
        
        # 15 marks question
        result = grader.grade(selected_option_id=4, correct_option_id=4, marks=15)
        assert result['score'] == 15
        assert result['is_correct'] is True
        
        # 3 marks question
        result = grader.grade(selected_option_id=3, correct_option_id=3, marks=3)
        assert result['score'] == 3
        assert result['is_correct'] is True
    
    # ==================
    # Incorrect Answers
    # ==================
    
    def test_incorrect_answer_zero_marks(self, grader):
        """Test that incorrect answer receives zero marks"""
        result = grader.grade(
            selected_option_id=3,
            correct_option_id=2,
            marks=5
        )
        
        assert result['is_correct'] is False
        assert result['score'] == 0
        assert result['feedback'] == "Incorrect"
    
    def test_incorrect_answer_regardless_of_marks(self, grader):
        """Test incorrect answer gets 0 regardless of question value"""
        # High value question
        result = grader.grade(selected_option_id=1, correct_option_id=2, marks=20)
        assert result['score'] == 0
        assert result['is_correct'] is False
        
        # Low value question
        result = grader.grade(selected_option_id=4, correct_option_id=1, marks=2)
        assert result['score'] == 0
        assert result['is_correct'] is False
    
    # ==================
    # Edge Cases
    # ==================
    
    def test_single_mark_question(self, grader):
        """Test questions worth only 1 mark"""
        # Correct
        result = grader.grade(selected_option_id=1, correct_option_id=1, marks=1)
        assert result['score'] == 1
        
        # Incorrect
        result = grader.grade(selected_option_id=2, correct_option_id=1, marks=1)
        assert result['score'] == 0
    
    def test_different_option_ids(self, grader):
        """Test with various option ID combinations"""
        test_cases = [
            (1, 1, 5, True, 5),    # Option 1 correct
            (2, 2, 5, True, 5),    # Option 2 correct
            (3, 3, 5, True, 5),    # Option 3 correct
            (4, 4, 5, True, 5),    # Option 4 correct
            (1, 2, 5, False, 0),   # Wrong answer
            (4, 1, 5, False, 0),   # Wrong answer
        ]
        
        for selected, correct, marks, expected_correct, expected_score in test_cases:
            result = grader.grade(selected, correct, marks)
            assert result['is_correct'] == expected_correct
            assert result['score'] == expected_score
    
    def test_feedback_messages(self, grader):
        """Test that feedback messages are appropriate"""
        # Correct answer
        result = grader.grade(selected_option_id=2, correct_option_id=2, marks=5)
        assert result['feedback'] == "Correct"
        
        # Incorrect answer
        result = grader.grade(selected_option_id=1, correct_option_id=2, marks=5)
        assert result['feedback'] == "Incorrect"
    
    def test_return_structure(self, grader):
        """Test that the return dictionary has all required keys"""
        result = grader.grade(selected_option_id=1, correct_option_id=1, marks=5)
        
        assert 'is_correct' in result
        assert 'score' in result
        assert 'feedback' in result
        assert len(result) == 3  # No extra keys
    
    # ==================
    # Parametrized Tests
    # ==================
    
    @pytest.mark.parametrize("selected,correct,marks,expected_score,expected_correct", [
        (1, 1, 5, 5, True),      # Correct
        (2, 2, 10, 10, True),    # Correct
        (3, 3, 15, 15, True),    # Correct
        (1, 2, 5, 0, False),     # Incorrect
        (2, 1, 10, 0, False),    # Incorrect
        (4, 1, 20, 0, False),    # Incorrect
    ])
    def test_grading_combinations(self, grader, selected, correct, marks, expected_score, expected_correct):
        """Test various grading scenarios with parametrized inputs"""
        result = grader.grade(selected, correct, marks)
        
        assert result['score'] == expected_score
        assert result['is_correct'] == expected_correct
        
        if expected_correct:
            assert result['feedback'] == "Correct"
        else:
            assert result['feedback'] == "Incorrect"