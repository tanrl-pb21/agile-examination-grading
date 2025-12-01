Feature: Student Overall Result API
  The student can retrieve all submissions with correct score,
  percentage, status normalization, and formatting.


  Scenario: Student retrieves overall results with graded and ungraded submissions
    Given the service returns two submissions for user 1
    When the student requests their overall result
    Then the API should return 2 results
    And result 1 should have status "graded"
    And result 1 should have score "45/50"
    And result 1 should have percentage "90.0%"
  


  Scenario: Student has no submissions
    Given the service returns an empty result list for user 1
    When the student requests their overall result
    Then the API should return an empty list


  Scenario: ValueError from service → API returns 404
    Given the service raises ValueError("No submissions found") for user 999
    When the student requests their overall result for user 999
    Then the response status code should be 404
    And the response detail should be "No submissions found"


  Scenario: Pending submission is returned without score or percentage
    Given the service returns a pending submission for user 2
    When the student requests their overall result for user 2
    Then the API should return 1 result
    And the result should have status "pending"
    And the result should have no score and no percentage
