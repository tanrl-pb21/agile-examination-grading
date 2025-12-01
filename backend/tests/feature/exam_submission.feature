# tests/feature/exam_submission.feature

Feature: Exam Submission
  As a student
  I want to submit my exam answers
  So that my work can be graded and recorded

  Background:
    Given a student is taking an exam

  Scenario: Submit exam with only MCQ questions
    Given the exam has 5 MCQ questions and 0 essay questions
    And the student has answered all questions
    And the current time is within the exam window
    When the student submits the exam
    Then the submission should be successful
    And a submission record should be created
    And the submission status should be "graded"
    And the MCQ questions should be automatically graded
    And the final grade should be calculated from MCQ scores
    And the total score should be 25 marks

  Scenario: Submit exam with MCQ and essay questions
    Given the exam has 3 MCQ questions and 2 essay questions
    And the student has answered all questions
    And the current time is within the exam window
    When the student submits the exam
    Then the submission should be successful
    And the submission status should be "pending"
    And the MCQ questions should be automatically graded
    And the essay questions should be marked "pending review"

  Scenario: Submit exam with only essay questions
    Given the exam has 0 MCQ questions and 3 essay questions
    And the student has answered all questions
    And the current time is within the exam window
    When the student submits the exam
    Then the submission should be successful
    And the submission status should be "pending"
    And the essay questions should be marked "pending review"

  Scenario: Reject late submission
    Given the exam has 5 MCQ questions and 0 essay questions
    And the student has answered all questions
    And the current time is after the exam has ended
    When the student attempts to submit the exam
    Then the submission should be rejected
    And the error message should indicate "late submission"

  Scenario: Prevent duplicate submission
    Given the exam has 5 MCQ questions and 0 essay questions
    And the student has already submitted this exam
    When the student tries to submit again
    Then the submission should be rejected
    And the error message should indicate "already submitted"