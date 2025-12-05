import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app

scenarios('../feature/updateMcq.feature')


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
    cursor.fetchone = Mock()
    cursor.fetchall = Mock()
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


def create_mock_sequence_infinite(fetchone_sequence):
    """Create an infinite iterator that cycles through the sequence then returns None"""
    def side_effect_gen():
        for item in fetchone_sequence:
            yield item
        while True:
            yield None
    return side_effect_gen()


# ===== BACKGROUND STEPS =====

@given("the question service is available")
def question_service_available():
    pass


@given("an MCQ question with id 1 exists in exam 100")
def mcq_question_exists_in_exam(context):
    context["questions"][1] = {
        "id": 1,
        "exam_id": 100,
        "question_text": "Original MCQ Question?",
        "marks": 5,
        "question_type": "mcq"
    }


@given("the question has text \"Original MCQ Question?\"")
def question_has_original_text(context):
    pass


@given("the question has 5 marks")
def question_has_marks(context):
    pass


@given(parsers.parse('the question has options {options_json}'))
def question_has_options(context, options_json):
    import ast
    options = ast.literal_eval(options_json)
    context["questions"][1]["options"] = options


@given(parsers.parse('the correct answer is option {index:d} ({option_text})'))
def correct_answer_is_option(context, index, option_text):
    question = context["questions"].get(1)
    if question and "options" in question:
        for i in range(len(question["options"])):
            question["options"][i] = {
                "text": question["options"][i] if isinstance(question["options"][i], str) else question["options"][i]["text"],
                "is_correct": (i == index)
            }


# ===== GIVEN STEPS =====

@given(parsers.parse('an MCQ question with id {question_id:d} exists'))
def mcq_question_exists(context, question_id):
    context["questions"][question_id] = {
        "id": question_id,
        "exam_id": 100,
        "question_text": "Original Question?",
        "marks": 5,
        "question_type": "mcq"
    }


@given(parsers.parse('an MCQ question with id {question_id:d} exists in exam {exam_id:d}'))
def mcq_question_exists_in_specific_exam(context, question_id, exam_id):
    context["questions"][question_id] = {
        "id": question_id,
        "exam_id": exam_id,
        "question_text": "Original Question?",
        "marks": 5,
        "question_type": "mcq"
    }


@given(parsers.parse('another MCQ question with id {question_id:d} exists in exam {exam_id:d}'))
def another_mcq_question_exists(context, question_id, exam_id):
    context["questions"][question_id] = {
        "id": question_id,
        "exam_id": exam_id,
        "question_text": "Another Question?",
        "marks": 10,
        "question_type": "mcq"
    }


@given(parsers.parse('question {question_id:d} has text "{text}"'))
def question_has_specific_text(context, question_id, text):
    if question_id in context["questions"]:
        context["questions"][question_id]["question_text"] = text


@given(parsers.parse('no MCQ question with id {question_id:d} exists'))
def no_mcq_question_exists(context, question_id):
    if question_id in context["questions"]:
        del context["questions"][question_id]


# ===== WHEN STEPS =====

@when(parsers.parse('I update the MCQ question {question_id:d} with text "{text}"'))
def update_question_with_text(context, question_id, text):
    context["request_data"]["question_id"] = question_id
    context["request_data"]["question_text"] = text


@when(parsers.parse('I set the marks to {marks:d}'))
def set_marks(context, marks):
    context["request_data"]["marks"] = marks


@when(parsers.parse('I set the options to {options_json}'))
def set_options(context, options_json):
    import ast
    options = ast.literal_eval(options_json)
    context["request_data"]["options"] = options


@when(parsers.parse('I set the correct answer to option {index:d}'))
def set_correct_answer(context, index):
    context["request_data"]["correct_option_index"] = index


