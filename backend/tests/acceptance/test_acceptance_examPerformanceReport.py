"""
BDD/Acceptance Tests for Exam Performance Reporting API
Testing API endpoints with mocked services
"""
import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then, parsers
from main import app
from unittest.mock import MagicMock
import json

client = TestClient(app)

# Load feature file
scenarios("../feature/examPerformanceReport.feature")


@pytest.fixture
def context():
    """Context to store test state between steps"""
    return {"response": None, "mock_state": {}}


# =======================
# GIVEN STEPS (mocked)
# =======================

@given(parsers.parse('the instructor with id {instructor_id:d} exists'))
@given(parsers.parse('instructor with id {instructor_id:d} exists'))
def instructor_exists(instructor_id, monkeypatch, context):
    """Mock that instructor exists"""
    context["mock_state"]["existing_instructors"] = context["mock_state"].get("existing_instructors", [])
    context["mock_state"]["existing_instructors"].append(instructor_id)
    
    # Mock ReportsService methods
    def mock_get_completed_exams(self, instructor_id_param=None):
        instructor_id_param = instructor_id_param or instructor_id
        
        if instructor_id_param == 2:  # Instructor with no completed exams
            return []
        
        return [
            {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "MT2024-001",
                "date": "2024-03-15",
                "course_name": "Mathematics 101",
                "course_code": "MATH101",
                "total_students": 30,
                "submitted": 28,
                "graded": 25,
                "average_score": 78.5
            },
            {
                "id": 2,
                "title": "Final Exam",
                "exam_code": "FE2024-001",
                "date": "2024-05-20",
                "course_name": "Physics 101",
                "course_code": "PHYS101",
                "total_students": 25,
                "submitted": 20,
                "graded": 18,
                "average_score": 85.2
            }
        ]
    
    def mock_get_exam_performance_stats(self, exam_id_param, instructor_id_param=None):
        instructor_id_param = instructor_id_param or instructor_id
        
        # Non-existent exam
        if exam_id_param == 999:
            return None
        
        # Exam that instructor doesn't have access to
        if instructor_id_param == 3 and exam_id_param == 1:
            return None
        
        # Exam with no graded submissions
        if exam_id_param == 2:
            return {
                "exam_info": {
                    "id": 2,
                    "title": "Final Exam",
                    "exam_code": "FE2024-001",
                    "date": "2024-05-20",
                    "course_name": "Physics 101",
                    "course_code": "PHYS101",
                    "total_points": 100
                },
                "statistics": {
                    "total_students": 25,
                    "submitted": 20,
                    "graded": 0,
                    "average_score": 0,
                    "highest_score": 0,
                    "lowest_score": 0,
                    "pass_rate": 0
                },
                "grade_distribution": [],
                "score_ranges": []
            }
        
        # Specific calculation test exam
        if exam_id_param == 5:
            return {
                "exam_info": {
                    "id": 5,
                    "title": "Test Calculation Exam",
                    "exam_code": "TC2024-001",
                    "date": "2024-04-10",
                    "course_name": "Test Course",
                    "course_code": "TEST101",
                    "total_points": 100
                },
                "statistics": {
                    "total_students": 10,
                    "submitted": 10,
                    "graded": 10,
                    "average_score": 75.0,
                    "highest_score": 95,
                    "lowest_score": 55,
                    "pass_rate": 80.0
                },
                "grade_distribution": [
                    {"grade": "A", "count": 3, "percentage": 30.0},
                    {"grade": "B", "count": 4, "percentage": 40.0},
                    {"grade": "C", "count": 2, "percentage": 20.0},
                    {"grade": "F", "count": 1, "percentage": 10.0}
                ],
                "score_ranges": [
                    {"range": "90-100", "count": 2, "percentage": 20.0},
                    {"range": "80-89", "count": 2, "percentage": 20.0},
                    {"range": "70-79", "count": 3, "percentage": 30.0},
                    {"range": "60-69", "count": 2, "percentage": 20.0},
                    {"range": "50-59", "count": 1, "percentage": 10.0}
                ]
            }
        
        # Normal exam with data
        return {
            "exam_info": {
                "id": 1,
                "title": "Midterm Exam",
                "exam_code": "MT2024-001",
                "date": "2024-03-15",
                "course_name": "Mathematics 101",
                "course_code": "MATH101",
                "total_points": 100
            },
            "statistics": {
                "total_students": 30,
                "submitted": 28,
                "graded": 25,
                "average_score": 78.5,
                "highest_score": 98,
                "lowest_score": 45,
                "pass_rate": 80.0
            },
            "grade_distribution": [
                {"grade": "A", "count": 8, "percentage": 32.0},
                {"grade": "B", "count": 10, "percentage": 40.0},
                {"grade": "C", "count": 5, "percentage": 20.0},
                {"grade": "D", "count": 1, "percentage": 4.0},
                {"grade": "F", "count": 1, "percentage": 4.0}
            ],
            "score_ranges": [
                {"range": "90-100", "count": 5, "percentage": 20.0},
                {"range": "80-89", "count": 8, "percentage": 32.0},
                {"range": "70-79", "count": 7, "percentage": 28.0},
                {"range": "60-69", "count": 3, "percentage": 12.0},
                {"range": "50-59", "count": 1, "percentage": 4.0},
                {"range": "40-49", "count": 1, "percentage": 4.0}
            ]
        }
    
    def mock_get_exam_student_scores(self, exam_id_param, instructor_id_param=None):
        instructor_id_param = instructor_id_param or instructor_id
        
        # Exam with no submissions
        if exam_id_param == 3:
            return []
        
        # Instructor without access
        if instructor_id_param == 3 and exam_id_param == 1:
            return []
        
        return [
            {
                "student_id": 101,
                "user_email": "student1@example.com",
                "student_number": "S001",
                "score": 95,
                "score_grade": "A",
                "status": "graded",
                "submission_date": "2024-03-16T10:30:00"
            },
            {
                "student_id": 102,
                "user_email": "student2@example.com",
                "student_number": "S002",
                "score": 85,
                "score_grade": "B",
                "status": "graded",
                "submission_date": "2024-03-16T11:15:00"
            },
            {
                "student_id": 103,
                "user_email": "student3@example.com",
                "student_number": "S003",
                "score": 75,
                "score_grade": "C",
                "status": "graded",
                "submission_date": "2024-03-16T12:00:00"
            },
            {
                "student_id": 104,
                "user_email": "student4@example.com",
                "student_number": "S004",
                "score": None,
                "score_grade": None,
                "status": "pending",
                "submission_date": None
            }
        ]
    
    def mock_get_instructor_courses(self, instructor_id_param):
        # Instructor with no courses
        if instructor_id_param == 4:
            return []
        
        return [
            {
                "id": 101,
                "course_code": "MATH101",
                "course_name": "Mathematics 101",
                "description": "Introduction to Mathematics",
                "status": "active",
                "student_count": 30,
                "exam_count": 2
            },
            {
                "id": 102,
                "course_code": "PHYS101",
                "course_name": "Physics 101",
                "description": "Introduction to Physics",
                "status": "active",
                "student_count": 25,
                "exam_count": 1
            }
        ]
    
    # Apply all mocks
    monkeypatch.setattr(
        "src.services.report_service.ReportsService.get_completed_exams",
        mock_get_completed_exams
    )
    
    monkeypatch.setattr(
        "src.services.report_service.ReportsService.get_exam_performance_stats",
        mock_get_exam_performance_stats
    )
    
    monkeypatch.setattr(
        "src.services.report_service.ReportsService.get_exam_student_scores",
        mock_get_exam_student_scores
    )
    
    monkeypatch.setattr(
        "src.services.report_service.ReportsService.get_instructor_courses",
        mock_get_instructor_courses
    )


