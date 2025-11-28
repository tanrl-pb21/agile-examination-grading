from src.db import get_conn
from psycopg.rows import dict_row


class QuestionService:

    def add_mcq_question(
        self,
        exam_id: int,
        question_text: str,
        marks: int,
        options: list,
        correct_option_index: int,
    ):
        """Add an MCQ question with options"""
        if not question_text:
            raise ValueError("Question text is required")
        if not options or len(options) < 2:
            raise ValueError("At least 2 options are required")
        if correct_option_index < 0 or correct_option_index >= len(options):
            raise ValueError("Invalid correct option index")

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT id FROM exams WHERE id = %s", (exam_id,))
                if not cur.fetchone():
                    raise ValueError(f"Exam with id {exam_id} not found")

                cur.execute(
                    """
                    INSERT INTO question (question_text, question_type, marks, exam_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, question_text, question_type, marks, exam_id;
                """,
                    (question_text, "mcq", marks, exam_id),
                )

                question = cur.fetchone()
                question_id = question["id"]

                options_data = []
                for i, option_text in enumerate(options):
                    is_correct = i == correct_option_index
                    cur.execute(
                        """
                        INSERT INTO "questionOption" (option_text, question_id, is_correct)
                        VALUES (%s, %s, %s)
                        RETURNING id, option_text, is_correct;
                    """,
                        (option_text, question_id, is_correct),
                    )

                    option = cur.fetchone()
                    options_data.append(option)

                conn.commit()

                return {**question, "options": options_data}

    def update_mcq_question(
        self,
        question_id: int,
        question_text: str,
        marks: int,
        options: list,
        correct_option_index: int,
    ):
        """Update an MCQ question"""
        if not question_text:
            raise ValueError("Question text is required")
        if not options or len(options) < 2:
            raise ValueError("At least 2 options are required")
        if correct_option_index < 0 or correct_option_index >= len(options):
            raise ValueError("Invalid correct option index")

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    UPDATE question
                    SET question_text = %s, marks = %s
                    WHERE id = %s AND question_type = 'mcq'
                    RETURNING id, question_text, question_type, marks, exam_id;
                """,
                    (question_text, marks, question_id),
                )

                question = cur.fetchone()
                if not question:
                    raise ValueError(f"MCQ Question with id {question_id} not found")

                cur.execute(
                    """
                    DELETE FROM "questionOption"
                    WHERE question_id = %s;
                """,
                    (question_id,),
                )

                options_data = []
                for i, option_text in enumerate(options):
                    is_correct = i == correct_option_index
                    cur.execute(
                        """
                        INSERT INTO "questionOption" (option_text, question_id, is_correct)
                        VALUES (%s, %s, %s)
                        RETURNING id, option_text, is_correct;
                    """,
                        (option_text, question_id, is_correct),
                    )

                    option = cur.fetchone()
                    options_data.append(option)

                conn.commit()

                return {**question, "options": options_data}

    def add_essay_question(
        self,
        exam_id: int,
        question_text: str,
        marks: int,
        rubric: str = None,
        word_limit: int = None,
        reference_answer: str = None,
    ):
        """Add an essay question"""
        if not question_text:
            raise ValueError("Question text is required")

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT id FROM exams WHERE id = %s", (exam_id,))
                if not cur.fetchone():
                    raise ValueError(f"Exam with id {exam_id} not found")

                cur.execute(
                    """
                    INSERT INTO question (question_text, question_type, marks, rubric, exam_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, question_text, question_type, marks, rubric, exam_id;
                """,
                    (question_text, "essay", marks, rubric, exam_id),
                )

                question = cur.fetchone()
                conn.commit()

                question["word_limit"] = word_limit
                question["reference_answer"] = reference_answer

                return question

    def update_essay_question(
        self,
        question_id: int,
        question_text: str,
        marks: int,
        rubric: str = None,
        word_limit: int = None,
        reference_answer: str = None,
    ):
        """Update an essay question"""
        if not question_text:
            raise ValueError("Question text is required")

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    UPDATE question
                    SET question_text = %s, marks = %s, rubric = %s
                    WHERE id = %s AND question_type = 'essay'
                    RETURNING id, question_text, question_type, marks, rubric, exam_id;
                """,
                    (question_text, marks, rubric, question_id),
                )

                question = cur.fetchone()
                if not question:
                    raise ValueError(f"Essay Question with id {question_id} not found")

                conn.commit()

                question["word_limit"] = word_limit
                question["reference_answer"] = reference_answer

                return question

    def get_exam_questions(self, exam_id: int):
        """Get all questions for an exam"""
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT id FROM exams WHERE id = %s", (exam_id,))
                if not cur.fetchone():
                    raise ValueError(f"Exam with id {exam_id} not found")

                cur.execute(
                    """
                    SELECT id, question_text, question_type, marks, rubric, exam_id
                    FROM question
                    WHERE exam_id = %s
                    ORDER BY id;
                """,
                    (exam_id,),
                )

                questions = cur.fetchall()

                for question in questions:
                    if question["question_type"] == "mcq":
                        cur.execute(
                            """
                            SELECT id, option_text, is_correct
                            FROM "questionOption"
                            WHERE question_id = %s
                            ORDER BY id;
                        """,
                            (question["id"],),
                        )

                        question["options"] = cur.fetchall()

                return questions

    def get_question(self, question_id: int):
        """Get a single question by ID"""
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, question_text, question_type, marks, rubric, exam_id
                    FROM question
                    WHERE id = %s;
                """,
                    (question_id,),
                )

                question = cur.fetchone()

                if not question:
                    return None

                if question["question_type"] == "mcq":
                    cur.execute(
                        """
                        SELECT id, option_text, is_correct
                        FROM "questionOption"
                        WHERE question_id = %s
                        ORDER BY id;
                    """,
                        (question_id,),
                    )

                    question["options"] = cur.fetchall()

                return question

    def delete_question(self, question_id: int):
        """Delete a question and its associated data"""
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    DELETE FROM "questionOption"
                    WHERE question_id = %s;
                """,
                    (question_id,),
                )

                cur.execute(
                    """
                    DELETE FROM question
                    WHERE id = %s
                    RETURNING id;
                """,
                    (question_id,),
                )

                row = cur.fetchone()
                conn.commit()

        if not row:
            raise ValueError(f"Question with id {question_id} not found")

        return row
