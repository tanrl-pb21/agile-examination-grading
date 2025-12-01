Feature: Late submission prevention and grading
  As a system
  I must manage exam submissions and prevent late entries
  So that students are graded fairly and on time

  Background:
    Given the API is running
    And the exam database is empty

  # ==================== HAPPY PATH SCENARIOS ====================

  Scenario: Submit exactly at the exam end time
    When I submit an exam exactly at the end time for exam code "EXAM_OK"
    Then I receive status code 200
    And the response contains "submission_id"
    And the grade is "A+"

  Scenario: Submit just before the exam ends
    When I submit an exam 1 minute before the end time for exam code "EXAM_OK"
    Then I receive status code 200
    And the response contains "submission_id"
    And the grade is "A+"

  Scenario: Multiple students submit on time
    Given students "Alice", "Bob", and "Charlie" exist
    When each student submits the exam "EXAM_OK" on time
    Then all submissions receive status code 200
    And each response contains "submission_id"

  # ==================== LATE SUBMISSION SCENARIOS ====================

  Scenario: Submit 1 minute after the exam ended
    When I submit an exam 1 minute after the end time for exam code "EXAM_LATE"
    Then I receive status code 400
    And the error message contains "late"

  Scenario: Submit 5 minutes after the exam ended with no answers
    When I submit an empty exam 5 minutes late for exam code "EXAM_LATE_EMPTY"
    Then I receive status code 400
    And the error message contains "late"

  Scenario: Attempt to resubmit after exam ended
    When I try to submit again after the exam ended for exam code "EXAM_RESUBMIT"
    Then I receive status code 400
    And the error message contains "already submitted"

  # ==================== EDGE CASES ====================

  Scenario: Submit partial answers just before the end
    When I submit an exam with only partial answers 2 minutes before the end time for exam code "EXAM_OK"
    Then I receive status code 200
    And the response contains "submission_id"
    And the grade is "F"

  Scenario: Submit with invalid exam code
    When I submit an exam with invalid exam code "EXAM_INVALID"
    Then I receive status code 400
    And the error message contains "not found"

  Scenario: Submit an exam and then resubmit before exam ends
    When I submit an exam and then resubmit 5 minutes before the end time for exam code "EXAM_OK"
    Then both submissions receive status code 200
    And each response contains "submission_id"

  Scenario: Late resubmission after grading
    Given the exam "EXAM_OK" has been graded
    When I attempt to resubmit after grading for exam code "EXAM_OK"
    Then I receive status code 400
    And the error message contains "cannot resubmit after grading"
