Feature: Search Student Submissions
  As a student
  I want to search my submissions by submission ID or exam title
  So that I can quickly find specific submissions

  Background:
    Given the submission service is available
    And user 1 has submission with id 1 for exam "Python Basics"
    And user 1 has submission with id 2 for exam "Data Structures"
    And user 1 has submission with id 3 for exam "Algorithms Final"
    And user 1 has submission with id 4 for exam "Machine Learning"
    And user 1 has submission with id 5 for exam "Python Advanced"

  Scenario: Search submission by exact submission ID
    Given user 1 has submissions
    When I search for submission ID "sub1"
    Then I should receive 1 submission
    And the submission should have id 1
    And the submission should have exam title "Python Basics"

  Scenario: Search submission by submission ID case insensitive
    Given user 1 has submissions
    When I search for submission ID "SUB2"
    Then I should receive 1 submission
    And the submission should have id 2
    And the submission should have exam title "Data Structures"

  Scenario: Search submission by partial submission ID
    Given user 1 has submissions
    When I search for submission ID "sub"
    Then I should receive 5 submissions
    And all submissions should have submission IDs starting with "sub"

  Scenario: Search submission by exact exam title
    Given user 1 has submissions
    When I search for exam title "Machine Learning"
    Then I should receive 1 submission
    And the submission should have exam title "Machine Learning"

  Scenario: Search submission by partial exam title
    Given user 1 has submissions
    When I search for exam title "Python"
    Then I should receive 2 submissions
    And one submission should have exam title "Python Basics"
    And one submission should have exam title "Python Advanced"

  Scenario: Search submission by exam title case insensitive
    Given user 1 has submissions
    When I search for exam title "algorithms final"
    Then I should receive 1 submission
    And the submission should have exam title "Algorithms Final"

  Scenario: Search with no matching submission ID
    Given user 1 has submissions
    When I search for submission ID "sub999"
    Then I should receive 0 submissions

  Scenario: Search with no matching exam title
    Given user 1 has submissions
    When I search for exam title "Nonexistent Exam"
    Then I should receive 0 submissions

  Scenario: Search returns submissions with all required fields
    Given user 1 has submissions
    When I search for exam title "Python Basics"
    Then I should receive 1 submission
    And the submission should have submission_id field
    And the submission should have exam_title field
    And the submission should have exam_id field
    And the submission should have date field
    And the submission should have status field

  Scenario: Search for user with no submissions
    Given user 999 has no submissions
    When I search for submission ID "sub1"
    Then I should receive 0 submissions

  Scenario: Get all submissions without search filter
    Given user 1 has submissions
    When I get all submissions without search
    Then I should receive 5 submissions
    And submissions should be ordered by date descending