Feature: Update Essay Question
  As an exam administrator
  I want to update essay questions
  So that I can maintain accurate exam content

  Background:
    Given the question service is available
    And an essay question with id 1 exists in exam 100
    And the question has text "Original Question?"
    And the question has 10 marks
    And the question has rubric "Original rubric"

  Scenario: Successfully update an essay question
    Given an essay question with id 1 exists
    When I update the essay question 1 with text "What is machine learning?"
    And I set the marks to 15
    And I set the rubric to "Updated rubric text"
    And I set the reference answer to "Sample answer text"
    Then the essay question should be updated successfully
    And the response should have id 1
    And the response should have question text "What is machine learning?"
    And the response should have marks 15
    And the response should have rubric "Updated rubric text"

  Scenario: Update essay question with minimal data
    Given an essay question with id 1 exists
    When I update the essay question 1 with text "Explain neural networks"
    And I set the marks to 20
    Then the essay question should be updated successfully
    And the response should have marks 20
    And the response should have question text "Explain neural networks"

  Scenario: Update essay question with whitespace trimming
    Given an essay question with id 1 exists
    When I update the essay question 1 with text "  What is AI?  "
    And I set the marks to 10
    Then the essay question should be updated successfully
    And the response should have question text "What is AI?"

  Scenario: Fail to update with empty question text
    Given an essay question with id 1 exists
    When I attempt to update the essay question 1 with empty question text
    Then the update should fail with status code 422
    And the error message should contain "Question text cannot be empty"

  Scenario: Fail to update with whitespace only question text
    Given an essay question with id 1 exists
    When I attempt to update the essay question 1 with text "   "
    Then the update should fail with status code 422
    And the error message should contain "Question text cannot be empty"

  Scenario: Fail to update non-existent question
    Given no essay question with id 999 exists
    When I attempt to update essay question 999 with text "Some question"
    Then the update should fail with status code 400
    And the error message should contain "not found"

  Scenario: Fail to update with duplicate question text in same exam
    Given an essay question with id 1 exists in exam 100
    And another essay question with id 2 exists in exam 100
    And question 2 has text "What is Python?"
    When I attempt to update question 1 with text "What is Python?"
    Then the update should fail with status code 400
    And the error message should contain "already exists"

  Scenario: Successfully update with duplicate text from different exam
    Given an essay question with id 1 exists in exam 100
    And another essay question with id 3 exists in exam 200
    And question 3 has text "What is Java?"
    When I update the essay question 1 with text "What is Java?"
    And I set the marks to 10
    Then the essay question should be updated successfully
    And the response should have question text "What is Java?"