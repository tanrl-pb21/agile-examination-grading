Feature: Exam Listing for Students
  As a student
  I want to view exams that are available to take now
  And exams that are coming up for my enrolled courses

  Background:
    Given the API is running
    And I am student 1

  # ============================================================================
  # AVAILABLE EXAMS TESTS
  # ============================================================================

  Scenario: Get list of available exams
    When I request my available exams
    Then I receive status code 200
    And the response is a list of exams
    And each exam has the required fields

  Scenario: Available exams are currently within time window
    When I request my available exams
    Then I receive status code 200
    And the response is a list of exams
    And each available exam is currently open

  Scenario: Available exams are from my enrolled courses
    When I request my available exams
    Then I receive status code 200
    And all exams belong to my enrolled courses

  # ============================================================================
  # UPCOMING EXAMS TESTS
  # ============================================================================

  Scenario: Get list of upcoming exams
    When I request my upcoming exams
    Then I receive status code 200
    And the response is a list of exams
    And each exam has the required fields

  Scenario: Upcoming exams are scheduled for the future
    When I request my upcoming exams
    Then I receive status code 200
    And the response is a list of exams
    And each upcoming exam is scheduled for the future

  Scenario: Upcoming exams are from my enrolled courses
    When I request my upcoming exams
    Then I receive status code 200
    And all exams belong to my enrolled courses

  # ============================================================================
  # EDGE CASES
  # ============================================================================

  Scenario: Available exams list can be empty
    When I request my available exams
    Then I receive status code 200
    And the response is a list of exams

  Scenario: Upcoming exams list can be empty
    When I request my upcoming exams
    Then I receive status code 200
    And the response is a list of exams