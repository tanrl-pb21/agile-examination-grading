"""
Unit Tests for Reset Password Service
Tests AuthService.request_password_reset() and reset_password() methods
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from src.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    """Create AuthService instance"""
    return AuthService()


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch('src.services.auth_service.get_conn') as mock_conn:
        yield mock_conn


class TestRequestPasswordResetPositive:
    """Positive unit tests for request_password_reset"""
    
    def test_request_reset_valid_email(self, auth_service, mock_db_connection):
        """Test requesting password reset with valid email"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com"
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'user_exists_by_email', return_value=True):
            # Act
            result = auth_service.request_password_reset("student@test.com")
            
            # Assert
            assert "reset_token" in result
            assert result["user_id"] == 1
            assert "password reset link will be sent" in result["message"]
            assert len(result["reset_token"]) > 20  # Token should be long enough
    
    def test_request_reset_email_normalized(self, auth_service, mock_db_connection):
        """Test that email is normalized (trimmed and lowercased)"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com"
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'user_exists_by_email', return_value=True):
            # Act
            result = auth_service.request_password_reset("  STUDENT@TEST.COM  ")
            
            # Assert
            assert "reset_token" in result
            # Verify database was called with normalized email
            mock_cursor.execute.assert_called_once()
            args = mock_cursor.execute.call_args[0]
            assert args[1][2] == "student@test.com"
    
    def test_request_reset_generates_unique_tokens(self, auth_service, mock_db_connection):
        """Test that each request generates a unique token"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com"
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'user_exists_by_email', return_value=True):
            # Act
            result1 = auth_service.request_password_reset("student@test.com")
            result2 = auth_service.request_password_reset("student@test.com")
            
            # Assert
            assert result1["reset_token"] != result2["reset_token"]
    
    def test_request_reset_stores_hashed_token(self, auth_service, mock_db_connection):
        """Test that token is hashed before storing in database"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com"
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'user_exists_by_email', return_value=True):
            # Act
            result = auth_service.request_password_reset("student@test.com")
            
            # Assert
            # Verify that the stored token is different from the returned token
            stored_token = mock_cursor.execute.call_args[0][1][0]
            assert stored_token != result["reset_token"]
            assert len(stored_token) == 64  # SHA-256 hash is 64 hex characters


class TestRequestPasswordResetNegative:
    """Negative unit tests for request_password_reset"""
    
    def test_request_reset_invalid_email_format(self, auth_service):
        """Test request reset with invalid email format"""
        # Act
        result = auth_service.request_password_reset("invalid-email")
        
        # Assert
        # Should still return success message for security
        assert "password reset link will be sent" in result["message"]
        assert "reset_token" not in result
    
    def test_request_reset_empty_email(self, auth_service):
        """Test request reset with empty email"""
        # Act
        result = auth_service.request_password_reset("")
        
        # Assert
        assert "password reset link will be sent" in result["message"]
        assert "reset_token" not in result
    
    def test_request_reset_nonexistent_email(self, auth_service):
        """Test request reset with non-existent email (security test)"""
        # Arrange
        with patch.object(auth_service, 'user_exists_by_email', return_value=False):
            # Act
            result = auth_service.request_password_reset("nonexistent@test.com")
            
            # Assert
            # Should return same message for security
            assert "password reset link will be sent" in result["message"]
            assert "reset_token" not in result
    
    def test_request_reset_database_error(self, auth_service, mock_db_connection):
        """Test request reset with database error"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database error")
        
        with patch.object(auth_service, 'user_exists_by_email', return_value=True):
            # Act
            result = auth_service.request_password_reset("student@test.com")
            
            # Assert
            # Should still return success message for security
            assert "password reset link will be sent" in result["message"]


class TestResetPasswordPositive:
    """Positive unit tests for reset_password"""
    
    def test_reset_password_valid_token(self, auth_service, mock_db_connection):
        """Test resetting password with valid token"""
        # Arrange
        mock_cursor = MagicMock()
        # First query - find user with valid token
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        # Second query - return updated user
        mock_updated_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_role": "student",
            "created_at": datetime.now(timezone.utc)
        }
        mock_cursor.fetchone.side_effect = [mock_user, mock_updated_user]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = auth_service.reset_password("valid_token_12345", "NewPassword123")
        
        # Assert
        assert result["id"] == 1
        assert result["email"] == "student@test.com"
        assert "Password reset successfully" in result["message"]
    
    def test_reset_password_clears_token(self, auth_service, mock_db_connection):
        """Test that reset password clears the reset token"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        mock_updated_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_role": "student",
            "created_at": datetime.now(timezone.utc)
        }
        mock_cursor.fetchone.side_effect = [mock_user, mock_updated_user]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = auth_service.reset_password("valid_token", "NewPassword123")
        
        # Assert
        # Verify UPDATE query sets tokens to NULL
        update_call = mock_cursor.execute.call_args_list[1]
        sql = update_call[0][0]
        assert "password_reset_token = NULL" in sql
        assert "password_reset_expires = NULL" in sql
    
    def test_reset_password_hashes_new_password(self, auth_service, mock_db_connection):
        """Test that new password is hashed"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        mock_updated_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_role": "student",
            "created_at": datetime.now(timezone.utc)
        }
        mock_cursor.fetchone.side_effect = [mock_user, mock_updated_user]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = auth_service.reset_password("valid_token", "NewPassword123")
        
        # Assert
        # Verify that password was hashed (contains $ separator from salt$hash format)
        update_call = mock_cursor.execute.call_args_list[1]
        hashed_password = update_call[0][1][0]
        assert "$" in hashed_password
        assert hashed_password != "NewPassword123"