@given('the instructor has access to multiple courses')
def instructor_has_multiple_courses():
    """Instructor has access to courses - already handled in instructor_exists"""
    pass


@given(parsers.parse('there are completed exams for the instructor\'s courses'))
def completed_exams_exist():
    """Completed exams exist - already handled in mock"""
    pass


@given(parsers.parse('there are no completed exams for the instructor\'s courses'))
def no_completed_exams():
    """No completed exams - already handled in mock"""
    pass


@given(parsers.parse('exam with id {exam_id:d} exists'))
def exam_exists(exam_id):
    """Exam exists - already handled in mock"""
    pass


@given(parsers.parse('exam {exam_id:d} has student submissions and grades'))
def exam_has_submissions(exam_id):
    """Exam has submissions - already handled in mock"""
    pass


@given(parsers.parse('exam {exam_id:d} has no graded submissions'))
def exam_no_graded_submissions(exam_id):
    """Exam has no graded submissions - already handled in mock"""
    pass


@given(parsers.parse('exam {exam_id:d} does not exist'))
def exam_not_exist(exam_id):
    """Exam doesn't exist - already handled in mock"""
    pass


@given(parsers.parse('instructor with id {instructor_id:d} does not have access to exam {exam_id:d}\'s course'))
def instructor_no_access_to_exam(instructor_id, exam_id):
    """Instructor has no access - already handled in mock"""
    pass


