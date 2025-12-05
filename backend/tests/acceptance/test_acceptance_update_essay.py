import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app  # Adjust import based on your main app location

# Load all scenarios from the feature file
scenarios('../feature/update_essay.feature')


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_cursor():
    """Create a mock cursor"""
    cursor = MagicMock()
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    """Create a mock connection"""
    conn = MagicMock()
    conn.__enter__ = Mock(return_value=conn)
    conn.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = mock_cursor
    return conn


@pytest.fixture
def context():
    """Shared context for BDD scenarios"""
    return {
        "questions": {},
        "request_data": {},
        "response": None,
        "status_code": None
    }


# ===== BACKGROUND STEPS =====

@given("the question service is available")
def question_service_available():
    """Question service is available"""
    pass


@given("an essay question with id 1 exists in exam 100")
def essay_question_exists_in_exam(context):
    """Store initial question data"""
    context["questions"][1] = {
        "id": 1,
        "exam_id": 100,
        "question_text": "Original Question?",
        "marks": 10,
        "rubric": "Original rubric",
        "question_type": "essay"
    }


@given("the question has text \"Original Question?\"")
def question_has_original_text(context):
    """Verify question text"""
    pass


@given("the question has 10 marks")
def question_has_marks(context):
    """Verify question marks"""
    pass


@given("the question has rubric \"Original rubric\"")
def question_has_rubric(context):
    """Verify question rubric"""
    pass


# ===== GIVEN STEPS =====

@given(parsers.parse('an essay question with id {question_id:d} exists'))
def essay_question_exists(context, question_id):
    """Mock an existing essay question"""
    context["questions"][question_id] = {
        "id": question_id,
        "exam_id": 100,
        "question_text": "Original Question?",
        "marks": 10,
        "rubric": "Original rubric",
        "question_type": "essay"
    }


@given(parsers.parse('an essay question with id {question_id:d} exists in exam {exam_id:d}'))
def essay_question_exists_in_specific_exam(context, question_id, exam_id):
    """Mock an existing essay question in a specific exam"""
    context["questions"][question_id] = {
        "id": question_id,
        "exam_id": exam_id,
        "question_text": "Original Question?",
        "marks": 10,
        "rubric": "Original rubric",
        "question_type": "essay"
    }


@given(parsers.parse('another essay question with id {question_id:d} exists in exam {exam_id:d}'))
def another_essay_question_exists(context, question_id, exam_id):
    """Mock another existing essay question"""
    context["questions"][question_id] = {
        "id": question_id,
        "exam_id": exam_id,
        "question_text": "Another Question?",
        "marks": 10,
        "rubric": None,
        "question_type": "essay"
    }


@given(parsers.parse('question {question_id:d} has text "{text}"'))
def question_has_specific_text(context, question_id, text):
    """Set specific text for a question"""
    if question_id in context["questions"]:
        context["questions"][question_id]["question_text"] = text


@given(parsers.parse('no essay question with id {question_id:d} exists'))
def no_essay_question_exists(context, question_id):
    """Ensure question doesn't exist"""
    if question_id in context["questions"]:
        del context["questions"][question_id]


# ===== WHEN STEPS =====

@when(parsers.parse('I update the essay question {question_id:d} with text "{text}"'))
def update_question_with_text(context, question_id, text):
    """Update question with new text"""
    context["request_data"]["question_id"] = question_id
    context["request_data"]["question_text"] = text


@when(parsers.parse('I set the marks to {marks:d}'))
def set_marks(context, marks):
    """Set marks for the question"""
    context["request_data"]["marks"] = marks


@when(parsers.parse('I set the rubric to "{rubric}"'))
def set_rubric(context, rubric):
    """Set rubric for the question"""
    context["request_data"]["rubric"] = rubric


@when(parsers.parse('I set the reference answer to "{answer}"'))
def set_reference_answer(context, answer):
    """Set reference answer for the question"""
    context["request_data"]["reference_answer"] = answer