class TestResetPasswordNegative:
    """Negative unit tests for reset_password"""
    
    def test_reset_password_invalid_token(self, auth_service, mock_db_connection):
        """Test reset password with invalid token"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid or expired reset token"):
            auth_service.reset_password("invalid_token", "NewPassword123")
    
    def test_reset_password_expired_token(self, auth_service, mock_db_connection):
        """Test reset password with expired token"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Token expired, so no user found
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid or expired reset token"):
            auth_service.reset_password("expired_token", "NewPassword123")
    
    def test_reset_password_empty_token(self, auth_service):
        """Test reset password with empty token"""
        # Act & Assert
        with pytest.raises(ValueError, match="Reset token is required"):
            auth_service.reset_password("", "NewPassword123")
    
    def test_reset_password_weak_password(self, auth_service, mock_db_connection):
        """Test reset password with weak password"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="at least 8 characters"):
            auth_service.reset_password("valid_token", "weak")
    
    def test_reset_password_no_uppercase(self, auth_service, mock_db_connection):
        """Test reset password without uppercase letter"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="uppercase letter"):
            auth_service.reset_password("valid_token", "password123")
    
    def test_reset_password_no_lowercase(self, auth_service, mock_db_connection):
        """Test reset password without lowercase letter"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="lowercase letter"):
            auth_service.reset_password("valid_token", "PASSWORD123")
    
    def test_reset_password_no_digit(self, auth_service, mock_db_connection):
        """Test reset password without digit"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(ValueError, match="digit"):
            auth_service.reset_password("valid_token", "PasswordOnly")
    
    def test_reset_password_database_error(self, auth_service, mock_db_connection):
        """Test reset password with database error"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Password reset failed"):
            auth_service.reset_password("valid_token", "NewPassword123")
    
    def test_reset_password_token_used_twice(self, auth_service, mock_db_connection):
        """Test that token cannot be used twice"""
        # Arrange
        mock_cursor = MagicMock()
        # First use - token exists
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        mock_updated_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_role": "student",
            "created_at": datetime.now(timezone.utc)
        }
        
        # First call succeeds
        mock_cursor.fetchone.side_effect = [mock_user, mock_updated_user]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act - first use
        result = auth_service.reset_password("valid_token", "NewPassword123")
        assert result["id"] == 1
        
        # Second use - token no longer exists (was cleared)
        mock_cursor.fetchone.side_effect = [None]
        
        # Act & Assert - second use should fail
        with pytest.raises(ValueError, match="Invalid or expired reset token"):
            auth_service.reset_password("valid_token", "AnotherPassword123")


class TestPasswordVerification:
    """Test password hashing and verification"""
    
    def test_verify_password_correct(self, auth_service):
        """Test password verification with correct password"""
        # Arrange
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        # Act
        result = auth_service.verify_password(hashed, password)
        
        # Assert
        assert result is True
    
    def test_verify_password_incorrect(self, auth_service):
        """Test password verification with incorrect password"""
        # Arrange
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        # Act
        result = auth_service.verify_password(hashed, "WrongPassword123")
        
        # Assert
        assert result is False
    
    def test_verify_password_invalid_hash_format(self, auth_service):
        """Test password verification with invalid hash format"""
        # Arrange
        invalid_hash = "invalidhashformat"
        
        # Act
        result = auth_service.verify_password(invalid_hash, "Password123")
        
        # Assert
        assert result is False
    
    def test_hash_password_generates_different_salts(self, auth_service):
        """Test that same password generates different hashes (due to salt)"""
        # Arrange
        password = "TestPassword123"
        
        # Act
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Assert
        assert hash1 != hash2  # Different salts should produce different hashes
        assert auth_service.verify_password(hash1, password)
        assert auth_service.verify_password(hash2, password)


class TestUserExists:
    """Test user_exists_by_email method"""
    
    def test_user_exists_returns_true(self, auth_service, mock_db_connection):
        """Test that user_exists_by_email returns True when user exists"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # User exists
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = auth_service.user_exists_by_email("student@test.com")
        
        # Assert
        assert result is True
    
    def test_user_exists_returns_false(self, auth_service, mock_db_connection):
        """Test that user_exists_by_email returns False when user doesn't exist"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # User doesn't exist
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Act
        result = auth_service.user_exists_by_email("nonexistent@test.com")
        
        # Assert
        assert result is False
    
    def test_user_exists_database_error(self, auth_service, mock_db_connection):
        """Test that user_exists_by_email returns False on database error"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database error")
        
        # Act
        result = auth_service.user_exists_by_email("student@test.com")
        
        # Assert
        assert result is False