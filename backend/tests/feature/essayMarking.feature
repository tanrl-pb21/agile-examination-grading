Feature: Instructor marks essay answers
  As an instructor
  I want to enter marks for each essay answer
  So that I can grade subjective responses

  Background:
    Given the grading API is running

  # ============================================================
  # TOP 10 CRITICAL SCENARIOS
  # ============================================================

  Scenario: Instructor submits marks for a single essay answer
    Given a submission with ID 100 has an essay answer
    When I submit a grade of 8.5 with feedback "Excellent analysis"
    Then the mark is saved successfully
    And the submission status is updated to "graded"

  Scenario: Instructor grades multiple essay questions in one submission
    Given a submission with ID 200 has 3 essay answers
    When I submit grades for all 3 essays with total score 21.5
    Then all marks are saved successfully
    And the total score is 21.5

  Scenario: Instructor gives partial marks for incomplete essay
    Given a submission with ID 300 has an essay answer worth 10 marks
    When I submit a grade of 6.5 with feedback "Good start but missing key points"
    Then the mark is saved successfully
    And the partial credit is recorded

  Scenario: Instructor re-grades a previously graded essay
    Given a submission with ID 400 has already been graded with score 7.0
    When I update the grade to 8.0 with feedback "Improved grade after review"
    Then the mark is updated successfully

  Scenario: Instructor retrieves ungraded submission for grading
    Given a submission with ID 500 exists with status "submitted"
    And it contains 2 essay questions
    When I request the submission for grading
    Then I receive the submission details
    And all essay questions are included
    And the student's essay answers are shown

  Scenario: Instructor grades exam with MCQ and essay questions
    Given a submission with ID 600 has 2 MCQ and 2 essay questions
    And the MCQ questions are auto-graded with score 10
    When I submit grades for the 2 essays with total score 25
    Then the total score combines MCQ and essay marks

  Scenario: Instructor submits grade without feedback
    Given a submission with ID 700 has an essay answer
    When I submit a grade of 7.5 without feedback
    Then the mark is saved successfully
    And the feedback is null

  Scenario: Cannot grade non-existent submission
    Given submission with ID 99999 does not exist
    When I attempt to submit grades
    Then I receive an error "Submission not found"
    And the response status is 404

  Scenario: Cannot submit overly long overall feedback
    Given a submission with ID 800 has an essay answer
    When I submit overall feedback exceeding 5000 characters
    Then I receive an error "exceeds maximum length"
    And the response status is 400

  Scenario: Instructor retrieves already graded submission for review
    Given a submission with ID 900 was fully graded with overall feedback
    When I request the submission for grading
    Then I see all existing grades
    And the overall feedback is displayed

