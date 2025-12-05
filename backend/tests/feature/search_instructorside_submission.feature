Feature: Search submissions on instructor side

  # Existing scenarios
  Scenario: Search submissions by student name (case-insensitive)
    Given I am viewing the submission list for exam 1
    When I search for submissions by student name "Alice"
    Then I should see 1 submission matching "Alice"

  Scenario: Search submissions by student email (case-insensitive)
    Given I am viewing the submission list for exam 1
    When I search for submissions by student email "bob@example.com"
    Then I should see 1 submission matching "bob@example.com"

  Scenario: Search submissions by submission ID
    Given I am viewing the submission list for exam 1
    When I search for submissions by submission ID "sub3"
    Then I should see 1 submission matching "sub3"

  Scenario: Search submissions with no match
    Given I am viewing the submission list for exam 1
    When I search for submissions by student name "Nonexistent"
    Then I should see 0 submissions

  # ----------------- New scenarios -----------------

  Scenario: Search submissions by partial student name
    Given I am viewing the submission list for exam 1
    When I search for submissions by student name "li"
    Then I should see 2 submissions matching "li"

  Scenario: Search submissions by partial email
    Given I am viewing the submission list for exam 1
    When I search for submissions by student email "example.com"
    Then I should see 3 submissions matching "example.com"

  Scenario: Search submissions sorted by score descending
    Given I am viewing the submission list for exam 1
    When I sort submissions by score descending
    Then the first submission should have score 90

  Scenario: Search submissions sorted by score ascending
    Given I am viewing the submission list for exam 1
    When I sort submissions by score ascending
    Then the first submission should have score 70

  Scenario: Search submissions by date range
    Given I am viewing the submission list for exam 1
    When I filter submissions from "2025-12-01" to "2025-12-01"
    Then I should see 3 submissions

  Scenario: Search submissions with multiple filters
    Given I am viewing the submission list for exam 1
    When I search for submissions by student name "Bob"
      And I filter submissions by status "graded"
    Then I should see 1 submission matching "Bob"
