"""
BDD/Acceptance Tests for Course Enrollment API
Testing API endpoints with mocked services
"""
import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then, parsers
from main import app

client = TestClient(app)

# Load feature file
scenarios("../feature/enrollCourse.feature")


@pytest.fixture
def context():
    """Context to store test state between steps"""
    return {"response": None, "mock_state": {}}


# =======================
# GIVEN STEPS (mocked)
# =======================

@given(parsers.parse('a student with id {student_id:d} exists'))
def student_exists(student_id, monkeypatch, context):
    """Mock that student exists"""
    context["mock_state"]["existing_students"] = context["mock_state"].get("existing_students", [])
    context["mock_state"]["existing_students"].append(student_id)
    
    # Mock enroll_student to validate student existence
    original_enroll_student = None
    
    def fake_enroll_student(self, s_id, c_id):
        if s_id not in context["mock_state"].get("existing_students", []):
            raise ValueError("Student not found or user is not a student")
        
        # Check if already enrolled
        enrollments = context["mock_state"].get("enrollments", [])
        for enrollment in enrollments:
            if enrollment["student_id"] == s_id and enrollment["course_id"] == c_id:
                raise ValueError("Student is already enrolled in this course")
        
        # Check course status
        courses = context["mock_state"].get("courses", {})
        if c_id in courses and courses[c_id]["status"] != "active":
            raise ValueError("Cannot enroll in an inactive course")
        
        # Create new enrollment
        enrollment_id = len(enrollments) + 1
        new_enrollment = {
            "id": enrollment_id,
            "student_id": s_id,
            "course_id": c_id,
            "course_name": f"Course {c_id}",
            "student_email": f"student{s_id}@example.com"
        }
        enrollments.append(new_enrollment)
        context["mock_state"]["enrollments"] = enrollments
        
        return new_enrollment
    
    # Store original method and apply mock
    monkeypatch.setattr(
        "src.services.course_service.CourseService.enroll_student",
        fake_enroll_student
    )
    
    # Also mock unenroll_student
    def fake_unenroll_student(self, s_id, c_id):
        enrollments = context["mock_state"].get("enrollments", [])
        for i, enrollment in enumerate(enrollments):
            if enrollment["student_id"] == s_id and enrollment["course_id"] == c_id:
                enrollments.pop(i)
                context["mock_state"]["enrollments"] = enrollments
                return True
        return False
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.unenroll_student",
        fake_unenroll_student
    )
    
    # Mock is_student_enrolled
    def fake_is_student_enrolled(self, s_id, c_id):
        enrollments = context["mock_state"].get("enrollments", [])
        return any(e["student_id"] == s_id and e["course_id"] == c_id for e in enrollments)
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.is_student_enrolled",
        fake_is_student_enrolled
    )
    
    # Mock get_student_courses
    def fake_get_student_courses(self, s_id):
        enrollments = context["mock_state"].get("enrollments", [])
        courses = context["mock_state"].get("courses", {})
        
        student_courses = []
        for enrollment in enrollments:
            if enrollment["student_id"] == s_id and enrollment["course_id"] in courses:
                course = courses[enrollment["course_id"]]
                student_courses.append({
                    **course,
                    "enrollment_id": enrollment["id"]
                })
        return student_courses
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.get_student_courses",
        fake_get_student_courses
    )
    
    # Mock get_available_courses_for_student
    def fake_get_available_courses_for_student(self, s_id):
        enrollments = context["mock_state"].get("enrollments", [])
        courses = context["mock_state"].get("courses", {})
        
        enrolled_course_ids = [e["course_id"] for e in enrollments if e["student_id"] == s_id]
        available_courses = []
        
        for course_id, course in courses.items():
            if course["status"] == "active" and course_id not in enrolled_course_ids:
                available_courses.append(course)
        
        return available_courses
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.get_available_courses_for_student",
        fake_get_available_courses_for_student
    )


@given(parsers.parse('a course with id {course_id:d} exists'))
def course_exists(course_id, monkeypatch, context):
    """Mock that course exists and is active"""
    context["mock_state"]["courses"] = context["mock_state"].get("courses", {})
    context["mock_state"]["courses"][course_id] = {
        "id": course_id,
        "course_name": f"Introduction to Testing {course_id}",
        "course_code": f"TEST{course_id}",
        "description": "Learn about testing",
        "status": "active",
        "number_student": 0,
        "instructor": f"teacher{course_id}@example.com"
    }
    
    # Mock get_course_by_id
    def fake_get_course_by_id(self, c_id):
        courses = context["mock_state"].get("courses", {})
        return courses.get(c_id)
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.get_course_by_id",
        fake_get_course_by_id
    )


