Feature: Manage exam scheduling
  As a course instructor
  I want to create and manage exams through the API
  So that I can organize and schedule exams for my courses

  Background:
    Given the API is running
    And the exam database is empty

  # ==================== HAPPY PATH SCENARIOS ====================

  Scenario: Create exam successfully
    When I create an exam with title "Software Engineering Midterm" and code "SEK123" on "2026-01-04" from "09:00" to "11:00"
    Then I receive status code 201
    And the exam is created with title "Software Engineering Midterm"
    And the exam has exam_code "SEK123"
    And the exam is scheduled for "2026-01-04"
    And the exam time is from "09:00" to "11:00"

  Scenario: Get all exams
    Given an exam "Math Midterm" with code "MATH101" on "2026-02-10" from "10:00" to "12:00" exists
    When I request all exams
    Then I receive status code 200
    And the response is a list
    And the list contains an exam with title "Math Midterm"

  Scenario: Get exam by ID successfully
    Given an exam "Physics Final" with code "PHYS201" on "2026-03-15" from "14:00" to "16:00" exists
    When I get the exam by ID
    Then I receive status code 200
    And the response contains title "Physics Final"
    And the response contains exam_code "PHYS201"

  # ==================== VALIDATION FAILURE SCENARIOS ====================

  Scenario: Create exam fails when title is missing
    When I create an exam with missing title
    Then I receive status code 422

  Scenario: Create exam fails when exam code is missing
    When I create an exam with missing exam_code
    Then I receive status code 422

  Scenario: Create exam fails with invalid date format
    When I create an exam with invalid date format "14-01-2025"
    Then I receive status code 400 or 422

  Scenario: Create exam fails with invalid time format
    When I create an exam with invalid time format "9am"
    Then I receive status code 400 or 422

  Scenario: Create exam fails with past date
    When I create an exam with past date "2020-01-01"
    Then I receive status code 422

  Scenario: Create exam fails when end time is before start time
    When I create an exam with start_time "11:00" and end_time "09:00"
    Then I receive status code 422
    And the error message contains "End time must be after start time"

  # ==================== CONFLICT & UNIQUENESS SCENARIOS ====================

  Scenario: Create exam fails on duplicate exam code
    Given an exam "Existing Exam" with code "DUPLICATE" on "2026-03-10" from "09:00" to "11:00" exists
    When I try to create an exam with duplicate code "DUPLICATE"
    Then I receive status code 400 or 422
    And the error message contains "duplicate"

  Scenario: Create exam fails on scheduling conflict
    Given an exam "Existing Exam" with code "EXIST001" on "2026-02-14" from "09:00" to "11:00" exists
    When I create an exam with overlapping time on "2026-02-14" from "10:00" to "12:00"
    Then I receive status code 400 or 422
    And the error message contains "conflict"

  # ==================== NOT FOUND SCENARIOS ====================

  Scenario: Get exam by non-existent ID returns 404
    When I request an exam with ID "99999"
    Then I receive status code 404