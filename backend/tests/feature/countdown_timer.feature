# tests/feature/countdown_timer.feature

Feature: Exam Countdown Timer
  As a student
  I want to see a countdown timer during the exam
  So that I can manage my time effectively and submit before the deadline

  Background:
    Given an exam scheduled from 09:00 to 11:00

  Scenario: Student starts exam with full time
    Given the current time is 09:00:00
    When the student views the exam timer
    Then the timer should show 2 hours and 0 minutes remaining

  Scenario: Student views timer halfway through exam
    Given the current time is 10:00:00
    When the student views the exam timer
    Then the timer should show 1 hours and 0 minutes remaining

  Scenario: Student views timer near the end
    Given the current time is 10:30:00
    When the student views the exam timer
    Then the remaining time should be 30 minutes

  Scenario: Student views timer with 5 minutes left
    Given the current time is 10:55:00
    When the student views the exam timer
    Then the remaining time should be 5 minutes

  Scenario: Timer reaches zero
    Given the current time is 11:00:00
    When the timer reaches zero
    Then the timer should show 00:00:00
    And the exam should automatically end

  Scenario: Student cannot submit after time expires
    Given the exam has ended
    When the student attempts to submit
    Then the submission should be rejected
    And no further answers can be changed

  Scenario: Timer shows zero after exam end time
    Given the current time is 11:05:00
    When the student views the exam timer
    Then the timer should show exactly 0 seconds
    And the exam should automatically end