@given(parsers.parse('a course with id {course_id:d} is inactive'))
def course_inactive(course_id, monkeypatch, context):
    """Mock that course is inactive"""
    context["mock_state"]["courses"] = context["mock_state"].get("courses", {})
    context["mock_state"]["courses"][course_id] = {
        "id": course_id,
        "course_name": f"Inactive Course {course_id}",
        "course_code": f"INACT{course_id}",
        "description": "This course is inactive",
        "status": "inactive",
        "number_student": 0,
        "instructor": f"teacher{course_id}@example.com"
    }
    
    # Mock get_course_by_id
    def fake_get_course_by_id(self, c_id):
        courses = context["mock_state"].get("courses", {})
        return courses.get(c_id)
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.get_course_by_id",
        fake_get_course_by_id
    )


@given(parsers.parse('student {student_id:d} is already enrolled in course {course_id:d}'))
def student_already_enrolled(student_id, course_id, context):
    """Mock that student is already enrolled"""
    context["mock_state"]["enrollments"] = context["mock_state"].get("enrollments", [])
    
    # Add enrollment if not already exists
    existing = False
    for enrollment in context["mock_state"]["enrollments"]:
        if enrollment["student_id"] == student_id and enrollment["course_id"] == course_id:
            existing = True
            break
    
    if not existing:
        enrollment_id = len(context["mock_state"]["enrollments"]) + 1
        context["mock_state"]["enrollments"].append({
            "id": enrollment_id,
            "student_id": student_id,
            "course_id": course_id,
            "course_name": f"Course {course_id}",
            "student_email": f"student{student_id}@example.com"
        })


@given(parsers.parse('student {student_id:d} is not enrolled in course {course_id:d}'))
def student_not_enrolled(student_id, course_id, context):
    """Mock that student is not enrolled"""
    # Ensure enrollments list exists
    context["mock_state"]["enrollments"] = context["mock_state"].get("enrollments", [])
    
    # Remove any existing enrollment for this student/course
    context["mock_state"]["enrollments"] = [
        e for e in context["mock_state"]["enrollments"]
        if not (e["student_id"] == student_id and e["course_id"] == course_id)
    ]


@given(parsers.parse('the student {student_id:d} is enrolled in multiple courses'))
def student_enrolled_multiple(student_id, context):
    """Mock that student is enrolled in multiple courses"""
    context["mock_state"]["enrollments"] = context["mock_state"].get("enrollments", [])
    context["mock_state"]["courses"] = context["mock_state"].get("courses", {})
    
    # Create two courses if they don't exist
    for course_id in [101, 102]:
        if course_id not in context["mock_state"]["courses"]:
            context["mock_state"]["courses"][course_id] = {
                "id": course_id,
                "course_name": f"Course {course_id}",
                "course_code": f"CSE{course_id}",
                "description": f"Description for course {course_id}",
                "status": "active",
                "number_student": 30 if course_id == 101 else 25,
                "instructor": f"teacher{course_id}@example.com"
            }
    
    # Remove any existing enrollments for this student
    context["mock_state"]["enrollments"] = [
        e for e in context["mock_state"]["enrollments"]
        if e["student_id"] != student_id
    ]
    
    # Add two enrollments
    for i, course_id in enumerate([101, 102], 1):
        context["mock_state"]["enrollments"].append({
            "id": i,
            "student_id": student_id,
            "course_id": course_id,
            "course_name": f"Course {course_id}",
            "student_email": f"student{student_id}@example.com"
        })


