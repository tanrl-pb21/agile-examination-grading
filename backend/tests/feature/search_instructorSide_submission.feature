Feature: Instructor Submission Management
  As an instructor
  I want to search, filter, and view summary information about student submissions
  So that I can manage grading efficiently and understand exam participation

  Background:
    Given I am logged in as an instructor
    And an exam with id "101" exists
    And the exam has 5 enrolled students
    And 3 students have submitted their exam
    And 2 students have missed the exam

  # User Story 1: Search student submissions by student ID
  Scenario: Successfully search submission by exact student ID
    Given student with id "1" has submitted the exam
    When I search for submissions with student ID "STU0001"
    Then I should see 1 submission result
    And the result should contain student with ID "STU0001"
    And the result should show student name "John Doe"

  Scenario: Search submission by partial student ID
    Given student with id "2" has submitted the exam
    When I search for submissions with partial ID "STU000"
    Then I should see multiple submission results
    And all results should contain "STU000" in their student ID

  Scenario: Search with non-existent student ID
    When I search for submissions with student ID "STU9999"
    Then I should see 0 submission results
    And I should see a message "No submissions found"

  Scenario: Search submission by student name
    Given student "Jane Smith" has submitted the exam
    When I search for submissions with name "Jane Smith"
    Then I should see 1 submission result
    And the result should show student name "Jane Smith"

  Scenario: Search submission by student email
    Given student with email "john.doe@example.com" has submitted
    When I search for submissions with email "john.doe@example.com"
    Then I should see 1 submission result
    And the result should show email "john.doe@example.com"

  Scenario: Case-insensitive search for student name
    Given student "Bob Johnson" has submitted the exam
    When I search for submissions with name "bob johnson"
    Then I should see 1 submission result
    And the result should show student name "Bob Johnson"

  # User Story 2: Filter submissions by status
  Scenario: Filter submissions to show only pending submissions
    Given there are 2 pending submissions
    And there are 3 graded submissions
    When I filter submissions by status "pending"
    Then I should see 2 submission results
    And all results should have status "pending"

  Scenario: Filter submissions to show only graded submissions
    Given there are 3 graded submissions
    And there are 2 pending submissions
    When I filter submissions by status "graded"
    Then I should see 3 submission results
    And all results should have status "graded"

  Scenario: Filter submissions to show only missed submissions
    Given there are 2 students who missed the exam
    When I filter submissions by status "missed"
    Then I should see 2 submission results
    And all results should have status "missed"
    And all results should have no submission date

  Scenario: Filter to show all submissions
    Given there are 5 total students enrolled
    When I filter submissions by status "all"
    Then I should see 5 submission results
    And results should include all statuses

  Scenario: Combine search and filter
    Given student "John Doe" has a graded submission
    And student "Jane Smith" has a pending submission
    When I search for "John" and filter by status "graded"
    Then I should see 1 submission result
    And the result should show student name "John Doe"
    And the result should have status "graded"

  Scenario: Filter with no matching results
    Given there are no pending submissions
    When I filter submissions by status "pending"
    Then I should see 0 submission results
    And I should see a message "No submissions found"

  # User Story 3: View summary information
  Scenario: View total students enrolled
    Given there are 5 students enrolled in the course
    When I view the submission summary
    Then the total students count should be 5

  Scenario: View total submitted count
    Given 3 students have submitted their exam
    And 2 students have not submitted
    When I view the submission summary
    Then the submitted count should be 3

  Scenario: View total missed count
    Given 2 students have missed the exam
    And 3 students have submitted
    When I view the submission summary
    Then the missed count should be 2

  Scenario: View complete summary statistics
    Given there are 10 students enrolled in the course
    And 6 students have submitted their exam
    And 4 students have missed the exam
    When I view the submission summary
    Then the total students count should be 10
    And the submitted count should be 6
    And the missed count should be 4

  Scenario: Summary updates after new submission
    Given there are 5 students enrolled
    And 3 students have submitted
    And 2 students have missed
    When a new student submits their exam
    Then the submitted count should increase to 4
    And the missed count should decrease to 1

  Scenario: View summary with no submissions
    Given there are 5 students enrolled in the course
    And 0 students have submitted their exam
    When I view the submission summary
    Then the total students count should be 5
    And the submitted count should be 0
    And the missed count should be 5

  Scenario: View summary with all submissions completed
    Given there are 5 students enrolled in the course
    And 5 students have submitted their exam
    When I view the submission summary
    Then the total students count should be 5
    And the submitted count should be 5
    And the missed count should be 0

  Scenario: Summary shows graded vs pending breakdown
    Given there are 3 graded submissions
    And there are 2 pending submissions
    When I view the submission summary with status breakdown
    Then I should see graded count as 3
    And I should see pending count as 2

  # API Integration Scenarios
  Scenario: API returns correct submission data
    Given the exam API endpoint is available
    When I request submissions for exam "101"
    Then the API should return status code 200
    And the response should contain all enrolled students
    And the response should include submission details

  Scenario: API handles invalid exam ID
    Given the exam API endpoint is available
    When I request submissions for exam "999999"
    Then the API should return status code 404
    And the response should contain error message "Exam not found"

  Scenario: API returns submissions with score information
    Given student "1" has a graded submission with score 85
    When I request submissions for exam "101"
    Then the API response should include score 85 for student "1"
    And the API response should include score_grade "A" for student "1"