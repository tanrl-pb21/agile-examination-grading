Feature: Exam Performance Reporting
  As an instructor
  I want to view overall student performance statistics for an exam
  So that I can understand how well students performed

  Background:
    Given the instructor with id 1 exists
    And the instructor has access to multiple courses

  # ============================================
  # VIEW COMPLETED EXAMS
  # ============================================

  Scenario: Instructor views list of completed exams
    Given the instructor with id 1 exists
    And there are completed exams for the instructor's courses
    When the instructor requests completed exams list
    Then the system should return status code 200
    And the response should contain list of completed exams
    And the list should contain exam with id 1
    And the exam list should include basic statistics

  Scenario: Instructor views empty completed exams list
    Given the instructor with id 2 exists
    And there are no completed exams for the instructor's courses
    When the instructor requests completed exams list
    Then the system should return status code 200
    And the response should be an empty list

  # ============================================
  # VIEW EXAM PERFORMANCE STATISTICS
  # ============================================

  Scenario: View comprehensive exam performance statistics
    Given exam with id 1 exists
    And exam 1 has student submissions and grades
    When the instructor requests performance statistics for exam 1
    Then the system should return status code 200
    And the response should contain exam information
    And the response should contain performance statistics
    And the statistics should include average score
    And the statistics should include pass rate
    And the response should contain grade distribution
    And the response should contain score ranges

  Scenario: View exam performance with no graded submissions
    Given exam with id 2 exists
    And exam 2 has no graded submissions
    When the instructor requests performance statistics for exam 2
    Then the system should return status code 200
    And the statistics should show 0 graded submissions
    And the pass rate should be 0

  Scenario: Try to view non-existent exam performance
    Given exam 999 does not exist
    When the instructor requests performance statistics for exam 999
    Then the system should return status code 404
    And the error should indicate exam not found

  Scenario: Instructor without access tries to view exam performance
    Given exam with id 1 exists
    And instructor with id 3 does not have access to exam 1's course
    When instructor 3 requests performance statistics for exam 1
    Then the system should return status code 404
    And the error should indicate no access

  # ============================================
  # VIEW STUDENT SCORES
  # ============================================

  Scenario: View individual student scores for an exam
    Given exam with id 1 exists
    And exam 1 has multiple student submissions
    When the instructor requests student scores for exam 1
    Then the system should return status code 200
    And the response should contain list of student scores
    And each student score should contain student information
    And each student score should contain score details

  Scenario: View student scores for exam with no submissions
    Given exam with id 3 exists
    And exam 3 has no student submissions
    When the instructor requests student scores for exam 3
    Then the system should return status code 404
    And the error should indicate no scores found

  # ============================================
  # VIEW INSTRUCTOR COURSES
  # ============================================

  Scenario: Instructor views their assigned courses
    Given instructor with id 1 exists
    And instructor 1 is assigned to multiple courses
    When instructor 1 requests their assigned courses
    Then the system should return status code 200
    And the response should contain list of courses
    And each course should include student and exam counts

  Scenario: Instructor with no assigned courses
    Given instructor with id 4 exists
    And instructor 4 is not assigned to any courses
    When instructor 4 requests their assigned courses
    Then the system should return status code 200
    And the response should be an empty list

  Scenario: Request courses without providing instructor ID
    When the system receives a request for courses without instructor ID
    Then the system should return status code 400
    And the error should indicate instructor ID is required

  # ============================================
  # ERROR HANDLING
  # ============================================

  Scenario: Invalid exam ID in performance request
    When the instructor requests performance statistics with exam ID 0
    Then the system should return status code 400
    And the error should indicate invalid exam ID

  Scenario: Invalid exam ID in student scores request
    When the instructor requests student scores with exam ID -1
    Then the system should return status code 400
    And the error should indicate invalid exam ID

  # ============================================
  # DATA VALIDATION
  # ============================================

  Scenario: Ensure statistics calculations are correct
    Given exam with id 5 exists
    And exam 5 has specific student scores for calculation testing
    When the instructor requests performance statistics for exam 5
    Then the system should return status code 200
    And the average score should be calculated correctly
    And the highest score should be identified correctly
    And the lowest score should be identified correctly
    And the pass rate should be calculated correctly
    And grade distribution should reflect actual grades

  # ============================================
  # COMPREHENSIVE FLOW
  # ============================================

  Scenario: Complete workflow for exam analysis
    Given instructor with id 1 exists
    When instructor 1 requests their assigned courses
    Then the system should return status code 200
    And the course list should contain course with id 101
    When instructor 1 requests completed exams
    Then the system should return status code 200
    And the exam list should contain exam with id 1
    When instructor 1 requests performance statistics for exam 1
    Then the system should return status code 200
    And the statistics should show graded submissions
    When instructor 1 requests student scores for exam 1
    Then the system should return status code 200
    And the student scores should match the statistics