Feature: MCQ autograding

  Scenario: Correct MCQ answers are graded automatically
    Given the exam code "MATH-1" is available
    When I submit the correct MCQ answer for that exam as user 7
    Then the MCQ answer is auto-graded as correct

  Scenario: Incorrect MCQ answers receive zero auto-score
    Given the exam code "MATH-1" is available
    When I submit a wrong MCQ answer for that exam as user 7
    Then the MCQ answer is auto-graded as incorrect