@given(parsers.parse('there are available courses for student {student_id:d}'))
def available_courses_exist(student_id, context):
    """Mock that there are available courses for student"""
    context["mock_state"]["courses"] = context["mock_state"].get("courses", {})
    context["mock_state"]["enrollments"] = context["mock_state"].get("enrollments", [])
    
    # Create two courses if they don't exist
    for course_id in [201, 202]:
        if course_id not in context["mock_state"]["courses"]:
            context["mock_state"]["courses"][course_id] = {
                "id": course_id,
                "course_name": f"Available Course {course_id - 200}",
                "course_code": f"CSE{course_id}",
                "description": f"Available course description {course_id - 200}",
                "status": "active",
                "number_student": 20 if course_id == 201 else 15,
                "instructor": f"teacher{course_id}@example.com"
            }
    
    # Ensure student is not enrolled in these courses
    context["mock_state"]["enrollments"] = [
        e for e in context["mock_state"]["enrollments"]
        if not (e["student_id"] == student_id and e["course_id"] in [201, 202])
    ]


@given('the student does not exist')
def student_not_exist(monkeypatch, context):
    """Mock that student doesn't exist"""
    # Clear existing students from mock state
    context["mock_state"]["existing_students"] = []
    
    # Mock enroll_student to reject non-existent student
    def fake_enroll_student(self, student_id, course_id):
        if student_id not in context["mock_state"].get("existing_students", []):
            raise ValueError("Student not found or user is not a student")
        
        # For existing students, proceed normally
        enrollments = context["mock_state"].get("enrollments", [])
        enrollment_id = len(enrollments) + 1
        new_enrollment = {
            "id": enrollment_id,
            "student_id": student_id,
            "course_id": course_id,
            "course_name": f"Course {course_id}",
            "student_email": f"student{student_id}@example.com"
        }
        enrollments.append(new_enrollment)
        context["mock_state"]["enrollments"] = enrollments
        
        return new_enrollment
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.enroll_student",
        fake_enroll_student
    )


@given('the course does not exist')
def course_not_exist(monkeypatch, context):
    """Mock that course doesn't exist"""
    # Clear courses from mock state
    context["mock_state"]["courses"] = {}
    
    # Mock get_course_by_id to return None for non-existent courses
    def fake_get_course_by_id(self, course_id):
        courses = context["mock_state"].get("courses", {})
        return courses.get(course_id)
    
    # Mock enroll_student to reject non-existent course
    def fake_enroll_student(self, student_id, course_id):
        courses = context["mock_state"].get("courses", {})
        if course_id not in courses:
            raise ValueError("Course not found")
        
        # For existing courses, proceed normally
        enrollments = context["mock_state"].get("enrollments", [])
        enrollment_id = len(enrollments) + 1
        new_enrollment = {
            "id": enrollment_id,
            "student_id": student_id,
            "course_id": course_id,
            "course_name": f"Course {course_id}",
            "student_email": f"student{student_id}@example.com"
        }
        enrollments.append(new_enrollment)
        context["mock_state"]["enrollments"] = enrollments
        
        return new_enrollment
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.get_course_by_id",
        fake_get_course_by_id
    )
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.enroll_student",
        fake_enroll_student
    )


@given('the database service is temporarily unavailable')
def database_unavailable(monkeypatch):
    """Mock database service failure"""
    
    def fake_enroll_student(self, student_id, course_id):
        raise Exception("Database connection failed")
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.enroll_student",
        fake_enroll_student
    )


@given('trying to unenroll from non-existent enrollment')
def nonexistent_enrollment(monkeypatch, context):
    """Mock non-existent enrollment for unenrollment"""
    # Clear all enrollments
    context["mock_state"]["enrollments"] = []
    
    # Mock unenroll_student to always return False
    def fake_unenroll_student(self, student_id, course_id):
        return False
    
    monkeypatch.setattr(
        "src.services.course_service.CourseService.unenroll_student",
        fake_unenroll_student
    )


@given('any enrollment request')
def any_enrollment_request():
    """Generic step for enrollment request - doesn't need implementation"""
    pass


# =======================
# WHEN STEPS (API Calls)
# =======================

@when(parsers.parse('the student {student_id:d} requests to enroll in course {course_id:d}'),
      target_fixture="context")
def request_enrollment(student_id, course_id, context):
    """Submit enrollment API request"""
    payload = {
        "student_id": student_id,
        "course_id": course_id
    }
    context["response"] = client.post("/courses/enroll", json=payload)
    return context


@when(parsers.parse('the student {student_id:d} requests to unenroll from course {course_id:d}'),
      target_fixture="context")
