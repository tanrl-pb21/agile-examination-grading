Feature: Add Multiple Choice Question
  As an instructor
  I want to add multiple choice questions to an exam
  So that I can prepare the exam content

  Scenario: Successfully add an MCQ
    Given the API is running
    And an exam with ID 1 exists
    When I submit an MCQ with text "What is 2+2?" and marks 5 and valid options
    Then the MCQ is stored under exam 1

  Scenario: Adding question to invalid exam fails
    Given the API is running
    And no exam exists with ID 99999
    When I submit an MCQ to exam 99999
    Then I receive the error "exam not found"

  Scenario: Must have at least two options
    Given the API is running
    And an exam with ID 1 exists
    When I submit an MCQ with only one option
    Then the system rejects the MCQ

  Scenario: Correct answer must match one of the provided options
    Given the API is running
    And an exam with ID 1 exists
    When I submit an MCQ with an invalid correct option index
    Then a validation error occurs
