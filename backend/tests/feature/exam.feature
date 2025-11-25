Feature: Exam Management
  Scenario: Add an exam
    Given the API is running
    When I send a POST request to create an exam
    Then it should return 201 Created
