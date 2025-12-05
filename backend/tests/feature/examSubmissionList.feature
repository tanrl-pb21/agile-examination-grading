Feature: Instructor views student list
  As an instructor
  I want to view all students in an exam
  So that I can see who submitted and who missed the exam

  # ----------------------------
  Scenario: Instructor views student list
    Given the API is running
    And exam 239 exists
    When I fetch the student list for exam 239
    Then the list contains valid student entries

  Scenario: Student count matches submitted + missed
    Given the API is running
    And exam 239 exists
    When I fetch the student list for exam 239
    Then submitted count plus missed count equals total enrolled students

  Scenario: Missed students appear with no submission details
    Given the API is running
    And exam 239 exists
    When I fetch the student list for exam 239
    Then missed students have no submission date, time, or score

  # ----------------------------
  Scenario: Total summary shows correct counts
    Given the API is running
    And exam 239 exists
    When I fetch the student list for exam 239
    Then the summary shows total students, submitted, and missed counts correctly

  Scenario: Students are marked as missed after exam end time
    Given the API is running
    And exam 239 exists
    And the current time is after the exam end time
    When I fetch the student list for exam 239
    Then all students who have not submitted are marked as "missed"

  Scenario: Counts update correctly when new submissions arrive
    Given the API is running
    And exam 239 exists
    And 1 student has submitted
    When another student submits the exam
    And I fetch the student list for exam 239
    Then submitted count increases and missed count decreases

  Scenario: Submissions display correct score and submission date/time
    Given the API is running
    And exam 239 exists
    When I fetch the student list for exam 239
    Then submitted students show correct score, submission date, and submission time

  Scenario: Exam does not exist
    Given the API is running
    And no exam exists with ID 999
    When I fetch the student list for exam 999
    Then I receive the error "Exam not found"