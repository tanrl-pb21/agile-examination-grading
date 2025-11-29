Feature: Exam timer and availability

  Scenario: Timer countdown is returned for an active exam
    Given the exam code "MATH-1" is available
    When I request the remaining time for that exam
    Then I receive a remaining seconds value for that exam

  Scenario: Questions can be retrieved for an active exam
    Given the exam code "MATH-1" is available
    When I request the questions for that exam
    Then I receive both MCQ and essay questions