Feature: Course Enrollment Management
  As a student
  I want to enroll in and manage my courses
  So that I can participate in academic activities

  # ============================================
  # VIEW ENROLLED COURSES
  # ============================================

  Scenario: View enrolled courses for student
    Given a student with id 1 exists
    And the student 1 is enrolled in multiple courses
    When the student 1 requests their enrolled courses
    Then the system should return status code 200
    And the response should contain list of enrolled courses
    And the enrolled courses list should have 2 courses
    And all courses in the list should be active

  Scenario: View enrolled courses for student with no enrollments
    Given a student with id 2 exists
    When the student 2 requests their enrolled courses
    Then the system should return status code 200
    And the response should contain list of enrolled courses
    And the enrolled courses list should have 0 courses

  # ============================================
  # VIEW AVAILABLE COURSES
  # ============================================

  Scenario: View available courses for student
    Given a student with id 1 exists
    And there are available courses for student 1
    When the student 1 requests available courses
    Then the system should return status code 200
    And the response should contain list of available courses
    And the available courses list should have 2 courses
    And all courses in the list should be active

  Scenario: View available courses when enrolled in all
    Given a student with id 3 exists
    When the student 3 requests available courses
    Then the system should return status code 200
    And the response should contain list of available courses
    And the available courses list should have 0 courses

  # ============================================
  # SUCCESSFUL ENROLLMENT
  # ============================================

  Scenario: Successfully enroll student in course
    Given a student with id 1 exists
    And a course with id 101 exists
    And student 1 is not enrolled in course 101
    When the student 1 requests to enroll in course 101
    Then the system should return status code 200
    And the response message should contain "Successfully enrolled"
    And the response should contain valid enrollment data
    And the response should contain enrollment id 1
    And the response should contain student id 1
    And the response should contain course id 101

  Scenario: Enroll student in another course
    Given a student with id 2 exists
    And a course with id 102 exists
    And student 2 is not enrolled in course 102
    When the student 2 requests to enroll in course 102
    Then the system should return status code 200
    And the response message should contain "Successfully enrolled"
    And the response should contain valid enrollment data

  # ============================================
  # ENROLLMENT FAILURES
  # ============================================

  Scenario: Try to enroll in non-existent course
    Given a student with id 1 exists
    And the course does not exist
    When the student 1 requests to enroll in course 999
    Then the system should return status code 400
    And the error detail should contain "Course not found"

  Scenario: Try to enroll non-existent student
    Given the student does not exist
    And a course with id 101 exists
    When the student 999 requests to enroll in course 101
    Then the system should return status code 400
    And the error detail should contain "Student not found"

  Scenario: Try to enroll in inactive course
    Given a student with id 1 exists
    And a course with id 103 is inactive
    When the system tries to enroll student 1 in inactive course 103
    Then the system should return status code 400
    And the error detail should contain "inactive course"

  Scenario: Try to enroll when already enrolled
    Given a student with id 1 exists
    And a course with id 101 exists
    And student 1 is already enrolled in course 101
    When the student 1 requests to enroll in course 101
    Then the system should return status code 400
    And the error detail should contain "already enrolled"

  # ============================================
  # UNENROLLMENT
  # ============================================

  Scenario: Successfully unenroll student from course
    Given a student with id 1 exists
    And a course with id 101 exists
    And student 1 is already enrolled in course 101
    When the student 1 requests to unenroll from course 101
    Then the system should return status code 200
    And the response message should contain "Successfully unenrolled"


  # ============================================
  # COMPREHENSIVE ENROLLMENT FLOW
  # ============================================

  Scenario: Complete enrollment flow for new student
    Given a student with id 4 exists
    And a course with id 104 exists
    And student 4 is not enrolled in course 104
    When the student 4 requests available courses
    Then the system should return status code 200
    And the available courses list should have 1 courses
    When the student 4 requests to enroll in course 104
    Then the system should return status code 200
    And the response message should contain "Successfully enrolled"
    When the student 4 requests their enrolled courses
    Then the system should return status code 200
    And the enrolled courses list should have 1 courses
    And the response should contain course id 104
    When the student 4 requests available courses
    Then the system should return status code 200
    And the available courses list should have 0 courses

  Scenario: Student enrolls and unenrolls from course
    Given a student with id 5 exists
    And a course with id 105 exists
    And student 5 is not enrolled in course 105
    When the student 5 requests to enroll in course 105
    Then the system should return status code 200
    And the response message should contain "Successfully enrolled"
    When the student 5 requests their enrolled courses
    Then the system should return status code 200
    And the enrolled courses list should have 1 courses
    When the student 5 requests to unenroll from course 105
    Then the system should return status code 200
    And the response message should contain "Successfully unenrolled"
    When the student 5 requests their enrolled courses
    Then the system should return status code 200
    And the enrolled courses list should have 0 courses

  # ============================================
  # ERROR HANDLING
  # ============================================

  Scenario: Invalid enrollment request (missing fields)
    When the system receives an enrollment request with missing student_id
    Then the system should return status code 422
    And the error detail should contain "field required"

  Scenario: Invalid enrollment request (wrong data types)
    When the system receives an enrollment request with string student_id
    Then the system should return status code 422
    And the error detail should contain "input should be a valid integer"

  # ============================================
  # SECURITY SCENARIOS
  # ============================================

  Scenario: Student cannot enroll other students
    Given a student with id 1 exists
    And a course with id 101 exists
    When student 1 tries to enroll student 2 in course 101
    Then the system should validate student authorization
    And the request should be rejected if unauthorized

  Scenario: Enrollment requests are validated
    Given any enrollment request
    When the request is processed
    Then the system should validate all required fields
    And the system should check course availability
    And the system should verify student eligibility

  # ============================================
  # DATA INTEGRITY
  # ============================================
  Scenario: Cannot enroll in same course twice
    Given a student with id 9 exists
    And a course with id 109 exists
    And student 9 is already enrolled in course 109
    When attempting to enroll student 9 in course 109 again
    Then the system should prevent duplicate enrollment
    And return an appropriate error message