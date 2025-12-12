Feature: Reset Password
  As a user who forgot my password
  I want to reset my password
  So that I can regain access to my account

  # ============================================
  # FORGOT PASSWORD SCENARIOS
  # ============================================

  Scenario: Successful password reset request with existing email
    Given a user with email "student@example.com" exists
    When the user submits forgot password with email "student@example.com"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"
    And a password reset email should be sent
    And the user should be redirected to "/login"

  Scenario: Password reset request with non-existent email
    Given a user with email "nonexistent@example.com" does not exist
    When the user submits forgot password with email "nonexistent@example.com"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"
    And no email should be sent
    And the user should be redirected to "/login"

  Scenario: Password reset request with invalid email format
    When the user submits invalid email format "invalid-email"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"

  Scenario: Password reset request with empty email
    When the user submits forgot password with empty email
    Then the system should handle empty email appropriately

  # ============================================
  # RESET PASSWORD SCENARIOS
  # ============================================

  Scenario: Successful password reset with valid token
    Given the user has a valid reset token "valid_token_123"
    When the user resets password with token "valid_token_123" and new password "NewPassword123"
    Then the system should return status code 200
    And the response message should contain "Password reset successfully"
    And the user should be redirected to "/login"
    And the response should contain user id 1
    And the response should contain role "student"

  Scenario: Reset password with expired token
    Given the user has an expired reset token "expired_token_456"
    When the user resets password with token "expired_token_456" and new password "NewPassword123"
    Then the system should return status code 400
    And the error detail should contain "Invalid or expired reset token"

  Scenario: Reset password with invalid token
    Given the reset token "invalid_token_789" is invalid
    When the user resets password with token "invalid_token_789" and new password "NewPassword123"
    Then the system should return status code 400
    And the error detail should contain "Invalid or expired reset token"

  Scenario: Reset password with mismatched passwords
    When the user resets password with mismatched passwords "NewPassword123" and "DifferentPassword456"
    Then the system should return status code 400
    And the error detail should contain "New passwords do not match"

  Scenario: Reset password with weak password (too short)
    When the user submits weak password "weak"
    Then the system should return status code 400
    And the error detail should contain "Password must be at least 8 characters long"

  Scenario: Reset password with weak password (no uppercase)
    When the user submits weak password "lowercase123"
    Then the system should return status code 400
    And the error detail should contain "Password must contain at least one uppercase letter"

  Scenario: Reset password with weak password (no lowercase)
    When the user submits weak password "UPPERCASE123"
    Then the system should return status code 400
    And the error detail should contain "Password must contain at least one lowercase letter"

  Scenario: Reset password with weak password (no digits)
    When the user submits weak password "NoDigitsHere"
    Then the system should return status code 400
    And the error detail should contain "Password must contain at least one digit"

  # ============================================
  # TOKEN VERIFICATION SCENARIOS
  # ============================================

  Scenario: Verify valid reset token
    When the user verifies reset token "valid_token_123"
    Then the system should return status code 200
    And the token verification should be valid

  Scenario: Verify expired reset token
    When the user verifies reset token "expired_token_456"
    Then the system should return status code 200
    And the token verification should be invalid

  Scenario: Verify invalid reset token
    When the user verifies reset token "nonexistent_token"
    Then the system should return status code 200
    And the token verification should be invalid

  # ============================================
  # COMPLETE FLOW SCENARIOS
  # ============================================

  Scenario: Complete password reset flow
    Given a user with email "student@example.com" exists
    When the user submits forgot password with email "student@example.com"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"
    When the user verifies reset token "valid_token_123"
    Then the token verification should be valid
    When the user resets password with token "valid_token_123" and new password "NewSecurePass123"
    Then the system should return status code 200
    And the response message should contain "Password reset successfully"
    And the user should be redirected to "/login"

  Scenario: Complete flow with invalid token
    Given a user with email "student@example.com" exists
    When the user submits forgot password with email "student@example.com"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"
    When the user verifies reset token "wrong_token"
    Then the token verification should be invalid
    When the user resets password with token "wrong_token" and new password "NewSecurePass123"
    Then the system should return status code 400
    And the error detail should contain "Invalid or expired reset token"

  # ============================================
  # SECURITY SCENARIOS
  # ============================================

  Scenario: Security - Same response for all emails (existing user)
    Given a user with email "student@example.com" exists
    When the user submits forgot password with email "student@example.com"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"

  Scenario: Security - Same response for all emails (non-existent user)
    Given a user with email "nonexistent@example.com" does not exist
    When the user submits forgot password with email "nonexistent@example.com"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"

  Scenario: Security - Token one-time use
    Given the user has a valid reset token "one_time_token"
    When the user resets password with token "one_time_token" and new password "NewPass123"
    Then the system should return status code 200
    And the response message should contain "Password reset successfully"
    When the user tries to reuse the same token
    Then the system should return status code 400
    And the error detail should contain "Invalid or expired reset token"

  # ============================================
  # EDGE CASES
  # ============================================

  Scenario: Reset password with special characters in password
    Given the user has a valid reset token "valid_token_123"
    When the user resets password with token "valid_token_123" and new password "NewPass@123#Special"
    Then the system should return status code 200
    And the response message should contain "Password reset successfully"

  Scenario: Reset password with very long password
    Given the user has a valid reset token "valid_token_123"
    When the user resets password with token "valid_token_123" and new password "VeryLongPassword1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    Then the system should return status code 200
    And the response message should contain "Password reset successfully"

  Scenario: Reset to same as old password (allowed)
    Given the user has a valid reset token "valid_token_123"
    When the user resets password with token "valid_token_123" and new password "OldPassword123"
    Then the system should return status code 200
    And the response message should contain "Password reset successfully"

  Scenario: Email sending failure
    Given a user with email "student@example.com" exists
    And the email service is temporarily unavailable
    When the user submits forgot password with email "student@example.com"
    Then the system should return status code 200
    And the response message should contain "If an account exists with this email"
    And the user should be redirected to "/login"