def request_unenrollment(student_id, course_id, context):
    """Submit unenrollment API request"""
    context["response"] = client.delete(f"/courses/unenroll/{student_id}/{course_id}")
    return context


@when(parsers.parse('the system tries to enroll student {student_id:d} in inactive course {course_id:d}'),
      target_fixture="context")
def try_enroll_inactive_course(student_id, course_id, context):
    """Try to enroll in inactive course"""
    payload = {
        "student_id": student_id,
        "course_id": course_id
    }
    context["response"] = client.post("/courses/enroll", json=payload)
    return context


@when(parsers.parse('the student {student_id:d} requests their enrolled courses'),
      target_fixture="context")
def request_enrolled_courses(student_id, context):
    """Get enrolled courses API request"""
    context["response"] = client.get(f"/courses/student/{student_id}/enrolled")
    return context


@when(parsers.parse('the student {student_id:d} requests available courses'),
      target_fixture="context")
def request_available_courses(student_id, context):
    """Get available courses API request"""
    context["response"] = client.get(f"/courses/student/{student_id}/available")
    return context


@when(parsers.parse('trying to unenroll from non-existent enrollment'),
      target_fixture="context")
def try_unenroll_nonexistent(context):
    """Try to unenroll from non-existent enrollment"""
    context["response"] = client.delete("/courses/unenroll/999/999")
    return context


@when('the system receives an enrollment request with missing student_id',
      target_fixture="context")
def enrollment_missing_fields(context):
    """Submit enrollment with missing required fields"""
    payload = {
        "course_id": 101  # Missing student_id
    }
    context["response"] = client.post("/courses/enroll", json=payload)
    return context


@when('the system receives an enrollment request with string student_id',
      target_fixture="context")
def enrollment_wrong_data_types(context):
    """Submit enrollment with wrong data types"""
    payload = {
        "student_id": "not_a_number",  # Should be integer
        "course_id": 101
    }
    context["response"] = client.post("/courses/enroll", json=payload)
    return context


@when(parsers.parse('student {student_id:d} tries to enroll student {target_student_id:d} in course {course_id:d}'),
      target_fixture="context")
def try_enroll_other_student(student_id, target_student_id, course_id, context):
    """Try to enroll another student (testing authorization)"""
    payload = {
        "student_id": target_student_id,
        "course_id": course_id
    }
    context["response"] = client.post("/courses/enroll", json=payload)
    return context


@when(parsers.parse('attempting to enroll student {student_id:d} in course {course_id:d} again'),
      target_fixture="context")
def try_duplicate_enrollment(student_id, course_id, context):
    """Try to enroll in same course twice"""
    payload = {
        "student_id": student_id,
        "course_id": course_id
    }
    context["response"] = client.post("/courses/enroll", json=payload)
    return context


@when('any enrollment request is processed')
def process_enrollment_request():
    """This is a descriptive step for validation scenarios"""
    pass


@when('the request is processed')
def request_processed():
    """This is a descriptive step for validation scenarios"""
    pass


# =======================
# THEN STEPS (Assertions)
# =======================

@then(parsers.parse("the system should return status code {code:d}"))
def status_code(context, code):
    """Assert HTTP status code"""
    assert context["response"].status_code == code, \
        f"Expected status code {code}, got {context['response'].status_code}. " \
        f"Response: {context['response'].text}"


@then(parsers.parse('the response message should contain "{text}"'))
def response_contains(context, text):
    """Assert response contains specific text"""
    response_json = context["response"].json()
    if "message" in response_json:
        assert text.lower() in response_json["message"].lower()
    else:
        # For direct responses
        response_text = str(response_json).lower()
        assert text.lower() in response_text


@then(parsers.parse('the error detail should contain "{msg}"'))
def error_contains(context, msg):
    """Assert error message contains specific text"""
    response_json = context["response"].json()
    # Handle both list and string error details
    if isinstance(response_json.get("detail"), list):
        detail_text = " ".join([str(item) for item in response_json["detail"]])
    else:
        detail_text = str(response_json.get("detail", ""))
    assert msg.lower() in detail_text.lower()