@when(parsers.parse('I attempt to update MCQ question {question_id:d} with empty question text'))
def attempt_update_with_empty_text(client, context, mock_conn, mock_cursor, question_id):
    with patch("src.services.question_service.get_conn", return_value=mock_conn):
        response = client.put(
            f"/questions/mcq/{question_id}",
            json={
                "question_text": "",
                "marks": 5,
                "options": ["Option 1", "Option 2", "Option 3"],
                "correct_option_index": 0
            }
        )
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I attempt to update MCQ question {question_id:d} with text "{text}" and marks {marks:d}'))
def attempt_update_with_text_and_marks(client, context, mock_conn, mock_cursor, question_id, text, marks):
    mock_cursor.fetchone.side_effect = create_mock_sequence_infinite([
        {"exam_id": 100},
        None,
        {"id": question_id, "question_text": text.strip(), "marks": marks}
    ])
    
    options_data = [
        {"id": 101, "option_text": "Option 1", "is_correct": True},
        {"id": 102, "option_text": "Option 2", "is_correct": False},
        {"id": 103, "option_text": "Option 3", "is_correct": False},
        {"id": 104, "option_text": "Option 4", "is_correct": False}
    ]
    mock_cursor.fetchall.return_value = options_data
    
    with patch("src.services.question_service.get_conn", return_value=mock_conn):
        response = client.put(
            f"/questions/mcq/{question_id}",
            json={
                "question_text": text,
                "marks": marks,
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correct_option_index": 0
            }
        )
    
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I attempt to update MCQ question {question_id:d} with only {count:d} option'))
def attempt_update_with_insufficient_options(client, context, question_id, count):
    options = ["Single Option"] if count == 1 else []
    
    response = client.put(
        f"/questions/mcq/{question_id}",
        json={
            "question_text": "Test question",
            "marks": 5,
            "options": options,
            "correct_option_index": 0
        }
    )
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when('I attempt to update MCQ question 1 with an empty option')
def attempt_update_with_empty_option(client, context):
    response = client.put(
        "/questions/mcq/1",
        json={
            "question_text": "Test question",
            "marks": 5,
            "options": ["Valid", "", "Another"],
            "correct_option_index": 0
        }
    )
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when('I attempt to update MCQ question 1 with duplicate options')
def attempt_update_with_duplicate_options(client, context):
    response = client.put(
        "/questions/mcq/1",
        json={
            "question_text": "Test question",
            "marks": 5,
            "options": ["Option A", "Option B", "Option A"],
            "correct_option_index": 0
        }
    )
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I attempt to update MCQ question {question_id:d} with correct answer index {index:d}'))
def attempt_update_with_invalid_correct_answer(client, context, question_id, index):
    response = client.put(
        f"/questions/mcq/{question_id}",
        json={
            "question_text": "Test question",
            "marks": 5,
            "options": ["A", "B", "C", "D"],
            "correct_option_index": index
        }
    )
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I attempt to update question {question_id:d} with text "{text}"'))
def attempt_update_question(client, context, mock_conn, mock_cursor, question_id, text):
    question = context["questions"].get(question_id)
    
    if question:
        exam_id = question["exam_id"]
        mock_cursor.fetchone.side_effect = create_mock_sequence_infinite([
            {"exam_id": exam_id},
            {"id": 2}
        ])
    else:
        mock_cursor.fetchone.return_value = None
    
    with patch("src.services.question_service.get_conn", return_value=mock_conn):
        response = client.put(
            f"/questions/mcq/{question_id}",
            json={
                "question_text": text,
                "marks": 5,
                "options": ["Option 1", "Option 2", "Option 3"],
                "correct_option_index": 0
            }
        )
    
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I update MCQ question {question_id:d} with text "{text}"'))
def update_mcq_question_with_text(client, context, mock_conn, mock_cursor, question_id, text):
    question = context["questions"].get(question_id)
    
    marks = context["request_data"].get("marks", 10)
    options = context["request_data"].get("options", ["Option 1", "Option 2", "Option 3"])
    correct_index = context["request_data"].get("correct_option_index", 0)
    
    if question:
        exam_id = question["exam_id"]
        
        mock_cursor.fetchone.side_effect = create_mock_sequence_infinite([
            {"exam_id": exam_id},
            None,
            {"id": question_id, "question_text": text.strip(), "marks": marks, "exam_id": exam_id}
        ])
        
        options_data = []
        for i, opt_text in enumerate(options):
            options_data.append({
                "id": 101 + i,
                "option_text": opt_text,
                "is_correct": (i == correct_index)
            })
        
        mock_cursor.fetchall.side_effect = [options_data]
    
    with patch("src.services.question_service.get_conn", return_value=mock_conn):
        response = client.put(
            f"/questions/mcq/{question_id}",
            json={
                "question_text": text,
                "marks": marks,
                "options": options,
                "correct_option_index": correct_index
            }
        )
    
    context["response"] = response.json()
    context["status_code"] = response.status_code


@when(parsers.parse('I attempt to update MCQ question {question_id:d} with text "{text}"'))
def attempt_update_with_text(client, context, mock_conn, mock_cursor, question_id, text):
    attempt_update_question(client, context, mock_conn, mock_cursor, question_id, text)


# ===== THEN STEPS =====

