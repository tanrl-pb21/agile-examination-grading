Feature: Delete Question
  As an exam administrator
  I want to delete questions from an exam
  So that I can remove incorrect or unwanted questions before the exam starts

  Background:
    Given the exam has not started
    And an MCQ question with id 1 exists in the system
    And an essay question with id 2 exists in the system
    And an MCQ question with id 3 exists in the system

  Scenario: Successfully delete an MCQ question
    Given I am an authenticated administrator
    And question with id 1 exists in the system
    When I request to delete question with id 1
    Then the question should be deleted successfully
    And the response status code should be 200
    And the response should contain message "Question deleted successfully"
    And the question with id 1 should no longer exist
    And all associated question options should be deleted

  Scenario: Successfully delete an essay question
    Given I am an authenticated administrator
    And question with id 2 exists in the system
    When I request to delete question with id 2
    Then the question should be deleted successfully
    And the response status code should be 200
    And the response should contain message "Question deleted successfully"
    And the question with id 2 should no longer exist

  Scenario: Attempt to delete a non-existent question
    Given I am an authenticated administrator
    And question with id 999 does not exist in the system
    When I request to delete question with id 999
    Then the deletion should fail
    And the response status code should be 404
    And the response should contain error "Question with id 999 not found"

  Scenario: Attempt to delete a question after exam has started
    Given the exam has already started
    And question with id 1 exists in the system
    When I request to delete question with id 1
    Then the deletion should be prevented
    And I should see an alert "Cannot delete questions after the exam has started"
    And the question with id 1 should still exist

  Scenario: Delete question with confirmation dialog
    Given I am an authenticated administrator
    And question with id 1 exists in the system
    When I initiate delete for question with id 1
    And I see a confirmation dialog "Are you sure you want to delete this question?"
    And I confirm the deletion
    Then the question should be deleted successfully
    And I should see success message "Question deleted successfully!"

  Scenario: Cancel question deletion
    Given I am an authenticated administrator
    And question with id 1 exists in the system
    When I initiate delete for question with id 1
    And I see a confirmation dialog "Are you sure you want to delete this question?"
    And I cancel the deletion
    Then the question should not be deleted
    And the question with id 1 should still exist

  Scenario: Delete question handles database error gracefully
    Given I am an authenticated administrator
    And question with id 1 exists in the system
    And the database connection fails
    When I request to delete question with id 1
    Then the deletion should fail
    And I should see an error message
    And the question with id 1 should still exist