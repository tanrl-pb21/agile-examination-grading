Feature: Overall Feedback on Exam Submissions
  As a teacher
  I want to provide overall feedback on student exam submissions
  So that students can understand their overall performance and receive guidance

  Background:
    Given the API is running
    And the grading database is empty

  # ============================================================================
  # HAPPY PATH: SUCCESSFUL FEEDBACK SAVE
  # ============================================================================

  Scenario: Save valid overall feedback successfully
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 85 grade "B" and feedback "Great work on this exam!"
    Then I receive status code 200
    And the response indicates success is true
    When I retrieve feedback for submission 21
    Then the overall_feedback is "Great work on this exam!"

  Scenario: Save feedback with special characters and emojis
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 90 grade "A" and feedback "Great job! 😊👍 Keep it up! 💯"
    Then I receive status code 200
    And the response indicates success is true
    When I retrieve feedback for submission 21
    Then the overall_feedback contains "Great job"
    And the overall_feedback contains "💯"

  Scenario: Save feedback with multiline content
    Given a submission with ID 21 exists
    When I save multiline feedback for submission 21 with score 78 grade "C" and feedback "Excellent analysis!\nWork on clarity"
    Then I receive status code 200
    And the response indicates success is true
    When I retrieve feedback for submission 21
    Then the overall_feedback contains newlines

  Scenario: Save feedback with essay grades included
    Given a submission with ID 21 exists
    When I save feedback with essay grades for submission 21 with score 75 grade "C"
    Then I receive status code 200
    And the response indicates success is true

  # ============================================================================
  # EDGE CASES: EMPTY AND OPTIONAL FEEDBACK
  # ============================================================================

  Scenario: Save empty overall feedback
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 0 grade "F" and feedback ""
    Then I receive status code 200
    And the response indicates success is true
    When I retrieve feedback for submission 21
    Then the overall_feedback is empty or null

  Scenario: Save feedback without overall_feedback field
    Given a submission with ID 21 exists
    When I save feedback without feedback field for submission 21 with score 50 grade "D"
    Then I receive status code 200
    And the response indicates success is true

  Scenario: Save feedback with whitespace-only feedback
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 60 grade "D" and feedback "   "
    Then I receive status code 200

  # ============================================================================
  # VALIDATION FAILURES: FEEDBACK LENGTH
  # ============================================================================

  Scenario: Save feedback exceeding maximum length
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 0 grade "F" and very long feedback of 6000 characters
    Then I receive status code 400
    And the error message contains "exceeds maximum length"

  Scenario: Save feedback at maximum allowed length
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 85 grade "B" and feedback of 5000 characters
    Then I receive status code 200
    And the response indicates success is true

  Scenario: Save feedback just under maximum length
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 85 grade "B" and feedback of 4999 characters
    Then I receive status code 200

  # ============================================================================
  # VALIDATION FAILURES: MISSING REQUIRED FIELDS
  # ============================================================================

  Scenario: Save feedback without submission_id
    When I save feedback without submission_id with score 85 grade "B"
    Then I receive status code 422
    And the error message contains "submission_id"

  Scenario: Save feedback with missing essay_grades array
    Given a submission with ID 21 exists
    When I save feedback without essay_grades for submission 21 with score 85 grade "B"
    Then I receive status code 422
    And the error message contains "essay_grades"

  Scenario: Save feedback with missing total_score
    Given a submission with ID 21 exists
    When I save feedback without total_score for submission 21 grade "B"
    Then I receive status code 422
    And the error message contains "total_score"

  # ============================================================================
  # VALIDATION FAILURES: ESSAY GRADES FORMAT
  # ============================================================================

  Scenario: Save feedback with missing submission_answer_id in essay grades
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with invalid essay grades missing submission_answer_id
    Then I receive status code 422
    And the error message contains "submission_answer_id"

  Scenario: Save feedback with missing score in essay grades
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with invalid essay grades missing score
    Then I receive status code 422
    And the error message contains "score"

  # ============================================================================
  # BUSINESS LOGIC: NON-EXISTENT RESOURCES
  # ============================================================================

  Scenario: Save feedback for non-existent submission
    When I save feedback for submission 9999999 with score 85 grade "B" and feedback "Feedback for fake submit"
    Then I receive status code 404
    And the error message is "Submission not found"

  # ============================================================================
  # RETRIEVE FEEDBACK: SUCCESSFUL RETRIEVAL
  # ============================================================================

  Scenario: Retrieve feedback for existing submission
    Given a submission with ID 21 exists
    And I have saved feedback "Excellent work" for submission 21
    When I retrieve feedback for submission 21
    Then I receive status code 200
    And the response contains "submission"
    And the overall_feedback is "Excellent work"

  Scenario: Retrieve feedback with special characters preserved
    Given a submission with ID 21 exists
    And I have saved feedback "Perfect! 🎉\nWell done 👏" for submission 21
    When I retrieve feedback for submission 21
    Then I receive status code 200
    And the overall_feedback contains "🎉"
    And the overall_feedback contains "👏"

  # ============================================================================
  # RETRIEVE FEEDBACK: NOT FOUND ERRORS
  # ============================================================================

  Scenario: Retrieve feedback for non-existent submission
    When I retrieve feedback for submission 9999999
    Then I receive status code 404
    And the error message contains "not found"

  # ============================================================================
  # DATA INTEGRITY
  # ============================================================================

  Scenario: Feedback persists after save
    Given a submission with ID 21 exists
    When I save feedback for submission 21 with score 92 grade "A" and feedback "Persistent text"
    And I retrieve feedback for submission 21
    Then the overall_feedback is "Persistent text"
    And the score_grade is "A"

  Scenario: Update feedback overwrites previous feedback
    Given a submission with ID 21 exists
    And I have saved feedback "First feedback" for submission 21
    When I save feedback for submission 21 with score 88 grade "B" and feedback "Updated feedback"
    And I retrieve feedback for submission 21
    Then the overall_feedback is "Updated feedback"
    And the score_grade is "B"