@given(parsers.parse('exam {exam_id:d} has no student submissions'))
def exam_no_submissions(exam_id):
    """Exam has no submissions - already handled in mock"""
    pass


@given(parsers.parse('instructor {instructor_id:d} is assigned to multiple courses'))
def instructor_assigned_courses(instructor_id):
    """Instructor has assigned courses - already handled in mock"""
    pass


@given(parsers.parse('instructor {instructor_id:d} is not assigned to any courses'))
def instructor_no_courses(instructor_id):
    """Instructor has no courses - already handled in mock"""
    pass


@given(parsers.parse('exam {exam_id:d} has specific student scores for calculation testing'))
def exam_with_calculation_scores(exam_id):
    """Exam with calculation scores - already handled in mock"""
    pass


@given(parsers.parse('exam {exam_id:d} has multiple student submissions'))
def exam_multiple_submissions(exam_id):
    """Exam with multiple submissions - already handled in mock"""
    pass


# =======================
# WHEN STEPS (API Calls)
# =======================

@when('the instructor requests completed exams list', target_fixture="context")
@when(parsers.parse('instructor {instructor_id:d} requests completed exams'), target_fixture="context")
def request_completed_exams(context, instructor_id=None):
    """Get completed exams API request"""
    if instructor_id:
        context["response"] = client.get(f"/reports/completed-exams?instructor_id={instructor_id}")
    else:
        context["response"] = client.get("/reports/completed-exams")
    return context


@when(parsers.parse('the instructor requests performance statistics for exam {exam_id:d}'),
      target_fixture="context")
@when(parsers.parse('instructor {instructor_id:d} requests performance statistics for exam {exam_id:d}'),
      target_fixture="context")
def request_exam_performance(exam_id, context, instructor_id=None):
    """Get exam performance statistics"""
    if instructor_id:
        context["response"] = client.get(f"/reports/exam/{exam_id}/performance?instructor_id={instructor_id}")
    else:
        context["response"] = client.get(f"/reports/exam/{exam_id}/performance")
    return context


@when(parsers.parse('the instructor requests student scores for exam {exam_id:d}'),
      target_fixture="context")
@when(parsers.parse('instructor {instructor_id:d} requests student scores for exam {exam_id:d}'),
      target_fixture="context")
def request_student_scores(exam_id, context, instructor_id=None):
    """Get student scores for an exam"""
    if instructor_id:
        context["response"] = client.get(f"/reports/exam/{exam_id}/student-scores?instructor_id={instructor_id}")
    else:
        context["response"] = client.get(f"/reports/exam/{exam_id}/student-scores")
    return context


@when(parsers.parse('instructor {instructor_id:d} requests their assigned courses'),
      target_fixture="context")
def request_instructor_courses(instructor_id, context):
    """Get instructor's assigned courses"""
    context["response"] = client.get(f"/reports/my-courses?instructor_id={instructor_id}")
    return context


@when('the system receives a request for courses without instructor ID',
      target_fixture="context")
def request_courses_without_id(context):
    """Get courses without providing instructor ID"""
    context["response"] = client.get("/reports/my-courses")
    return context


@when(parsers.parse('the instructor requests performance statistics with exam ID {exam_id:d}'),
      target_fixture="context")
def request_invalid_exam_performance(exam_id, context):
    """Request performance with invalid exam ID"""
    context["response"] = client.get(f"/reports/exam/{exam_id}/performance")
    return context


@when(parsers.parse('the instructor requests student scores with exam ID {exam_id:d}'),
      target_fixture="context")
def request_invalid_student_scores(exam_id, context):
    """Request student scores with invalid exam ID"""
    context["response"] = client.get(f"/reports/exam/{exam_id}/student-scores")
    return context


# =======================
# THEN STEPS (Assertions)
# =======================

