Feature: Student Review Submission Answers
  As a student
  I want to review my submission answers
  So that I can see correct and incorrect responses

  Scenario: Successfully review a graded submission
    Given the API is running
    And a graded submission with ID 22 exists for user 2
    When I request a review for submission 22 as user 2
    Then the review contains question details and correctness

  Scenario: Cannot review if not graded yet
    Given the API is running
    And an ungraded submission with ID 37 exists for user 1
    When I request a review for submission 37 as user 1
    Then I receive the error "not graded"

  Scenario: Cannot review another student's submission
    Given the API is running
    And a graded submission with ID 22 exists for user 2
    When I request a review for submission 22 as user 1
    Then I receive the error "not found"

  Scenario: Submission does not exist
    Given the API is running
    And submission 9999 does not exist
    When I request a review for submission 9999 as user 1
    Then I receive the error "not found"
