Feature: Essay Answer Submission
  As a student
  I want to submit essay answers to exams
  So that my responses can be recorded and graded

  Background:
    Given the API is running
    And the exam database is empty

  # ============================================================================
  # HAPPY PATH: SUCCESSFUL SUBMISSIONS
  # ============================================================================

  Scenario: Submit a single essay answer successfully
    When I submit an essay answer for exam code "666" with question ID 7 and answer "This is my essay answer."
    Then I receive status code 200
    And the grade is "Pending"
    And the response contains "total_score"
    And the response contains "max_score"
    And the message contains "submitted"

  Scenario: Submit two essay answers successfully
    When I submit an essay answer for exam code "666" with question ID 7 and answer "Essay answer 1."
    And I submit an essay answer for exam code "666" with question ID 21 and answer "Essay answer 2."
    Then I receive status code 200
    And the grade is "Pending"
    And the response contains "total_score"
    And the response contains "max_score"
    And the message contains "submitted"

  # ============================================================================
  # EDGE CASES: VALID INPUTS
  # ============================================================================

  Scenario: Submit an empty essay answer
    When I submit an essay answer for exam code "666" with question ID 7 and answer ""
    Then I receive status code 200
    And the response is valid

  Scenario: Submit a very long essay answer
    When I submit a very long essay answer for exam code "666" with question ID 7
    Then I receive status code 200
    And the grade is "Pending"
    And the message contains "submitted"

  Scenario: Submit with no answers
    When I submit an exam with code "666" and user ID 1 but with no answers
    Then I receive status code 200
    And the response is valid

  # ============================================================================
  # VALIDATION FAILURES: MISSING FIELDS
  # ============================================================================

  Scenario: Submit with missing answer field
    When I submit an exam answer for exam code "666" with question ID 7 but without the answer field
    Then I receive status code 422
    And the response contains an error detail

  Scenario: Submit with missing question_id field
    When I submit an exam answer for exam code "666" with answer "Some answer" but without question_id field
    Then I receive status code 422
    And the response contains an error detail

  Scenario: Submit with missing exam_code
    When I submit an exam answer with user ID 1 but without exam_code
    Then I receive status code 422
    And the response contains an error detail

  Scenario: Submit with missing user_id
    When I submit an exam answer for exam code "666" but without user_id
    Then I receive status code 422
    And the response contains an error detail

  # ============================================================================
  # VALIDATION FAILURES: INVALID DATA TYPES
  # ============================================================================

  Scenario: Submit with invalid exam_code type
    When I submit an exam answer with exam_code of type number
    Then I receive status code 422
    And the response contains an error detail

  Scenario: Submit with invalid user_id type
    When I submit an exam answer with user_id of type string
    Then I receive status code 422
    And the response contains an error detail

  Scenario: Submit with invalid question_id type
    When I submit an exam answer with question_id of type string
    Then I receive status code 422
    And the response contains an error detail

  # ============================================================================
  # BUSINESS LOGIC VALIDATION
  # ============================================================================

  Scenario: Submit for non-existent exam
    When I submit an essay answer for exam code "NONEXISTENT" with question ID 7 and answer "Some answer"
    Then I receive status code 400
    And the error message contains "exam"

  Scenario: Submit for non-existent question
    When I submit an essay answer for exam code "666" with question ID 9999 and answer "Some answer"
    Then I receive status code 400 or 404
    And the response contains an error detail