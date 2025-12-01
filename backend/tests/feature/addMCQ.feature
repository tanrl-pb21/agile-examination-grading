Feature: Add MCQ
  As an instructor, 
  I want to add multiple choice question by specifying the question text, options, correct answer and the mark allocated for each multiple choice question to an exam through the exam id 
  so that I can prepare the exam content

  # -------------------
  # SUCCESS SCENARIOS
  # -------------------

  Scenario: Successfully add an MCQ
    Given exam 1 exists
    When the instructor adds an MCQ with text "What is 2+2?", marks 5, options "3,4", correct index 1
    Then the system returns status code 201
    And the MCQ has correct option at index 1

  Scenario: Update MCQ
    Given exam 1 exists
    When the instructor updates the MCQ 100 with text "Updated question?", marks 10, options "Yes,No", correct index 0
    Then the system returns status code 200
    And the MCQ has correct option at index 0

  Scenario: Delete MCQ
    Given exam 1 exists
    When the instructor deletes the MCQ with ID 100
    Then the system returns status code 200

  # -------------------
  # VALIDATION ERRORS (Pydantic)
  # -------------------

  Scenario: Empty question text
    Given exam 1 exists
    When the instructor adds an MCQ with text "  ", marks 5, options "A,B", correct index 0
    Then the system returns status code 422
    And the response contains error "value_error, question text cannot be empty"

  Scenario: Less than 2 options
    Given exam 1 exists
    When the instructor adds an MCQ with text "Test?", marks 5, options "OnlyOne", correct index 0
    Then the system returns status code 422
    And the response contains error "value_error, at least 2 options required"

  Scenario: Duplicate options
    Given exam 1 exists
    When the instructor adds an MCQ with text "Is water wet?", marks 5, options "Yes,Yes", correct index 0
    Then the system returns status code 422
    And the response contains error "value_error, duplicate options not allowed"

  Scenario: Invalid correct option index
    Given exam 1 exists
    When the instructor adds an MCQ with text "Test?", marks 5, options "A,B", correct index 5
    Then the system returns status code 422
    And the response contains error "value_error, correct option index out of range"

  # -------------------
  # BUSINESS LOGIC ERRORS
  # -------------------

  Scenario: Adding question to invalid exam fails
    Given no exam exists with ID 99999
    When the instructor adds an MCQ with text "Sample?", marks 5, options "A,B", correct index 0
    Then the system returns status code 400
    And the response contains error "Exam not found"

  Scenario: Adding duplicate question fails
    Given exam 1 exists
    And exam 1 already has a question "What is 2 + 2?"
    When the instructor adds an MCQ with text "What is 2 + 2?", marks 5, options "3,4", correct index 1
    Then the system returns status code 400
    And the response contains error "Question already exists"


