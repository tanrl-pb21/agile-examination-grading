Feature: Late submission prevention
  As a system
  I must block late submissions
  So that students cannot submit after the exam time ends

  Scenario: Late student appears as missed
    Given the API is running
    And exam 1 exists
    When I fetch the student list for exam 1
    Then missed students have no submission fields

  Scenario: Submitted students are not marked missed
    Given the API is running
    And exam 1 exists
    When I fetch the student list for exam 1
    Then submitted students have submission fields

  Scenario: Student count is consistent
    Given the API is running
    And exam 1 exists
    When I fetch the student list for exam 1
    Then submitted + missed equals total students

  Scenario: Invalid exam returns error
    Given the API is running
    When I fetch the student list for exam 999999
    Then I receive the error "Exam not found"
