Feature: View Student Score and Submission Details
  As a teacher
  I want to view student submissions with their scores and grades
  So that I can review and grade student work

  Background:
    Given the API is running
    And the grading database is populated

  # ============================================================================
  # HAPPY PATH: SUCCESSFUL RETRIEVAL
  # ============================================================================

  Scenario: Retrieve valid submission with complete details
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the response contains submission details
    And the response contains exam information
    And the response contains questions list
    And the submission has ID 21
    And the submission has student_name field
    And the submission has current_score field

  Scenario: Retrieve submission with all required fields
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the submission contains all required fields
    And the exam contains all required fields
    And the questions contain all required fields

  Scenario: Response has correct structure
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the response has exactly these keys: submission, exam, questions
    And submission is a dictionary
    And exam is a dictionary
    And questions is a list

  # ============================================================================
  # HAPPY PATH: SCORE VALIDATION
  # ============================================================================

  Scenario: Current score is within valid range
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the current_score is null or between 0 and 100

  Scenario: Score grade is present
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the score_grade is present

  Scenario: Overall feedback field exists
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the overall_feedback is null or a string
    And the overall_feedback length is less than 5000 characters

  # ============================================================================
  # HAPPY PATH: TIMESTAMP FORMAT
  # ============================================================================

  Scenario: Submitted timestamp is in valid format
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the submitted_at is a valid ISO format timestamp

  # ============================================================================
  # HAPPY PATH: PENDING SUBMISSIONS
  # ============================================================================

  Scenario: Pending submission shows ungraded status
    When I retrieve submission with ID 26
    Then I receive status code 200
    And the score_grade is null or "Pending"

  # ============================================================================
  # HAPPY PATH: QUESTIONS DATA
  # ============================================================================

  Scenario: Questions list has valid structure
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the questions list contains valid question objects
    And each question has id as integer
    And each question has question_text as string
    And each question has question_type in valid types
    And each question has marks as number
    And each question has student_answer field

  Scenario: Question types are valid
    When I retrieve submission with ID 21
    Then I receive status code 200
    And all question types are valid mcq or essay types

  # ============================================================================
  # ERROR HANDLING: NON-EXISTENT SUBMISSIONS
  # ============================================================================

  Scenario: Retrieve non-existent submission
    When I retrieve submission with ID 9999999
    Then I receive status code 404
    And the error message is "Submission not found"

  Scenario: Non-existent submission returns proper error structure
    When I retrieve submission with ID 9999999
    Then I receive status code 404
    And the response contains error detail

  # ============================================================================
  # ERROR HANDLING: INVALID INPUT
  # ============================================================================

  Scenario: Non-integer submission ID returns validation error
    When I retrieve submission with ID "abc"
    Then I receive status code 422
    And the error message contains "parsing"

  Scenario: Negative submission ID returns validation error or not found
    When I retrieve submission with ID -1
    Then I receive status code 404 or 422

  # ============================================================================
  # DATA INTEGRITY
  # ============================================================================

  Scenario: Student information is preserved
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the submission has student_id field
    And the submission has student_email field
    And the student_name is a non-empty string

  Scenario: Exam information is preserved
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the exam has title field
    And the exam has date field
    And the exam has start_time field
    And the exam has end_time field

  Scenario: Questions maintain original content
    When I retrieve submission with ID 21
    Then I receive status code 200
    And the questions list is not empty
    And each question has non-empty question_text
    And each question has marks greater than 0