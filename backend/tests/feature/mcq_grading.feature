# tests/feature/mcq_grading.feature

Feature: Automatic MCQ Grading
  As a student
  I want my MCQ answers to be automatically graded
  So that I can get immediate feedback on my objective answers

  Background:
    Given a student is taking an MCQ exam

  Scenario: Student selects correct answer
    Given an MCQ question worth 5 marks
    And the correct answer is option 2
    When the student selects option 2
    And the exam is submitted
    Then the student should receive 5 marks
    And the feedback should be "Correct"
    And the answer should be marked as correct

  Scenario: Student selects incorrect answer
    Given an MCQ question worth 5 marks
    And the correct answer is option 2
    When the student selects option 3
    And the exam is submitted
    Then the student should receive 0 marks
    And the feedback should be "Incorrect"
    And the answer should be marked as incorrect

  Scenario: Multiple questions with different marks
    Given an MCQ question worth 10 marks
    And the correct answer is option 1
    When the student selects option 1
    And the exam is submitted
    Then the student should receive 10 marks
    And the feedback should be "Correct"

  Scenario: Zero marks for wrong answer regardless of question value
    Given an MCQ question worth 15 marks
    And the correct answer is option 4
    When the student selects option 1
    And the exam is submitted
    Then the student should receive 0 marks
    And the feedback should be "Incorrect"