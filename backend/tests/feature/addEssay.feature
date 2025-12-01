Feature: Add Essay Question
  The system must allow instructors to add valid essay questions to an exam

  Scenario: Successfully add an essay question
    Given exam 1 exists
    When the instructor submits a new essay question "Explain gravity" with 10 marks
    Then the system should return 201
    And the response should contain "Explain gravity"

  Scenario: Reject empty essay question
    When the instructor submits an essay question with empty text
    Then the system should return 422

  Scenario: Reject adding question to a non-existing exam
    When the instructor submits an essay question to exam 999
    Then the system should return 400
    And the error should contain "not found"

  Scenario: Reject duplicate essay question
    Given exam 1 already has a question "What is AI?"
    When the instructor submits another essay question "What is AI?"
    Then the system should return 400
    And the error should contain "already exists"