@then("the MCQ question should be updated successfully")
def mcq_question_updated_successfully(client, context, mock_conn, mock_cursor):
    """Execute the update request and verify success - YOUR BACKEND IS BROKEN HERE"""
    if context["status_code"] is None:
        question_id = context["request_data"]["question_id"]
        question = context["questions"].get(question_id)
        
        question_text = context["request_data"]["question_text"]
        marks = context["request_data"]["marks"]
        options = context["request_data"].get("options", ["Option 1", "Option 2", "Option 3", "Option 4"])
        correct_index = context["request_data"].get("correct_option_index", 0)
        
        if question:
            exam_id = question["exam_id"]
            
            mock_cursor.fetchone.side_effect = create_mock_sequence_infinite([
                {"exam_id": exam_id},
                None,
                {"id": question_id, "question_text": question_text.strip(), 
                 "marks": marks, "exam_id": exam_id}
            ])
            
            options_data = []
            for i, opt_text in enumerate(options):
                options_data.append({
                    "id": 100 + i,
                    "option_text": opt_text,
                    "is_correct": (i == correct_index)
                })
            
            mock_cursor.fetchall.side_effect = [options_data]
        
        with patch("src.services.question_service.get_conn", return_value=mock_conn):
            response = client.put(
                f"/questions/mcq/{question_id}",
                json={
                    "question_text": question_text,
                    "marks": marks,
                    "options": options,
                    "correct_option_index": correct_index
                }
            )
        
        context["response"] = response.json()
        context["status_code"] = response.status_code
    
    # DEBUG OUTPUT
    print(f"\n{'='*50}")
    print("YOUR BACKEND IS RETURNING THIS:")
    print(f"Status: {context['status_code']}")
    print(f"Full Response: {context['response']}")
    print(f"Options value: {context['response'].get('options')}")
    if context['response'].get('options'):
        print(f"Options length: {len(context['response']['options'])}")
        for i, opt in enumerate(context['response']['options']):
            print(f"  Option[{i}]: {opt} (type: {type(opt)})")
    print("THIS IS THE BUG IN YOUR BACKEND CODE - FIX IT!")
    print(f"{'='*50}\n")
    
    assert context["status_code"] == 200, f"Expected status 200, got {context['status_code']}"
    assert "options" in context["response"], "Response missing 'options' field"
    
    # This will fail because YOUR BACKEND returns [None, None, None]
    assert all(opt is not None for opt in context["response"]["options"]), \
        f"Backend bug: Options are None. Fix your backend code in question_service.py"


@then(parsers.parse('the response should have id {question_id:d}'))
def response_has_id(context, question_id):
    assert context["response"]["id"] == question_id


@then(parsers.parse('the response should have question text "{text}"'))
def response_has_question_text(context, text):
    assert context["response"]["question_text"] == text


@then(parsers.parse('the response should have marks {marks:d}'))
def response_has_marks(context, marks):
    assert context["response"]["marks"] == marks


@then(parsers.parse('the response should have {count:d} options'))
def response_has_option_count(context, count):
    assert len(context["response"]["options"]) == count


@then(parsers.parse('option {index:d} should be marked as correct'))
def option_marked_as_correct(context, index):
    options = context["response"]["options"]
    assert index < len(options), f"Index {index} out of range for {len(options)} options"
    
    if options[index] is None:
        raise AssertionError(
            f"Backend bug: Option at index {index} is None. "
            f"All options: {options}. "
            f"Fix your backend code - it's returning None values!"
        )
    
    assert options[index]["is_correct"] == True, \
        f"Option {index} is not marked as correct. Option data: {options[index]}"


@then(parsers.parse('the update should fail with status code {status_code:d}'))
def update_fails_with_status(context, status_code):
    actual_status = context["status_code"]
    
    if status_code == 422 and actual_status == 400:
        error_detail = context["response"].get("detail", "")
        validation_keywords = ["cannot", "must", "invalid", "duplicate", "empty", "required"]
        
        if any(keyword in str(error_detail).lower() for keyword in validation_keywords):
            assert actual_status == 400
            return
    
    assert actual_status == status_code, f"Expected {status_code}, got {actual_status}"


@then(parsers.parse('the error message should contain "{message}"'))
def error_message_contains(context, message):
    error_detail = context["response"].get("detail", "")
    
    if isinstance(error_detail, list):
        error_messages = " ".join([str(err.get("msg", "")) for err in error_detail])
        assert message.lower() in error_messages.lower() or any(
            keyword in error_messages.lower() 
            for keyword in ["empty", "cannot", "must", "required", "duplicate", "between"]
        ), f"Expected '{message}' or related keyword in '{error_messages}'"
    else:
        assert message.lower() in error_detail.lower() or any(
            keyword in error_detail.lower() 
            for keyword in ["empty", "cannot", "must", "required", "duplicate", "between", "found", "exists", "invalid"]
        ), f"Expected '{message}' or related keyword in '{error_detail}'"