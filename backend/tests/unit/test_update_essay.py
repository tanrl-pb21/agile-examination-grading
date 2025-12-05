import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.question_service import QuestionService


class TestUpdateEssayQuestion:
    """Unit tests for update_essay_question service method"""

    @pytest.fixture
    def service(self):
        """Create QuestionService instance"""
        return QuestionService()

    @pytest.fixture
    def mock_cursor(self):
        """Create a mock cursor"""
        cursor = MagicMock()
        cursor.__enter__ = Mock(return_value=cursor)
        cursor.__exit__ = Mock(return_value=False)
        return cursor

    @pytest.fixture
    def mock_conn(self, mock_cursor):
        """Create a mock connection"""
        conn = MagicMock()
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = mock_cursor
        return conn

    # ===== POSITIVE SCENARIOS =====

    def test_update_essay_question_success(self, service, mock_conn, mock_cursor):
        """Test successful update of essay question"""
        # Arrange
        question_id = 1
        question_text = "What is machine learning?"
        marks = 15
        rubric = "Updated rubric"
        reference_answer = "ML is a subset of AI"
        
        # Mock exam_id fetch
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 100},  # First call: get exam_id
            None,  # Second call: duplicate check (no duplicate)
            {  # Third call: update result
                "id": question_id,
                "question_text": question_text,
                "question_type": "essay",
                "marks": marks,
                "rubric": rubric,
                "exam_id": 100
            }
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act
            result = service.update_essay_question(
                question_id=question_id,
                question_text=question_text,
                marks=marks,
                rubric=rubric,
                reference_answer=reference_answer
            )

        # Assert
        assert result["id"] == question_id
        assert result["question_text"] == question_text
        assert result["marks"] == marks
        assert result["rubric"] == rubric
        assert result["reference_answer"] == reference_answer
        mock_conn.commit.assert_called_once()

    def test_update_essay_question_with_minimal_data(self, service, mock_conn, mock_cursor):
        """Test update with only required fields"""
        # Arrange
        question_id = 1
        question_text = "Explain neural networks"
        marks = 20
        
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 100},
            None,
            {
                "id": question_id,
                "question_text": question_text,
                "question_type": "essay",
                "marks": marks,
                "rubric": None,
                "exam_id": 100
            }
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act
            result = service.update_essay_question(
                question_id=question_id,
                question_text=question_text,
                marks=marks
            )

        # Assert
        assert result["id"] == question_id
        assert result["question_text"] == question_text
        assert result["marks"] == marks
        assert result["rubric"] is None
        assert result["word_limit"] is None
        assert result["reference_answer"] is None

    def test_update_essay_question_trims_whitespace(self, service, mock_conn, mock_cursor):
        """Test that question text whitespace is trimmed"""
        # Arrange
        question_id = 1
        question_text_with_spaces = "  What is AI?  "
        expected_text = "What is AI?"
        
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 100},
            None,
            {
                "id": question_id,
                "question_text": expected_text,
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
                "exam_id": 100
            }
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act
            result = service.update_essay_question(
                question_id=question_id,
                question_text=question_text_with_spaces,
                marks=10
            )

        # Assert
        assert result["question_text"] == expected_text

    def test_update_essay_question_with_all_optional_fields(self, service, mock_conn, mock_cursor):
        """Test update with all optional fields provided"""
        # Arrange
        question_id = 1
        
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 100},
            None,
            {
                "id": question_id,
                "question_text": "Complete question",
                "question_type": "essay",
                "marks": 25,
                "rubric": "Detailed rubric",
                "exam_id": 100
            }
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act
            result = service.update_essay_question(
                question_id=question_id,
                question_text="Complete question",
                marks=25,
                rubric="Detailed rubric",
                word_limit=500,
                reference_answer="Reference answer"
            )

        # Assert
        assert result["word_limit"] == 500
        assert result["reference_answer"] == "Reference answer"

    # ===== NEGATIVE SCENARIOS =====

    def test_update_essay_question_empty_text_raises_error(self, service, mock_conn, mock_cursor):
        """Test that empty question text raises ValueError"""
        # Arrange
        question_id = 1
        
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act & Assert
            with pytest.raises(ValueError, match="Question text is required"):
                service.update_essay_question(
                    question_id=question_id,
                    question_text="",
                    marks=10
                )

    def test_update_essay_question_whitespace_only_text_raises_error(self, service, mock_conn, mock_cursor):
        """Test that whitespace-only question text raises ValueError"""
        # Arrange
        question_id = 1
        
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act & Assert
            with pytest.raises(ValueError, match="Question text is required"):
                service.update_essay_question(
                    question_id=question_id,
                    question_text="   ",
                    marks=10
                )

    def test_update_essay_question_none_text_raises_error(self, service, mock_conn, mock_cursor):
        """Test that None question text raises ValueError"""
        # Arrange
        question_id = 1
        
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act & Assert
            with pytest.raises(ValueError, match="Question text is required"):
                service.update_essay_question(
                    question_id=question_id,
                    question_text=None,
                    marks=10
                )

    def test_update_essay_question_not_found(self, service, mock_conn, mock_cursor):
        """Test update fails when question doesn't exist"""
        # Arrange
        question_id = 999
        mock_cursor.fetchone.return_value = None

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act & Assert
            with pytest.raises(ValueError, match=f"Essay Question with id {question_id} not found"):
                service.update_essay_question(
                    question_id=question_id,
                    question_text="Some question",
                    marks=10
                )

    def test_update_essay_question_duplicate_text_in_same_exam(self, service, mock_conn, mock_cursor):
        """Test update fails when duplicate question text exists in same exam"""
        # Arrange
        question_id = 1
        exam_id = 100
        duplicate_text = "What is Python?"
        
        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},  # First call: get exam_id
            {"id": 2}  # Second call: duplicate found
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act & Assert
            with pytest.raises(ValueError, match=f"A question with the same text already exists in exam {exam_id}"):
                service.update_essay_question(
                    question_id=question_id,
                    question_text=duplicate_text,
                    marks=10
                )

    def test_update_essay_question_case_insensitive_duplicate_check(self, service, mock_conn, mock_cursor):
        """Test duplicate check is case-insensitive"""
        # Arrange
        question_id = 1
        exam_id = 100
        
        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},
            {"id": 2}  # Duplicate found
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act & Assert
            with pytest.raises(ValueError, match="already exists"):
                service.update_essay_question(
                    question_id=question_id,
                    question_text="WHAT IS PYTHON?",
                    marks=10
                )

    def test_update_essay_question_allows_same_text_different_exam(self, service, mock_conn, mock_cursor):
        """Test that same question text is allowed in different exams"""
        # Arrange
        question_id = 1
        question_text = "What is Java?"
        
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 100},  # This question is in exam 100
            None,  # No duplicate in exam 100
            {
                "id": question_id,
                "question_text": question_text,
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
                "exam_id": 100
            }
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act
            result = service.update_essay_question(
                question_id=question_id,
                question_text=question_text,
                marks=10
            )

        # Assert
        assert result["question_text"] == question_text
        mock_conn.commit.assert_called_once()

    def test_update_essay_question_commit_called(self, service, mock_conn, mock_cursor):
        """Test that database commit is called on successful update"""
        # Arrange
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 100},
            None,
            {
                "id": 1,
                "question_text": "Test",
                "question_type": "essay",
                "marks": 10,
                "rubric": None,
                "exam_id": 100
            }
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Act
            service.update_essay_question(
                question_id=1,
                question_text="Test",
                marks=10
            )

        # Assert
        mock_conn.commit.assert_called_once()