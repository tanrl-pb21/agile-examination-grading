Feature: Instructor views student list
  As an instructor
  I want to view all students in an exam
  So that I can see who submitted and who missed the exam

  Scenario: Instructor views student list
    Given the API is running
    And exam 1 exists
    When I fetch the student list for exam 1
    Then the list contains valid student entries

  Scenario: Student count matches submitted + missed
    Given the API is running
    And exam 1 exists
    When I fetch the student list for exam 1
    Then submitted count plus missed count equals total enrolled students

  Scenario: Missed students appear with no submission details
    Given the API is running
    And exam 1 exists
    When I fetch the student list for exam 1
    Then missed students have no submission date, time, or score
