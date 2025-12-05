# features/exam_search_filter_api.feature
Feature: Exam Search and Filter API Endpoints
  As an instructor or student
  I want to use API endpoints to search and filter exams
  So that I can programmatically access exam data with various filters

  Background:
    Given the following exams exist
      | id | title                    | exam_code   | course | date       | start_time | end_time | status      |
      | 1  | Midterm Exam             | CS101-MID   | 1      | 2025-12-15 | 09:00      | 11:00    | scheduled   |
      | 2  | Final Exam               | CS101-FIN   | 1      | 2025-12-20 | 14:00      | 16:00    | completed   |
      | 3  | Mathematics Quiz         | MATH101-QZ  | 2      | 2025-12-18 | 10:30      | 11:30    | scheduled   |
      | 4  | Python Test              | CS102-TST   | 3      | 2025-12-22 | 15:00      | 17:00    | cancelled   |
      | 5  | Data Structures Exam     | CS201-DSA   | 4      | 2025-12-25 | 13:00      | 15:00    | scheduled   |


  # ===================== SEARCH BY TITLE API TESTS =====================
  Scenario: Instructor searches exams by title
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by title "Midterm"
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have title "Midterm Exam"
    And the first exam should have code "CS101-MID"
    And the response should be a valid JSON array

  Scenario: Instructor searches exams by title with partial match
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by title "Exam"
    Then the API should return status code 200
    And I should see 2 exams in the results
    And the response should be a valid JSON array

  Scenario: Instructor searches exams by title case insensitive
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by title "MIDTERM"
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have title "Midterm Exam"

  Scenario: Instructor searches exams by title with empty string
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by title with empty string
    Then the API should return status code 400
    And the error message should contain "Search term cannot be empty"

  Scenario: Instructor searches exams by title with no match
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by title "NonExistent"
    Then the API should return status code 200
    And I should get an empty list


  # ===================== SEARCH BY CODE API TESTS =====================
  Scenario: Instructor searches exams by exam code
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by code "CS101-MID"
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have code "CS101-MID"
    And the first exam should have title "Midterm Exam"

  Scenario: Instructor searches exams by exam code case insensitive
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by code "cs101-mid" case insensitive
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have code "CS101-MID"

  Scenario: Instructor searches exams by invalid exam code
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by code "INVALID-CODE"
    Then the API should return status code 200
    And I should get an empty list

  Scenario: Instructor searches exams by empty exam code
    Given I am viewing the exam list
    And I am an instructor
    When I search for exams by code ""
    Then the API should return status code 400
    And the error message should contain "Exam code cannot be empty"


  # ===================== SEARCH BY COURSE API TESTS =====================
  Scenario: Student searches their exams by course name
    Given I am a student with ID 1
    When I search my exams by course "Computer Science"
    Then the API should return status code 200
    And I should see 2 exams in the results
    And the response should be a valid JSON array

  Scenario: Student searches their exams by course name case insensitive
    Given I am a student with ID 1
    When I search my exams by course "COMPUTER SCIENCE"
    Then the API should return status code 200
    And I should see 2 exams in the results

  Scenario: Student searches their exams by partial course name
    Given I am a student with ID 1
    When I search my exams by course "Computer"
    Then the API should return status code 200
    And I should see 2 exams in the results

  Scenario: Student searches their exams by non-enrolled course
    Given I am a student with ID 1
    When I search my exams by course "Physics"
    Then the API should return status code 200
    And I should get an empty list

  Scenario: Student searches their exams with empty course name
    Given I am a student with ID 1
    When I search my exams by course ""
    Then the API should return status code 400
    And the error message should contain "Course name cannot be empty"


  # ===================== FILTER BY STATUS API TESTS =====================
  Scenario: Instructor filters all exams by scheduled status
    Given I am viewing the exam list
    And I am an instructor
    When I filter exams by status "scheduled"
    Then the API should return status code 200
    And I should see 3 exams in the results
    And all exams should have status scheduled
    And the response should be a valid JSON array

  Scenario: Instructor filters all exams by completed status
    Given I am viewing the exam list
    And I am an instructor
    When I filter exams by status "completed"
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have status "completed"

  Scenario: Instructor filters all exams by cancelled status
    Given I am viewing the exam list
    And I am an instructor
    When I filter exams by status "cancelled"
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have status "cancelled"

  Scenario: Instructor filters exams by status case insensitive
    Given I am viewing the exam list
    And I am an instructor
    When I filter exams by status "SCHEDULED"
    Then the API should return status code 200
    And I should see 3 exams in the results
    And all exams should have status scheduled

  Scenario: Instructor filters exams by invalid status
    Given I am viewing the exam list
    And I am an instructor
    When I filter exams by invalid status "invalid"
    Then the API should return status code 400
    And the error message should contain "Status must be one of"

  Scenario: Instructor filters exams by empty status
    Given I am viewing the exam list
    And I am an instructor
    When I filter exams by status ""
    Then the API should return status code 400
    And the error message should contain "Status must be one of"


  # ===================== FILTER STUDENT EXAMS BY STATUS API TESTS =====================
  Scenario: Student filters their exams by scheduled status
    Given I am a student with ID 1
    When I filter my exams by status "scheduled"
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have status "scheduled"
    And the response should be a valid JSON array

  Scenario: Student filters their exams by completed status
    Given I am a student with ID 1
    When I filter my exams by status "completed"
    Then the API should return status code 200
    And I should see 1 exam in the results
    And the first exam should have status "completed"

  Scenario: Student filters their exams by non-existent status results
    Given I am a student with ID 1
    When I filter my exams by status "cancelled"
    Then the API should return status code 200
    And I should get an empty list

  Scenario: Student filters exams with invalid student ID
    Given I am a student with ID 0
    When I filter my exams by status "scheduled"
    Then the API should return status code 400
    And the error message should contain "Valid student ID is required"

  Scenario: Student filters exams by invalid status
    Given I am a student with ID 1
    When I filter my exams by status "invalid"
    Then the API should return status code 400
    And the error message should contain "Status must be one of"