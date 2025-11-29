Feature: MCQ submission recording

  Scenario: Student submits MCQ answers for recording and grading
    Given the exam code "MATH-1" is available
    When I submit a multiple-choice answer for that exam as user 7
    Then the submission is recorded with MCQ grading info

  Scenario: Submission payload echoes all answers
    Given the exam code "MATH-1" is available
    When I submit multiple answers for that exam as user 8
    Then all answers are echoed back in the submission response