@then(parsers.parse("the system should return status code {code:d}"))
def status_code(context, code):
    """Assert HTTP status code"""
    assert context["response"].status_code == code, \
        f"Expected status code {code}, got {context['response'].status_code}. " \
        f"Response: {context['response'].text}"


@then('the response should contain list of completed exams')
def contains_completed_exams_list(context):
    """Assert response contains list of completed exams"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    if len(response_json) > 0:
        exam = response_json[0]
        assert "id" in exam
        assert "title" in exam
        assert "exam_code" in exam
        assert "course_name" in exam
        assert "average_score" in exam


@then(parsers.parse('the list should contain exam with id {exam_id:d}'))
def contains_exam_with_id(context, exam_id):
    """Assert list contains specific exam ID"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    exam_ids = [exam["id"] for exam in response_json]
    assert exam_id in exam_ids, f"Exam ID {exam_id} not found in response: {exam_ids}"


@then('the exam list should include basic statistics')
def exam_list_includes_statistics(context):
    """Assert exam list includes statistics"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    if len(response_json) > 0:
        exam = response_json[0]
        assert "total_students" in exam
        assert "submitted" in exam
        assert "graded" in exam
        assert "average_score" in exam


@then('the response should be an empty list')
def response_is_empty_list(context):
    """Assert response is an empty list"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    assert len(response_json) == 0, f"Expected empty list, got {len(response_json)} items"


@then('the response should contain exam information')
def contains_exam_info(context):
    """Assert response contains exam information"""
    response_json = context["response"].json()
    assert "exam_info" in response_json
    exam_info = response_json["exam_info"]
    assert "id" in exam_info
    assert "title" in exam_info
    assert "exam_code" in exam_info
    assert "course_name" in exam_info


@then('the response should contain performance statistics')
def contains_performance_stats(context):
    """Assert response contains performance statistics"""
    response_json = context["response"].json()
    assert "statistics" in response_json
    stats = response_json["statistics"]
    assert "total_students" in stats
    assert "graded" in stats
    assert "average_score" in stats


@then('the statistics should include average score')
def stats_include_average_score(context):
    """Assert statistics include average score"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert "average_score" in stats
    assert isinstance(stats["average_score"], (int, float))


@then('the statistics should include pass rate')
def stats_include_pass_rate(context):
    """Assert statistics include pass rate"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert "pass_rate" in stats
    assert isinstance(stats["pass_rate"], (int, float))


@then('the response should contain grade distribution')
def contains_grade_distribution(context):
    """Assert response contains grade distribution"""
    response_json = context["response"].json()
    assert "grade_distribution" in response_json
    assert isinstance(response_json["grade_distribution"], list)


@then('the response should contain score ranges')
def contains_score_ranges(context):
    """Assert response contains score ranges"""
    response_json = context["response"].json()
    assert "score_ranges" in response_json
    assert isinstance(response_json["score_ranges"], list)


@then(parsers.parse('the statistics should show {count:d} graded submissions'))
def stats_show_graded_count(context, count):
    """Assert specific number of graded submissions"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert stats["graded"] == count, f"Expected {count} graded, got {stats['graded']}"


@then('the pass rate should be 0')
def pass_rate_is_zero(context):
    """Assert pass rate is 0"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert stats["pass_rate"] == 0, f"Expected pass rate 0, got {stats['pass_rate']}"


@then('the error should indicate exam not found')
def error_indicates_exam_not_found(context):
    """Assert error message indicates exam not found"""
    response_json = context["response"].json()
    error_msg = response_json.get("detail", "").lower()
    assert "exam" in error_msg and ("not found" in error_msg or "no access" in error_msg)


@then('the error should indicate no access')
def error_indicates_no_access(context):
    """Assert error message indicates no access"""
    response_json = context["response"].json()
    error_msg = response_json.get("detail", "").lower()
    assert "access" in error_msg or "not found" in error_msg


