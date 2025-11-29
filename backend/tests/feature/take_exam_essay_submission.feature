Feature: Essay submission

  Scenario: Student submits essay answers for recording
    Given the exam code "MATH-1" is available
    When I submit an essay answer for that exam as user 7
    Then the submission is accepted and stored

  Scenario: Duplicate submission is detected
    Given the exam code "MATH-1" is available
    When I submit an essay answer for that exam as user 7
    And I check if user 7 already submitted
    Then the API reports the submission exists