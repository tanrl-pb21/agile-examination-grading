Feature: Student Review Submission Answers
  As a student
  I want to review my submission answers
  So that I can see correct and incorrect responses and learn from my mistakes

  Background:
    Given the API is running

  # ============================================================
  # POSITIVE SCENARIOS - Successful Review
  # ============================================================

  Scenario: Successfully review a graded submission with mixed results
    Given a graded submission with ID 22 exists for user 2
    And the submission has 2 questions with 1 correct and 1 incorrect
    When I request a review for submission 22 as user 2
    Then the review contains question details and correctness
    And I can see which answers are correct
    And I can see which answers are incorrect
    And each question shows the earned marks
    And the correct answer is displayed for MCQ questions

  Scenario: Review graded submission with perfect score
    Given a graded submission with ID 100 exists for user 5
    And the submission has all correct answers
    When I request a review for submission 100 as user 5
    Then the review contains question details and correctness
    And all questions are marked as correct
    And the total score matches the maximum possible marks
    And the percentage is 100%

  Scenario: Review graded submission with zero score
    Given a graded submission with ID 250 exists for user 12
    And the submission has all incorrect answers
    When I request a review for submission 250 as user 12
    Then the review contains question details and correctness
    And all questions are marked as incorrect
    And correct answers are shown for each MCQ question
    And the total score is 0
    And the percentage is 0%

  Scenario: Review submission with essay questions and feedback
    Given a graded submission with ID 150 exists for user 8
    And the submission contains essay questions with feedback
    When I request a review for submission 150 as user 8
    Then the review contains question details and correctness
    And essay answers are displayed
    And detailed feedback is shown for each essay
    And partial marks are visible for essay questions

  Scenario: Review submission with mixed question types
    Given a graded submission with ID 200 exists for user 10
    And the submission has both MCQ and essay questions
    When I request a review for submission 200 as user 10
    Then the review contains question details and correctness
    And MCQ questions show selected answer and correct answer
    And essay questions show the submitted text and feedback
    And each question type displays appropriate information

  # ============================================================
  # EDGE CASES - Partial/Incomplete Submissions
  # ============================================================

  Scenario: Review submission with unanswered MCQ questions
    Given a graded submission with ID 450 exists for user 22
    And some MCQ questions were not answered
    When I request a review for submission 450 as user 22
    Then the review contains question details and correctness
    And unanswered questions show no selected answer
    And unanswered questions are marked as incorrect
    And unanswered questions have 0 earned marks
    And correct answers are still displayed

  Scenario: Review submission with unanswered essay questions
    Given a graded submission with ID 500 exists for user 25
    And some essay questions were not answered
    When I request a review for submission 500 as user 25
    Then the review contains question details and correctness
    And unanswered essays show "No answer provided"
    And unanswered essays have 0 earned marks

  Scenario: Review submission with partial marks on essays
    Given a graded submission with ID 300 exists for user 15
    And essay questions received partial credit
    When I request a review for submission 300 as user 15
    Then the review contains question details and correctness
    And earned marks are less than total marks for some questions
    And feedback explains why points were deducted

  # ============================================================
  # DISPLAY & FORMATTING
  # ============================================================

  Scenario: Verify question numbering in review
    Given a graded submission with ID 350 exists for user 18
    And the submission has multiple questions
    When I request a review for submission 350 as user 18
    Then the review contains question details and correctness
    And questions are numbered sequentially starting from 1
    And question numbers match the exam structure

  Scenario: Verify MCQ option labels
    Given a graded submission with ID 400 exists for user 20
    And the submission has MCQ questions
    When I request a review for submission 400 as user 20
    Then the review contains question details and correctness
    And MCQ options are labeled A, B, C, D
    And selected answer uses letter labels
    And correct answer uses letter labels

  Scenario: Verify score and percentage display
    Given a graded submission with ID 600 exists for user 30
    And the submission score is 13 out of 20
    When I request a review for submission 600 as user 30
    Then the review contains question details and correctness
    And score is displayed as "13/20"
    And percentage is displayed as "65.0%"

  Scenario: Review submission without feedback
    Given a graded submission with ID 300 exists for user 15
    And no feedback was provided by the grader
    When I request a review for submission 300 as user 15
    Then the review contains question details and correctness
    And questions display with null or empty feedback fields
    And the review still shows scores and correctness

  # ============================================================
  # NEGATIVE SCENARIOS - Access Control
  # ============================================================

  Scenario: Cannot review if submission is pending grading
    Given an ungraded submission with ID 37 exists for user 1
    And the submission status is "pending"
    When I request a review for submission 37 as user 1
    Then I receive the error "not graded"
    And the response status is 404

  Scenario: Cannot review if submission is submitted but not graded
    Given an ungraded submission with ID 850 exists for user 42
    And the submission status is "submitted"
    When I request a review for submission 850 as user 42
    Then I receive the error "not graded"
    And the response status is 404

  Scenario: Cannot review another student's submission
    Given a graded submission with ID 22 exists for user 2
    When I request a review for submission 22 as user 1
    Then I receive the error "not found"
    And the response status is 404

  Scenario: Cannot review with invalid user ID
    Given a graded submission with ID 22 exists for user 2
    When I request a review for submission 22 as user 999
    Then I receive the error "not found"
    And the response status is 404

  Scenario: Submission does not exist
    Given submission 9999 does not exist
    When I request a review for submission 9999 as user 1
    Then I receive the error "not found"
    And the response status is 404

  # ============================================================
  # COMPLEX SCENARIOS
  # ============================================================

  Scenario: Review large exam with many questions
    Given a graded submission with ID 900 exists for user 45
    And the submission has 10 or more questions
    When I request a review for submission 900 as user 45
    Then the review contains question details and correctness
    And all questions are included in the response
    And performance remains acceptable

  Scenario: Review submission with all question types
    Given a graded submission with ID 700 exists for user 35
    And the submission includes MCQ and essay questions
    And some answers are correct and some are incorrect
    And some questions were not answered
    When I request a review for submission 700 as user 35
    Then the review contains question details and correctness
    And each question displays appropriate format
    And overall feedback is included
    And summary statistics are correct

  # ============================================================
  # DATA INTEGRITY
  # ============================================================

  Scenario: Verify earned marks never exceed question marks
    Given a graded submission with ID 150 exists for user 8
    When I request a review for submission 150 as user 8
    Then the review contains question details and correctness
    And no question's earned marks exceed its total marks
    And the total score does not exceed total possible marks

  Scenario: Verify correct answer is always shown for MCQ
    Given a graded submission with ID 100 exists for user 5
    And the submission has MCQ questions
    When I request a review for submission 100 as user 5
    Then the review contains question details and correctness
    And each MCQ shows which option is correct
    And the correct option is marked with isCorrect flag

  Scenario: Verify submission ID format in response
    Given a graded submission with ID 22 exists for user 2
    When I request a review for submission 22 as user 2
    Then the review contains question details and correctness
    And submission ID is formatted as "sub22"