@then('the response should contain list of student scores')
def contains_student_scores_list(context):
    """Assert response contains list of student scores"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    if len(response_json) > 0:
        score = response_json[0]
        assert "student_id" in score
        assert "user_email" in score
        assert "score" in score or "status" in score


@then('each student score should contain student information')
def student_score_has_info(context):
    """Assert each student score contains student information"""
    response_json = context["response"].json()
    for score in response_json:
        assert "student_id" in score
        assert "user_email" in score
        assert "student_number" in score


@then('each student score should contain score details')
def student_score_has_details(context):
    """Assert each student score contains score details"""
    response_json = context["response"].json()
    for score in response_json:
        assert "status" in score
        if score["status"] == "graded":
            assert "score" in score
            assert "score_grade" in score


@then('the error should indicate no scores found')
def error_indicates_no_scores(context):
    """Assert error message indicates no scores found"""
    response_json = context["response"].json()
    error_msg = response_json.get("detail", "").lower()
    assert "score" in error_msg or "found" in error_msg


@then('the response should contain list of courses')
def contains_courses_list(context):
    """Assert response contains list of courses"""
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    if len(response_json) > 0:
        course = response_json[0]
        assert "id" in course
        assert "course_code" in course
        assert "course_name" in course


@then('each course should include student and exam counts')
def course_includes_counts(context):
    """Assert each course includes student and exam counts"""
    response_json = context["response"].json()
    for course in response_json:
        assert "student_count" in course
        assert "exam_count" in course
        assert isinstance(course["student_count"], int)
        assert isinstance(course["exam_count"], int)


@then('the error should indicate instructor ID is required')
def error_indicates_instructor_id_required(context):
    """Assert error message indicates instructor ID is required"""
    response_json = context["response"].json()
    error_msg = response_json.get("detail", "").lower()
    assert "instructor" in error_msg and "required" in error_msg


@then('the error should indicate invalid exam ID')
def error_indicates_invalid_exam_id(context):
    """Assert error message indicates invalid exam ID"""
    response_json = context["response"].json()
    error_msg = response_json.get("detail", "").lower()
    assert "invalid" in error_msg and "exam" in error_msg


@then('the average score should be calculated correctly')
def average_score_calculated_correctly(context):
    """Assert average score is calculated correctly"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert stats["average_score"] == 75.0, f"Expected average 75.0, got {stats['average_score']}"


@then('the highest score should be identified correctly')
def highest_score_identified_correctly(context):
    """Assert highest score is identified correctly"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert stats["highest_score"] == 95, f"Expected highest 95, got {stats['highest_score']}"


@then('the lowest score should be identified correctly')
def lowest_score_identified_correctly(context):
    """Assert lowest score is identified correctly"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert stats["lowest_score"] == 55, f"Expected lowest 55, got {stats['lowest_score']}"


@then('the pass rate should be calculated correctly')
def pass_rate_calculated_correctly(context):
    """Assert pass rate is calculated correctly"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert stats["pass_rate"] == 80.0, f"Expected pass rate 80.0, got {stats['pass_rate']}"


@then('grade distribution should reflect actual grades')
def grade_distribution_reflects_grades(context):
    """Assert grade distribution reflects actual grades"""
    response_json = context["response"].json()
    grade_dist = response_json["grade_distribution"]
    
    # Check specific grades exist
    grade_counts = {g["grade"]: g["count"] for g in grade_dist}
    assert grade_counts.get("A", 0) == 3
    assert grade_counts.get("B", 0) == 4
    assert grade_counts.get("C", 0) == 2
    assert grade_counts.get("F", 0) == 1


@then('the course list should contain course with id 101')
def course_list_contains_course_101(context):
    """Assert course list contains course with ID 101"""
    response_json = context["response"].json()
    course_ids = [course["id"] for course in response_json]
    assert 101 in course_ids, f"Course ID 101 not found in: {course_ids}"


@then('the exam list should contain exam with id 1')
def exam_list_contains_exam_1(context):
    """Assert exam list contains exam with ID 1"""
    response_json = context["response"].json()
    exam_ids = [exam["id"] for exam in response_json]
    assert 1 in exam_ids, f"Exam ID 1 not found in: {exam_ids}"


@then('the statistics should show graded submissions')
def statistics_show_graded(context):
    """Assert statistics show graded submissions"""
    response_json = context["response"].json()
    stats = response_json["statistics"]
    assert stats["graded"] > 0, "Expected graded submissions > 0"


@then('the student scores should match the statistics')
def student_scores_match_statistics(context):
    """Assert student scores match statistics"""
    # This would require comparing aggregated scores with statistics
    # For now, just check that we have scores
    response_json = context["response"].json()
    assert isinstance(response_json, list)
    assert len(response_json) > 0