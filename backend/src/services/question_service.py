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
        """Add an MCQ question with duplicate question + duplicate option prevention"""

        # --- Validate question text ---
        if not question_text or not question_text.strip():
            raise ValueError("Question text is required")
        question_text_clean = question_text.strip()

        # --- Validate options count ---
        if not options or len(options) < 2:
            raise ValueError("At least 2 options are required")

        # --- Validate unique options (trim + case-insensitive) ---
        normalized_opts = [opt.strip().lower() for opt in options]
        if len(normalized_opts) != len(set(normalized_opts)):
            raise ValueError("MCQ options cannot contain duplicate values")

        # --- Validate index ---
        if correct_option_index < 0 or correct_option_index >= len(options):
            raise ValueError("Invalid correct option index")

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:

                # Check exam exists
                cur.execute("SELECT id FROM exams WHERE id = %s", (exam_id,))
                if not cur.fetchone():
                    raise ValueError(f"Exam with id {exam_id} not found")

                # Duplicate question text
                cur.execute(
                    """
                    SELECT id FROM question
                    WHERE exam_id = %s
                    AND LOWER(TRIM(question_text)) = LOWER(TRIM(%s))
                    """,
                    (exam_id, question_text_clean),
                )
                if cur.fetchone():
                    raise ValueError(
                        f"A question with the same text already exists in exam {exam_id}."
                    )

                # Insert MCQ
                cur.execute(
                    """
                    INSERT INTO question (question_text, question_type, marks, exam_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, question_text, question_type, marks, exam_id;
                    """,
                    (question_text_clean, "mcq", marks, exam_id),
                )

                question = cur.fetchone()
                question_id = question["id"]

                # Insert options
                options_data = []
                for i, option_text in enumerate(options):
                    is_correct = i == correct_option_index
                    cur.execute(
                        """
                        INSERT INTO "questionOption" (option_text, question_id, is_correct)
                        VALUES (%s, %s, %s)
                        RETURNING id, option_text, is_correct;
                        """,
                        (option_text.strip(), question_id, is_correct),
                    )
                    options_data.append(cur.fetchone())

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
        """Update an MCQ with duplicate question + duplicate option prevention"""

        # --- Validate question text ---
        if not question_text or not question_text.strip():
            raise ValueError("Question text is required")
        question_text_clean = question_text.strip()

        # --- Validate options count ---
        if not options or len(options) < 2:
            raise ValueError("At least 2 options are required")

        # --- Validate unique options ---
        normalized_opts = [opt.strip().lower() for opt in options]
        if len(normalized_opts) != len(set(normalized_opts)):
            raise ValueError("MCQ options cannot contain duplicate values")

        # --- Validate index ---
        if correct_option_index < 0 or correct_option_index >= len(options):
            raise ValueError("Invalid correct option index")

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:

                # Read exam ID
                cur.execute(
                    "SELECT exam_id FROM question WHERE id = %s AND question_type = 'mcq'",
                    (question_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"MCQ Question with id {question_id} not found")

                exam_id = row["exam_id"]

                # Duplicate question text (exclude itself)
                cur.execute(
                    """
                    SELECT id FROM question
                    WHERE exam_id = %s
                    AND LOWER(TRIM(question_text)) = LOWER(TRIM(%s))
                    AND id <> %s
                    """,
                    (exam_id, question_text_clean, question_id),
                )
                if cur.fetchone():
                    raise ValueError(
                        f"A question with the same text already exists in exam {exam_id}."
                    )

                # Update question
                cur.execute(
                    """
                    UPDATE question
                    SET question_text = %s, marks = %s
                    WHERE id = %s AND question_type = 'mcq'
                    RETURNING id, question_text, question_type, marks, exam_id;
                    """,
                    (question_text_clean, marks, question_id),
                )

                question = cur.fetchone()

                # Remove old options
                cur.execute(
                    'DELETE FROM "questionOption" WHERE question_id = %s',
                    (question_id,),
                )

                # Insert new options
                options_data = []
                for i, option_text in enumerate(options):
                    is_correct = i == correct_option_index
                    cur.execute(
                        """
                        INSERT INTO "questionOption" (option_text, question_id, is_correct)
                        VALUES (%s, %s, %s)
                        RETURNING id, option_text, is_correct;
                        """,
                        (option_text.strip(), question_id, is_correct),
                    )
                    options_data.append(cur.fetchone())

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
        """Add an essay question with duplicate prevention"""

        if not question_text or not question_text.strip():
            raise ValueError("Question text is required")
        question_text_clean = question_text.strip()

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:

                # Check exam exists
                cur.execute("SELECT id FROM exams WHERE id = %s", (exam_id,))
                if not cur.fetchone():
                    raise ValueError(f"Exam with id {exam_id} not found")

                # Duplicate check
                cur.execute(
                    """
                    SELECT id FROM question
                    WHERE exam_id = %s
                    AND LOWER(TRIM(question_text)) = LOWER(TRIM(%s))
                    """,
                    (exam_id, question_text_clean),
                )
                if cur.fetchone():
                    raise ValueError(
                        f"A question with the same text already exists in exam {exam_id}."
                    )

                # Insert essay question
                cur.execute(
                    """
                    INSERT INTO question (question_text, question_type, marks, rubric, exam_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, question_text, question_type, marks, rubric, exam_id;
                    """,
                    (question_text_clean, "essay", marks, rubric, exam_id),
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
        """Update an essay question with duplicate prevention"""

        if not question_text or not question_text.strip():
            raise ValueError("Question text is required")

        question_text_clean = question_text.strip()

        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:

                # Get exam_id
                cur.execute(
                    "SELECT exam_id FROM question WHERE id = %s AND question_type = 'essay'",
                    (question_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Essay Question with id {question_id} not found")

                exam_id = row["exam_id"]

                # Duplicate check (exclude itself)
                cur.execute(
                    """
                    SELECT id FROM question
                    WHERE exam_id = %s
                    AND LOWER(TRIM(question_text)) = LOWER(TRIM(%s))
                    AND id <> %s
                    """,
                    (exam_id, question_text_clean, question_id),
                )
                if cur.fetchone():
                    raise ValueError(
                        f"A question with the same text already exists in exam {exam_id}."
                    )

                # Update
                cur.execute(
                    """
                    UPDATE question
                    SET question_text = %s, marks = %s, rubric = %s
                    WHERE id = %s AND question_type = 'essay'
                    RETURNING id, question_text, question_type, marks, rubric, exam_id;
                    """,
                    (question_text_clean, marks, rubric, question_id),
                )

                question = cur.fetchone()
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
