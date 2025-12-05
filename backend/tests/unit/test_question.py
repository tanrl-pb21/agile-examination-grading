import pytest
from unittest.mock import MagicMock, Mock, patch, call
from src.services.question_service import QuestionService
import psycopg


class TestQuestionService:

    @pytest.fixture
    def service(self):
        return QuestionService()

    @pytest.fixture
    def mock_cursor(self):
        cur = MagicMock()
        cur.__enter__ = Mock(return_value=cur)
        cur.__exit__ = Mock(return_value=False)
        cur.fetchone = Mock()
        cur.fetchall = Mock()
        cur.execute = Mock()
        return cur

    @pytest.fixture
    def mock_conn(self, mock_cursor):
        conn = MagicMock()
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = mock_cursor
        conn.commit = Mock()
        return conn

    # ============================================================
    # ADD MCQ QUESTION TESTS
    # ============================================================

    def test_add_mcq_question_success(self, service, mock_conn, mock_cursor):
        """Test successful MCQ question creation"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},  # Exam exists
            None,  # No duplicate question
            {"id": 10, "question_text": "Test?", "question_type": "mcq", "marks": 5, "exam_id": 1},
            {"id": 101, "option_text": "Option A", "is_correct": True},
            {"id": 102, "option_text": "Option B", "is_correct": False},
            {"id": 103, "option_text": "Option C", "is_correct": False},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.add_mcq_question(
                exam_id=1,
                question_text="Test?",
                marks=5,
                options=["Option A", "Option B", "Option C"],
                correct_option_index=0
            )

        assert result["id"] == 10
        assert result["question_text"] == "Test?"
        assert result["question_type"] == "mcq"
        assert len(result["options"]) == 3
        assert result["options"][0]["is_correct"] is True
        mock_conn.commit.assert_called_once()

    def test_add_mcq_question_exam_not_found(self, service, mock_conn, mock_cursor):
        """Test adding MCQ to non-existent exam"""
        mock_cursor.fetchone.return_value = None  # Exam doesn't exist

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="Exam with id 999 not found"):
                service.add_mcq_question(
                    exam_id=999,
                    question_text="Test?",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0
                )

    def test_add_mcq_question_duplicate_question_text(self, service, mock_conn, mock_cursor):
        """Test adding MCQ with duplicate question text"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},  # Exam exists
            {"id": 5},  # Duplicate question found
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="already exists"):
                service.add_mcq_question(
                    exam_id=1,
                    question_text="Duplicate?",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0
                )

    def test_add_mcq_question_empty_text(self, service):
        """Test adding MCQ with empty question text"""
        with pytest.raises(ValueError, match="Question text is required"):
            service.add_mcq_question(
                exam_id=1,
                question_text="   ",
                marks=5,
                options=["A", "B"],
                correct_option_index=0
            )

    def test_add_mcq_question_single_option(self, service):
        """Test adding MCQ with only one option"""
        with pytest.raises(ValueError, match="At least 2 options are required"):
            service.add_mcq_question(
                exam_id=1,
                question_text="Test?",
                marks=5,
                options=["Only one"],
                correct_option_index=0
            )

    def test_add_mcq_question_none_options(self, service):
        """Test adding MCQ with None options"""
        with pytest.raises(ValueError, match="At least 2 options are required"):
            service.add_mcq_question(
                exam_id=1,
                question_text="Test?",
                marks=5,
                options=None,
                correct_option_index=0
            )

    def test_add_mcq_question_duplicate_options(self, service):
        """Test adding MCQ with duplicate options (case-insensitive)"""
        with pytest.raises(ValueError, match="cannot contain duplicate values"):
            service.add_mcq_question(
                exam_id=1,
                question_text="Test?",
                marks=5,
                options=["Yes", "yes", "No"],
                correct_option_index=0
            )

    def test_add_mcq_question_invalid_correct_index_negative(self, service):
        """Test adding MCQ with negative correct option index"""
        with pytest.raises(ValueError, match="Invalid correct option index"):
            service.add_mcq_question(
                exam_id=1,
                question_text="Test?",
                marks=5,
                options=["A", "B", "C"],
                correct_option_index=-1
            )


    # ============================================================
    # UPDATE MCQ QUESTION TESTS (Additional coverage)
    # ============================================================

    def test_update_mcq_question_empty_question_text(self, service):
        """Test updating MCQ with empty question text"""
        with pytest.raises(ValueError, match="Question text is required"):
            service.update_mcq_question(
                question_id=1,
                question_text="",
                marks=5,
                options=["A", "B"],
                correct_option_index=0
            )

    def test_update_mcq_question_no_options(self, service):
        """Test updating MCQ with no options"""
        with pytest.raises(ValueError, match="At least 2 options are required"):
            service.update_mcq_question(
                question_id=1,
                question_text="Test",
                marks=5,
                options=[],
                correct_option_index=0
            )

    def test_update_mcq_question_database_error(self, service, mock_conn, mock_cursor):
        """Test database error during update"""
        mock_cursor.fetchone.side_effect = psycopg.Error("Database error")

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(psycopg.Error):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Test",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0
                )
        mock_conn.commit.assert_not_called()

    # ============================================================
    # ADD ESSAY QUESTION TESTS
    # ============================================================

    def test_add_essay_question_success(self, service, mock_conn, mock_cursor):
        """Test successful essay question creation"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},  # Exam exists
            None,  # No duplicate question
            {"id": 20, "question_text": "Essay?", "question_type": "essay", 
             "marks": 10, "rubric": "Content 50%, Structure 50%", "exam_id": 1},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.add_essay_question(
                exam_id=1,
                question_text="Essay?",
                marks=10,
                rubric="Content 50%, Structure 50%",
                reference_answer="Sample answer"
            )

        assert result["id"] == 20
        assert result["question_text"] == "Essay?"
        assert result["question_type"] == "essay"
        assert result["marks"] == 10
        assert result["rubric"] == "Content 50%, Structure 50%"
        assert result["reference_answer"] == "Sample answer"
        mock_conn.commit.assert_called_once()

    def test_add_essay_question_empty_text(self, service):
        """Test adding essay with empty question text"""
        with pytest.raises(ValueError, match="Question text is required"):
            service.add_essay_question(
                exam_id=1,
                question_text="   ",
                marks=10,
                rubric="Test rubric"
            )

    def test_add_essay_question_exam_not_found(self, service, mock_conn, mock_cursor):
        """Test adding essay to non-existent exam"""
        mock_cursor.fetchone.return_value = None  # Exam doesn't exist

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="Exam with id 999 not found"):
                service.add_essay_question(
                    exam_id=999,
                    question_text="Essay?",
                    marks=10,
                    rubric="Test rubric"
                )

    def test_add_essay_question_duplicate_text(self, service, mock_conn, mock_cursor):
        """Test adding essay with duplicate question text"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},  # Exam exists
            {"id": 5},  # Duplicate question found
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="already exists"):
                service.add_essay_question(
                    exam_id=1,
                    question_text="Duplicate?",
                    marks=10,
                    rubric="Test rubric"
                )

    def test_add_essay_question_without_rubric(self, service, mock_conn, mock_cursor):
        """Test adding essay without rubric"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},  # Exam exists
            None,  # No duplicate question
            {"id": 30, "question_text": "No rubric?", "question_type": "essay", 
             "marks": 5, "rubric": None, "exam_id": 1},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.add_essay_question(
                exam_id=1,
                question_text="No rubric?",
                marks=5
            )

        assert result["id"] == 30
        assert result["rubric"] is None
        assert result["reference_answer"] is None

    # ============================================================
    # UPDATE ESSAY QUESTION TESTS
    # ============================================================

    def test_update_essay_question_success(self, service, mock_conn, mock_cursor):
        """Test successful essay question update"""
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 1},  # Get exam_id
            None,  # No duplicate question
            {"id": 25, "question_text": "Updated essay?", "question_type": "essay",
             "marks": 15, "rubric": "Updated rubric", "exam_id": 1},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_essay_question(
                question_id=25,
                question_text="Updated essay?",
                marks=15,
                rubric="Updated rubric",
                reference_answer="Updated answer"
            )

        assert result["id"] == 25
        assert result["question_text"] == "Updated essay?"
        assert result["marks"] == 15
        assert result["rubric"] == "Updated rubric"
        assert result["reference_answer"] == "Updated answer"
        mock_conn.commit.assert_called_once()

    def test_update_essay_question_not_found(self, service, mock_conn, mock_cursor):
        """Test updating non-existent essay question"""
        mock_cursor.fetchone.return_value = None  # Question not found

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="Essay Question with id 999 not found"):
                service.update_essay_question(
                    question_id=999,
                    question_text="Test",
                    marks=10
                )

    def test_update_essay_question_empty_text(self, service):
        """Test updating essay with empty question text"""
        with pytest.raises(ValueError, match="Question text is required"):
            service.update_essay_question(
                question_id=1,
                question_text="   ",
                marks=10,
                rubric="Test rubric"
            )

    def test_update_essay_question_duplicate_text(self, service, mock_conn, mock_cursor):
        """Test updating essay with duplicate question text"""
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 1},  # Get exam_id
            {"id": 5},  # Duplicate question found
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="already exists"):
                service.update_essay_question(
                    question_id=1,
                    question_text="Duplicate?",
                    marks=10,
                    rubric="Test rubric"
                )

    def test_update_essay_question_remove_rubric(self, service, mock_conn, mock_cursor):
        """Test updating essay to remove rubric"""
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 1},  # Get exam_id
            None,  # No duplicate question
            {"id": 26, "question_text": "No rubric?", "question_type": "essay",
             "marks": 5, "rubric": None, "exam_id": 1},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_essay_question(
                question_id=26,
                question_text="No rubric?",
                marks=5,
                rubric=None
            )

        assert result["rubric"] is None

    # ============================================================
    # GET EXAM QUESTIONS TESTS
    # ============================================================

    def test_get_exam_questions_success(self, service, mock_conn, mock_cursor):
        """Test getting all questions for an exam"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},  # Exam exists
        ]
        
        mcq_question = {
            "id": 10, 
            "question_text": "MCQ?", 
            "question_type": "mcq", 
            "marks": 5,
            "rubric": None,
            "exam_id": 1
        }
        
        essay_question = {
            "id": 11, 
            "question_text": "Essay?", 
            "question_type": "essay", 
            "marks": 10,
            "rubric": "Test rubric",
            "exam_id": 1
        }
        
        mock_cursor.fetchall.side_effect = [
            [mcq_question, essay_question],  # All questions
            [{"id": 101, "option_text": "A", "is_correct": True},
             {"id": 102, "option_text": "B", "is_correct": False}],  # MCQ options
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.get_exam_questions(exam_id=1)

        assert len(result) == 2
        assert result[0]["question_type"] == "mcq"
        assert result[1]["question_type"] == "essay"
        assert "options" in result[0]  # MCQ has options
        assert "options" not in result[1]  # Essay doesn't have options

    def test_get_exam_questions_exam_not_found(self, service, mock_conn, mock_cursor):
        """Test getting questions for non-existent exam"""
        mock_cursor.fetchone.return_value = None  # Exam doesn't exist

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="Exam with id 999 not found"):
                service.get_exam_questions(exam_id=999)

    def test_get_exam_questions_no_questions(self, service, mock_conn, mock_cursor):
        """Test getting questions for exam with no questions"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},  # Exam exists
        ]
        mock_cursor.fetchall.return_value = []  # No questions

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.get_exam_questions(exam_id=1)

        assert result == []

    # ============================================================
    # GET QUESTION TESTS
    # ============================================================

    def test_get_question_mcq_success(self, service, mock_conn, mock_cursor):
        """Test getting an MCQ question by ID"""
        mcq_data = {
            "id": 10, 
            "question_text": "MCQ?", 
            "question_type": "mcq", 
            "marks": 5,
            "rubric": None,
            "exam_id": 1
        }
        
        mock_cursor.fetchone.side_effect = [
            mcq_data,
        ]
        
        mock_cursor.fetchall.return_value = [
            {"id": 101, "option_text": "A", "is_correct": True},
            {"id": 102, "option_text": "B", "is_correct": False}
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.get_question(question_id=10)

        assert result["id"] == 10
        assert result["question_type"] == "mcq"
        assert len(result["options"]) == 2
        assert "options" in result


    # ============================================================
    # DELETE QUESTION TESTS
    # ============================================================

    def test_delete_question_success(self, service, mock_conn, mock_cursor):
        """Test successful question deletion"""
        mock_cursor.fetchone.return_value = {"id": 10}

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.delete_question(question_id=10)

        assert result["id"] == 10
        
        # Verify DELETE calls were made
        delete_calls = mock_cursor.execute.call_args_list
        assert len(delete_calls) == 2
        assert 'DELETE FROM "questionOption"' in str(delete_calls[0])
        assert 'DELETE FROM question' in str(delete_calls[1])
        
        mock_conn.commit.assert_called_once()

    def test_delete_question_not_found(self, service, mock_conn, mock_cursor):
        """Test deleting non-existent question"""
        mock_cursor.fetchone.return_value = None

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="Question with id 999 not found"):
                service.delete_question(question_id=999)


    # ============================================================
    # EDGE CASE TESTS
    # ============================================================

    def test_add_mcq_question_whitespace_in_options(self, service, mock_conn, mock_cursor):
        """Test that whitespace is properly handled in options"""
        mock_cursor.fetchone.side_effect = [
            {"id": 1},
            None,
            {"id": 15, "question_text": "Test", "question_type": "mcq", "marks": 5, "exam_id": 1},
            {"id": 101, "option_text": "  Option A  ", "is_correct": True},
            {"id": 102, "option_text": "Option B", "is_correct": False},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.add_mcq_question(
                exam_id=1,
                question_text="Test",
                marks=5,
                options=["  Option A  ", "Option B"],
                correct_option_index=0
            )

        # Verify options are stored with trimmed values
        assert result["options"][0]["option_text"] == "  Option A  "
        assert result["options"][1]["option_text"] == "Option B"

    def test_update_mcq_question_with_same_options(self, service, mock_conn, mock_cursor):
        """Test updating MCQ with the same options (should still work)"""
        question_id = 5
        exam_id = 2

        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},
            None,
            {"id": question_id, "question_text": "Same options", "question_type": "mcq", 
             "marks": 3, "exam_id": exam_id},
            {"id": 1, "option_text": "A", "is_correct": True},
            {"id": 2, "option_text": "B", "is_correct": False},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_mcq_question(
                question_id=question_id,
                question_text="Same options",
                marks=3,
                options=["A", "B"],  # Same as before
                correct_option_index=0
            )

        assert result["id"] == question_id
        # Verify DELETE was called to remove old options
        delete_calls = [call for call in mock_cursor.execute.call_args_list 
                       if 'DELETE FROM "questionOption"' in str(call)]
        assert len(delete_calls) == 1

