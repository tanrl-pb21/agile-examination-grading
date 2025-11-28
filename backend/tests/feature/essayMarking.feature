Feature: Instructor marks essay answers
  As an instructor
  I want to enter marks for each essay answer
  So that I can grade subjective responses

  Scenario: Instructor submits marks for an essay answer
    Given the grading API is running
    And a submission with an essay answer exists
    When I submit marks for the essay answer
    Then the mark is saved successfully
