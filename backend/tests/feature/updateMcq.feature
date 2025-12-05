Feature: Update MCQ Question
  As an instructor
  I want to update MCQ questions
  So that I can maintain accurate exam content

  Background:
    Given the question service is available
    And an MCQ question with id 1 exists in exam 100
    And the question has text "Original MCQ Question?"
    And the question has 5 marks
    And the question has options ["Option A", "Option B", "Option C", "Option D"]
    And the correct answer is option 0 (Option A)

  Scenario: Fail to update with empty question text
    When I attempt to update MCQ question 1 with empty question text
    Then the update should fail with status code 422
    And the error message should contain "Question text cannot be empty"

  Scenario: Fail to update with whitespace only question text
    When I attempt to update MCQ question 1 with text "   "
    Then the update should fail with status code 422
    And the error message should contain "Question text cannot be empty"

  Scenario: Fail to update with invalid marks
    When I attempt to update MCQ question 1 with text "Valid question" and marks 0
    Then the update should fail with status code 422
    And the error message should contain "Marks must be at least 1"

  Scenario: Fail to update with insufficient options
    When I attempt to update MCQ question 1 with only 1 option
    Then the update should fail with status code 422
    And the error message should contain "At least 2 options are required"

  Scenario: Fail to update with empty option
    When I attempt to update MCQ question 1 with an empty option
    Then the update should fail with status code 422
    And the error message should contain "Option cannot be empty"

  Scenario: Fail to update with duplicate options
    When I attempt to update MCQ question 1 with duplicate options
    Then the update should fail with status code 422
    And the error message should contain "cannot contain duplicate values"

  Scenario: Fail to update with invalid correct answer index
    When I attempt to update MCQ question 1 with correct answer index 10
    Then the update should fail with status code 422
    And the error message should contain "must be between"

  Scenario: Fail to update non-existent question
    Given no MCQ question with id 999 exists
    When I attempt to update MCQ question 999 with text "Some question"
    Then the update should fail with status code 400
    And the error message should contain "not found"

  Scenario: Fail to update with duplicate question text in same exam
    Given another MCQ question with id 2 exists in exam 100
    And question 2 has text "What is Python?"
    When I attempt to update question 1 with text "What is Python?"
    Then the update should fail with status code 400
    And the error message should contain "already exists"
