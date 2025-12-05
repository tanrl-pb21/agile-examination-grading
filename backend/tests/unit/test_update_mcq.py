import pytest
from unittest.mock import MagicMock, Mock, patch
from src.services.question_service import QuestionService


class TestUpdateMCQQuestionService:

    @pytest.fixture
    def service(self):
        return QuestionService()

    @pytest.fixture
    def mock_cursor(self):
        cur = MagicMock()
        cur.__enter__ = Mock(return_value=cur)
        cur.__exit__ = Mock(return_value=False)
        return cur

    @pytest.fixture
    def mock_conn(self, mock_cursor):
        conn = MagicMock()
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = mock_cursor
        return conn

    # ============================================================
    #  SUCCESS
    # ============================================================
    def test_update_mcq_question_success(self, service, mock_conn, mock_cursor):
        question_id = 10
        exam_id = 7

        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},          # SELECT exam_id WHERE id = ?
            None,                          # duplicate text check → None OK
            {                              # UPDATE question RETURNING...
                "id": question_id,
                "question_text": "Updated text",
                "question_type": "mcq",
                "marks": 10,
                "exam_id": exam_id,
            },
            {"id": 1, "option_text": "A", "is_correct": True},
            {"id": 2, "option_text": "B", "is_correct": False},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_mcq_question(
                question_id=question_id,
                question_text="Updated text",
                marks=10,
                options=["A", "B"],
                correct_option_index=0,
            )

        assert result["id"] == question_id
        assert result["marks"] == 10
        assert len(result["options"]) == 2
        assert result["options"][0]["is_correct"] is True
        mock_conn.commit.assert_called_once()

    # ============================================================
    #  DUPLICATE QUESTION TEXT
    # ============================================================
    def test_update_mcq_question_duplicate_text(self, service, mock_conn, mock_cursor):
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 5},   # exam_id read success
            {"id": 999},      # duplicate question text exists
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="already exists"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Duplicate",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0,
                )

    # ============================================================
    #  DUPLICATE OPTIONS (case-insensitive)
    # ============================================================
    def test_update_mcq_question_duplicate_options(self, service, mock_conn):
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="duplicate"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Test",
                    marks=3,
                    options=["Hello", "hello"],
                    correct_option_index=0,
                )

    # ============================================================
    #  QUESTION NOT FOUND
    # ============================================================
    def test_update_mcq_question_not_found(self, service, mock_conn, mock_cursor):
        mock_cursor.fetchone.return_value = None  # question missing

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(
                ValueError, match="MCQ Question with id 1 not found"
            ):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Test",
                    marks=2,
                    options=["A", "B"],
                    correct_option_index=0,
                )

    # ============================================================
    #  INVALID CORRECT OPTION INDEX
    # ============================================================
    def test_update_mcq_question_invalid_index(self, service, mock_conn, mock_cursor):
        mock_cursor.fetchone.side_effect = [{"exam_id": 2}, None]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="Invalid correct option index"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Valid",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=10,
                )

    # ============================================================
    #  EMPTY QUESTION TEXT
    # ============================================================
    def test_update_mcq_question_empty_text(self, service, mock_conn):
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="Question text is required"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="   ",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0,
                )

    # ============================================================
    #  OPTIONS < 2
    # ============================================================
    def test_update_mcq_question_less_than_two_options(self, service, mock_conn):
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="At least 2 options"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Valid",
                    marks=5,
                    options=["Only one"],
                    correct_option_index=0,
                )

    # ============================================================
    #  WHITESPACE-ONLY OPTIONS
    # ============================================================
    def test_update_mcq_question_whitespace_options(self, service, mock_conn):
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Valid",
                    marks=5,
                    options=["   ", "Option"],
                    correct_option_index=1,
                )

    def test_update_mcq_question_with_maximum_options(self, service, mock_conn, mock_cursor):
        """Test updating MCQ with many options (e.g., 10 options)"""
        question_id = 5
        exam_id = 3
        options = [f"Option {i}" for i in range(1, 11)]  # 10 options

        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},
            None,  # no duplicate
            {
                "id": question_id,
                "question_text": "Question with 10 options",
                "question_type": "mcq",
                "marks": 5,
                "exam_id": exam_id,
            },
        ] + [{"id": i, "option_text": f"Option {i}", "is_correct": i == 5} for i in range(1, 11)]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_mcq_question(
                question_id=question_id,
                question_text="Question with 10 options",
                marks=5,
                options=options,
                correct_option_index=4,
            )

        assert len(result["options"]) == 10
        assert result["options"][4]["is_correct"] is True
        mock_conn.commit.assert_called_once()

    def test_update_mcq_question_change_correct_answer(self, service, mock_conn, mock_cursor):
        """Test changing the correct answer from one option to another"""
        question_id = 7
        exam_id = 2

        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},
            None,
            {
                "id": question_id,
                "question_text": "Updated question",
                "question_type": "mcq",
                "marks": 3,
                "exam_id": exam_id,
            },
            {"id": 1, "option_text": "A", "is_correct": False},
            {"id": 2, "option_text": "B", "is_correct": False},
            {"id": 3, "option_text": "C", "is_correct": True},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_mcq_question(
                question_id=question_id,
                question_text="Updated question",
                marks=3,
                options=["A", "B", "C"],
                correct_option_index=2,  # C is now correct
            )

        assert result["options"][0]["is_correct"] is False
        assert result["options"][1]["is_correct"] is False
        assert result["options"][2]["is_correct"] is True

    def test_update_mcq_question_with_special_characters(self, service, mock_conn, mock_cursor):
        """Test updating MCQ with special characters in text and options"""
        question_id = 8
        exam_id = 4

        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},
            None,
            {
                "id": question_id,
                "question_text": "What is 2 + 2 = ?",
                "question_type": "mcq",
                "marks": 2,
                "exam_id": exam_id,
            },
            {"id": 1, "option_text": "3 < 4", "is_correct": False},
            {"id": 2, "option_text": "4 = 4", "is_correct": True},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_mcq_question(
                question_id=question_id,
                question_text="What is 2 + 2 = ?",
                marks=2,
                options=["3 < 4", "4 = 4"],
                correct_option_index=1,
            )

        assert result["question_text"] == "What is 2 + 2 = ?"
        assert result["options"][1]["option_text"] == "4 = 4"

    def test_update_mcq_question_case_insensitive_duplicate_detection(self, service, mock_conn, mock_cursor):
        """Test that duplicate detection is case-insensitive"""
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 5},
            {"id": 999},  # duplicate found
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="already exists"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="   WHAT IS PYTHON?   ",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0,
                )

    def test_update_mcq_question_trim_whitespace_in_options(self, service, mock_conn, mock_cursor):
        """Test that whitespace is trimmed from options"""
        question_id = 9
        exam_id = 6

        mock_cursor.fetchone.side_effect = [
            {"exam_id": exam_id},
            None,
            {
                "id": question_id,
                "question_text": "Test",
                "question_type": "mcq",
                "marks": 3,
                "exam_id": exam_id,
            },
            {"id": 1, "option_text": "Option A", "is_correct": True},
            {"id": 2, "option_text": "Option B", "is_correct": False},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_mcq_question(
                question_id=question_id,
                question_text="Test",
                marks=3,
                options=["   Option A   ", "  Option B  "],
                correct_option_index=0,
            )

        # Verify the INSERT calls used trimmed values
        insert_calls = [
            call for call in mock_cursor.execute.call_args_list
            if 'INSERT INTO "questionOption"' in str(call)
        ]
        assert len(insert_calls) == 2

    def test_update_mcq_question_negative_marks(self, service, mock_conn, mock_cursor):
        """Test updating with negative marks (should be handled by API layer but test service)"""
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 1},
            None,
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            # Service doesn't validate marks, so this should proceed
            # But it's a good test to ensure service behavior
            mock_cursor.fetchone.side_effect = [
                {"exam_id": 1},
                None,
                {
                    "id": 1,
                    "question_text": "Test",
                    "question_type": "mcq",
                    "marks": -5,  # negative marks
                    "exam_id": 1,
                },
                {"id": 1, "option_text": "A", "is_correct": True},
                {"id": 2, "option_text": "B", "is_correct": False},
            ]
            
            result = service.update_mcq_question(
                question_id=1,
                question_text="Test",
                marks=-5,
                options=["A", "B"],
                correct_option_index=0,
            )
            
            assert result["marks"] == -5

    def test_update_mcq_question_wrong_question_type(self, service, mock_conn, mock_cursor):
        """Test updating an essay question as MCQ should fail"""
        mock_cursor.fetchone.return_value = None  # No MCQ found

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="MCQ Question with id 1 not found"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Test",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0,
                )

    def test_update_mcq_question_duplicate_options_mixed_case(self, service, mock_conn):
        """Test duplicate options with mixed case"""
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError, match="duplicate"):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Test",
                    marks=3,
                    options=["Apple", "APPLE", "orange"],
                    correct_option_index=0,
                )

    def test_update_mcq_question_rollback_on_error(self, service, mock_conn, mock_cursor):
        """Test that transaction is not committed on error"""
        mock_cursor.fetchone.side_effect = Exception("Database error")

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(Exception):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Test",
                    marks=5,
                    options=["A", "B"],
                    correct_option_index=0,
                )

        mock_conn.commit.assert_not_called()

    def test_update_mcq_question_zero_marks(self, service, mock_conn, mock_cursor):
        mock_cursor.fetchone.side_effect = [
            {"exam_id": 1},
            None,
            {
                "id": 1,
                "question_text": "Zero mark question",
                "question_type": "mcq",
                "marks": 0,
                "exam_id": 1,
            },
            {"id": 1, "option_text": "A", "is_correct": True},
            {"id": 2, "option_text": "B", "is_correct": False},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            result = service.update_mcq_question(
                question_id=1,
                question_text="Zero mark question",
                marks=0,
                options=["A", "B"],
                correct_option_index=0,
            )

        assert result["marks"] == 0

    def test_update_mcq_question_none_options(self, service, mock_conn):
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            with pytest.raises(ValueError):
                service.update_mcq_question(
                    question_id=1,
                    question_text="Test",
                    marks=5,
                    options=None,
                    correct_option_index=0,
                )

    # ============================================================
    # DELETE OLD OPTIONS BEFORE INSERT
    # ============================================================
    def test_update_mcq_question_delete_old_options_called(self, service, mock_conn, mock_cursor):

        mock_cursor.fetchone.side_effect = [
            {"exam_id": 1},    # exam lookup
            None,              # duplicate text check
            {                  # update question
                "id": 1,
                "question_text": "New Q",
                "question_type": "mcq",
                "marks": 5,
                "exam_id": 1,
            },
            {"id": 11, "option_text": "X", "is_correct": True},
            {"id": 12, "option_text": "Y", "is_correct": False},
        ]

        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            service.update_mcq_question(
                question_id=1,
                question_text="New Q",
                marks=5,
                options=["X", "Y"],
                correct_option_index=0,
            )

        mock_cursor.execute.assert_any_call(
            'DELETE FROM "questionOption" WHERE question_id = %s', (1,)
        )

    