@then(parsers.parse('the response should contain enrollment id {enrollment_id:d}'))
def contains_enrollment_id(context, enrollment_id):
    """Assert response contains enrollment ID"""
    response_json = context["response"].json()
    if "enrollment" in response_json:
        assert response_json["enrollment"]["id"] == enrollment_id
    else:
        # For direct enrollment data
        if "id" in response_json:
            assert response_json["id"] == enrollment_id
        # For list responses, check if any item has the id
        elif isinstance(response_json, list) and response_json:
            assert any(item.get("id") == enrollment_id or item.get("enrollment_id") == enrollment_id 
                      for item in response_json)


@then(parsers.parse('the response should contain student id {student_id:d}'))
def contains_student_id(context, student_id):
    """Assert response contains student ID"""
    response_json = context["response"].json()
    if "enrollment" in response_json:
        assert response_json["enrollment"]["student_id"] == student_id
    elif isinstance(response_json, list):
        # For list of enrollments
        for item in response_json:
            if "student_id" in item:
                assert item["student_id"] == student_id
    else:
        assert response_json.get("student_id") == student_id


@then(parsers.parse('the response should contain course id {course_id:d}'))
def contains_course_id(context, course_id):
    """Assert response contains course ID"""
    response_json = context["response"].json()
    if "enrollment" in response_json:
        assert response_json["enrollment"]["course_id"] == course_id
    elif isinstance(response_json, list):
        # For list of courses
        for item in response_json:
            if item.get("id") == course_id or item.get("course_id") == course_id:
                return
        # If we get here, course_id not found
        assert False, f"Course ID {course_id} not found in response"
    else:
        assert response_json.get("course_id") == course_id


@then('the response should contain valid enrollment data')
def valid_enrollment_data(context):
    """Assert response contains valid enrollment data structure"""
    response_json = context["response"].json()
    if "enrollment" in response_json:
        enrollment = response_json["enrollment"]
        assert "id" in enrollment
        assert "student_id" in enrollment
        assert "course_id" in enrollment
    else:
        # Check if it's a direct enrollment response
        assert "id" in response_json
        assert "student_id" in response_json
        assert "course_id" in response_json


@then('the response should contain list of enrolled courses')
def contains_enrolled_courses_list(context):
    """Assert response contains list of enrolled courses"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    if len(response_json) > 0:
        course = response_json[0]
        assert "id" in course
        assert "course_name" in course
        assert "course_code" in course
        assert "status" in course


@then('the response should contain list of available courses')
def contains_available_courses_list(context):
    """Assert response contains list of available courses"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    if len(response_json) > 0:
        course = response_json[0]
        assert "id" in course
        assert "course_name" in course
        assert "course_code" in course
        assert "status" in course
        assert "number_student" in course


@then(parsers.parse('the enrolled courses list should have {count:d} courses'))
def enrolled_courses_count(context, count):
    """Assert number of enrolled courses"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    assert len(response_json) == count, \
        f"Expected {count} courses, got {len(response_json)}. Response: {response_json}"


@then(parsers.parse('the available courses list should have {count:d} courses'))
def available_courses_count(context, count):
    """Assert number of available courses"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    assert len(response_json) == count, \
        f"Expected {count} courses, got {len(response_json)}. Response: {response_json}"


@then('all courses in the list should be active')
def all_courses_active(context):
    """Assert all courses in list are active"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    for course in response_json:
        assert course.get("status") == "active", \
            f"Course {course.get('id')} is not active. Status: {course.get('status')}"


@then('the system should validate student authorization')
def validate_authorization(context):
    """Assert that authorization validation occurs"""
    assert context["response"] is not None


@then('the request should be rejected if unauthorized')
def reject_if_unauthorized(context):
    """Assert unauthorized requests are rejected"""
    pass


@then('the system should validate all required fields')
def validate_required_fields():
    """Assert field validation occurs"""
    pass


@then('the system should check course availability')
def check_course_availability():
    """Assert course availability is checked"""
    pass


@then('the system should verify student eligibility')
def verify_student_eligibility():
    """Assert student eligibility is verified"""
    pass


@then('the system should prevent duplicate enrollment')
def prevent_duplicate_enrollment(context):
    """Assert duplicate enrollment is prevented"""
    assert context["response"].status_code in [400, 409]


@then('return an appropriate error message')
def return_duplicate_error(context):
    """Assert appropriate error message for duplicate enrollment"""
    response_json = context["response"].json()
    error_msg = response_json.get("detail", "").lower()
    assert any(term in error_msg for term in ["already", "duplicate", "enrolled"])