@when(parsers.parse('I attempt to update the essay question {question_id:d} with empty question text'))
def attempt_update_with_empty_text(client, context, mock_conn, mock_cursor, question_id):
    """Attempt to update with empty text"""
    with patch("src.services.question_service.get_conn", return_value=mock_conn):
        response = client.put(
            f"/questions/essay/{question_id}",
            json={
                "question_text": "",
                "marks": 10
            }
        )
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I attempt to update the essay question {question_id:d} with text "{text}"'))
def attempt_update_with_text(client, context, mock_conn, mock_cursor, question_id, text):
    """Attempt to update with specific text"""
    question = context["questions"].get(question_id)
    
    if question:
        exam_id = question["exam_id"]
        
        # Check for duplicate
        duplicate_found = False
        for qid, q in context["questions"].items():
            if (qid != question_id and 
                q["exam_id"] == exam_id and 
                q["question_text"].lower().strip() == text.lower().strip()):
                duplicate_found = True
                break
        
        if duplicate_found:
            mock_cursor.fetchone.side_effect = [
                {"exam_id": exam_id},
                {"id": 2}  # Duplicate found
            ]
        else:
            mock_cursor.fetchone.side_effect = [
                {"exam_id": exam_id},
                None,
                {
                    "id": question_id,
                    "question_text": text.strip(),
                    "question_type": "essay",
                    "marks": context["request_data"].get("marks", 10),
                    "rubric": context["request_data"].get("rubric"),
                    "exam_id": exam_id
                }
            ]
    else:
        mock_cursor.fetchone.return_value = None
    
    with patch("src.services.question_service.get_conn", return_value=mock_conn):
        response = client.put(
            f"/questions/essay/{question_id}",
            json={
                "question_text": text,
                "marks": context["request_data"].get("marks", 10),
                "rubric": context["request_data"].get("rubric")
            }
        )
    
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I attempt to update essay question {question_id:d} with text "{text}"'))
def attempt_update_essay_question(client, context, mock_conn, mock_cursor, question_id, text):
    """Attempt to update essay question (same as above)"""
    attempt_update_with_text(client, context, mock_conn, mock_cursor, question_id, text)


@when(parsers.parse('I attempt to update question {question_id:d} with text "{text}"'))
def attempt_update_question(client, context, mock_conn, mock_cursor, question_id, text):
    """Attempt to update question"""
    context["request_data"]["marks"] = context["request_data"].get("marks", 10)
    attempt_update_with_text(client, context, mock_conn, mock_cursor, question_id, text)


# ===== THEN STEPS =====

@then("the essay question should be updated successfully")
def question_updated_successfully(client, context, mock_conn, mock_cursor):
    """Execute the update request and verify success"""
    if context["status_code"] is None:
        question_id = context["request_data"]["question_id"]
        question = context["questions"].get(question_id)
        
        if question:
            exam_id = question["exam_id"]
            question_text = context["request_data"]["question_text"]
            
            # Check for duplicate
            duplicate_found = False
            for qid, q in context["questions"].items():
                if (qid != question_id and 
                    q["exam_id"] == exam_id and 
                    q["question_text"].lower().strip() == question_text.lower().strip()):
                    duplicate_found = True
                    break
            
            if not duplicate_found:
                mock_cursor.fetchone.side_effect = [
                    {"exam_id": exam_id},
                    None,
                    {
                        "id": question_id,
                        "question_text": question_text.strip(),
                        "question_type": "essay",
                        "marks": context["request_data"]["marks"],
                        "rubric": context["request_data"].get("rubric"),
                        "exam_id": exam_id
                    }
                ]
        
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            response = client.put(
                f"/questions/essay/{question_id}",
                json=context["request_data"]
            )
        
        context["response"] = response.json()
        context["status_code"] = response.status_code
    
    assert context["status_code"] == 200


@then(parsers.parse('the response should have id {question_id:d}'))
def response_has_id(context, question_id):
    """Verify response has correct id"""
    assert context["response"]["id"] == question_id


@then(parsers.parse('the response should have question text "{text}"'))
def response_has_question_text(context, text):
    """Verify response has correct question text"""
    assert context["response"]["question_text"] == text


@then(parsers.parse('the response should have marks {marks:d}'))
def response_has_marks(context, marks):
    """Verify response has correct marks"""
    assert context["response"]["marks"] == marks


@then(parsers.parse('the response should have rubric "{rubric}"'))
def response_has_rubric(context, rubric):
    """Verify response has correct rubric"""
    assert context["response"]["rubric"] == rubric


@then(parsers.parse('the question should have marks {marks:d}'))
def question_has_specific_marks(context, marks):
    """Verify question has specific marks"""
    assert context["response"]["marks"] == marks


@then(parsers.parse('the update should fail with status code {status_code:d}'))
def update_fails_with_status(context, status_code):
    """Verify update fails with specific status code"""
    assert context["status_code"] == status_code


@then(parsers.parse('the error message should contain "{message}"'))
def error_message_contains(context, message):
    """Verify error message contains specific text"""
    error_detail = context["response"].get("detail", "")
    
    # Handle both string detail and list of validation errors
    if isinstance(error_detail, list):
        # Pydantic validation errors return a list
        error_messages = " ".join([str(err.get("msg", "")) for err in error_detail])
        assert message.lower() in error_messages.lower()
    else:
        # Service layer errors return a string
        assert message.lower() in error_detail.lower()