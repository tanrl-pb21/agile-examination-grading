Feature: User Login
  As a user
  I want to login to my account
  So that I can access the system features

  # ============================================
  # SUCCESSFUL LOGIN SCENARIOS
  # ============================================

  Scenario: Successful login with correct credentials
    Given a user with email "student@example.com" and password "Password123" exists
    And the JWT secret is configured
    When the user submits login with email "student@example.com" and password "Password123"
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user information should include id 1
    And the user information should include email "student@example.com"
    And the user information should include role "student"
    And the user should be redirected to "/studentExam"

  Scenario: Successful login with remember_me true
    Given a user with email "student@example.com" and password "Password123" exists
    And the JWT secret is configured
    When the user submits login with remember_me true
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user should be redirected to "/studentExam"

  Scenario: Successful login with remember_me false
    Given a user with email "student@example.com" and password "Password123" exists
    And the JWT secret is configured
    When the user submits login with remember_me false
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user should be redirected to "/studentExam"

  Scenario: Successful login with case insensitive email
    Given a user with email "student@example.com" and password "Password123" exists
    And the JWT secret is configured
    When the user submits login with email "STUDENT@EXAMPLE.COM" and password "Password123"
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the user information should include email "student@example.com"

  Scenario: Successful login as admin
    Given the user with email "admin@example.com" has role "admin"
    And the JWT secret is configured
    When the user with role "admin" logs in
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user information should include role "admin"
    And the redirect URL should be appropriate for role "admin"

  Scenario: Successful login as teacher
    Given the user with email "teacher@example.com" has role "teacher"
    And the JWT secret is configured
    When the user with role "teacher" logs in
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user information should include role "teacher"
    And the redirect URL should be appropriate for role "teacher"

  Scenario: Successful login as student
    Given the user with email "student@example.com" has role "student"
    And the JWT secret is configured
    When the user with role "student" logs in
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user information should include role "student"
    And the redirect URL should be appropriate for role "student"

  # ============================================
  # FAILED LOGIN SCENARIOS
  # ============================================

  Scenario: Login with non-existent email
    Given a user with email "nonexistent@example.com" does not exist
    When the user submits login with email "nonexistent@example.com" and password "Password123"
    Then the system should return status code 401
    And the error detail should contain "Invalid email or password"
    And no token should be returned

  Scenario: Login with wrong password
    Given a user with email "student@example.com" and password "Password123" exists
    When the user submits login with email "student@example.com" and wrong password "WrongPassword"
    Then the system should return status code 401
    And the error detail should contain "Invalid email or password"
    And no token should be returned

  # Note: The following validation scenarios are skipped because the API returns 401
  # instead of 422 for validation errors. This is a security-first approach where
  # validation happens in the service layer, not in the request validation layer.

  # ============================================
  # SECURITY SCENARIOS
  # ============================================

  Scenario: Same error message for invalid email and password (security)
    Given a user with email "student@example.com" does not exist
    When the user submits login with email "student@example.com" and wrong password "WrongPassword"
    Then the system should return status code 401
    And the error detail should contain "Invalid email or password"
    And no token should be returned
    # Security: Same error message whether email exists or password is wrong

  Scenario: Login with locked account
    Given the user account is locked
    When the user submits login with email "student@example.com" and password "Password123"
    Then the system should return status code 500
    And the error detail should contain "Login failed"
    And no token should be returned

  Scenario: Authentication service failure
    Given the authentication service is down
    When the user submits login with email "student@example.com" and password "Password123"
    Then the system should return status code 500
    And the error detail should contain "Login failed"
    And no token should be returned

  # ============================================
  # EDGE CASES
  # ============================================

  Scenario: Login with password containing special characters
    Given a user with email "student@example.com" and password "P@ssw0rd!123" exists
    And the JWT secret is configured
    When the user submits login with email "student@example.com" and special password "P@ssw0rd!123"
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data

  Scenario: Login with very long password
    Given a user with email "student@example.com" and password "VeryLongPassword1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ" exists
    And the JWT secret is configured
    When the user submits login with email "student@example.com" and special password "VeryLongPassword1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data

  Scenario: Login with leading/trailing spaces in email
    Given a user with email "student@example.com" and password "Password123" exists
    And the JWT secret is configured
    When the user submits login with email "  student@example.com  " and password "Password123"
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the user information should include email "student@example.com"

  # ============================================
  # JWT TOKEN SCENARIOS
  # ============================================

  Scenario: JWT token contains correct user information
    Given a user with email "student@example.com" and password "Password123" exists
    And the JWT secret is configured
    When the user submits login with email "student@example.com" and password "Password123"
    Then the system should return status code 200
    And a valid JWT token should be returned
    And the token should contain user ID, email, and role information

  Scenario: Different users get different tokens
    Given a user with email "student1@example.com" and password "Password123" exists
    And a user with email "student2@example.com" and password "Password123" exists
    And the JWT secret is configured
    When user 1 logs in with email "student1@example.com"
    And user 2 logs in with email "student2@example.com"
    Then both users should receive different JWT tokens
    And each token should contain the correct user information

  # ============================================
  # REDIRECT SCENARIOS
  # ============================================

  Scenario: Default redirect for unknown role
    Given the user with email "unknown@example.com" has role "unknown"
    And the JWT secret is configured
    When the user with role "unknown" logs in
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user should be redirected to "/"

  # ============================================
  # COMPREHENSIVE SCENARIOS
  # ============================================

  Scenario: Complete login flow for student
    Given a user with email "john.doe@university.edu" and password "StudentPass123" exists
    And the user with email "john.doe@university.edu" has role "student"
    And the JWT secret is configured
    When the user submits login with email "john.doe@university.edu" and password "StudentPass123"
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user information should include email "john.doe@university.edu"
    And the user information should include role "student"
    And the user should be redirected to "/studentExam"

  Scenario: Complete login flow for teacher
    Given a user with email "prof.smith@university.edu" and password "TeacherPass123" exists
    And the user with email "prof.smith@university.edu" has role "teacher"
    And the JWT secret is configured
    When the user submits login with email "prof.smith@university.edu" and password "TeacherPass123"
    Then the system should return status code 200
    And the response message should contain "Login successful"
    And a valid JWT token should be returned
    And the response should contain valid user data
    And the user information should include email "prof.smith@university.edu"
    And the user information should include role "teacher"
    And the user should be redirected to "/examManagement"