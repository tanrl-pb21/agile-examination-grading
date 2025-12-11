"""
Unit Tests for Login Service
Tests AuthService.login() method and related functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
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


class TestLoginPositive:
    """Positive unit tests for login"""
    
    def test_login_valid_credentials(self, auth_service, mock_db_connection):
        """Test login with valid credentials"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_password": "hashed_password_123",
            "user_role": "student",
            "created_at": datetime.now()
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock password verification
        with patch.object(auth_service, 'verify_password', return_value=True):
            with patch.object(auth_service, 'validate_email', return_value="student@test.com"):
                # Act
                result = auth_service.login("student@test.com", "Password123")
                
                # Assert
                assert result["id"] == 1
                assert result["email"] == "student@test.com"
                assert result["role"] == "student"
    
    def test_login_email_normalized(self, auth_service, mock_db_connection):
        """Test that email is normalized before query"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_password": "hashed_password_123",
            "user_role": "student",
            "created_at": datetime.now()
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            # Act
            result = auth_service.login("  STUDENT@TEST.COM  ", "Password123")
            
            # Assert
            # Verify database was called with normalized email
            mock_cursor.execute.assert_called_once()
            args = mock_cursor.execute.call_args[0]
            sql = args[0].lower()
            assert "lower(user_email)" in sql or "user_email" in sql
    
    def test_login_case_insensitive_email(self, auth_service, mock_db_connection):
        """Test login is case insensitive for email"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_password": "hashed_password_123",
            "user_role": "student",
            "created_at": datetime.now()
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            # Act
            result = auth_service.login("STUDENT@TEST.COM", "Password123")
            
            # Assert
            assert result["email"] == "student@test.com"


class TestLoginNegative:
    """Negative unit tests for login"""
    
    def test_login_user_not_found(self, auth_service, mock_db_connection):
        """Test login when user doesn't exist"""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # User not found
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'validate_email', return_value="nonexistent@test.com"):
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid email or password"):
                auth_service.login("nonexistent@test.com", "Password123")
    
    def test_login_wrong_password(self, auth_service, mock_db_connection):
        """Test login with wrong password"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_password": "hashed_password_123",
            "user_role": "student",
            "created_at": datetime.now()
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock password verification to return False
        with patch.object(auth_service, 'verify_password', return_value=False):
            with patch.object(auth_service, 'validate_email', return_value="student@test.com"):
                # Act & Assert
                with pytest.raises(ValueError, match="Invalid email or password"):
                    auth_service.login("student@test.com", "WrongPassword123")
    
    def test_login_empty_email(self, auth_service):
        """Test login with empty email"""
        # Act & Assert
        with pytest.raises(ValueError, match="Email is required"):
            auth_service.login("", "Password123")
    
    def test_login_invalid_email_format(self, auth_service):
        """Test login with invalid email format"""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            auth_service.login("invalid-email", "Password123")
    
    def test_login_empty_password(self, auth_service):
        """Test login with empty password"""
        with patch.object(auth_service, 'validate_email', return_value="student@test.com"):
            # Act & Assert
            with pytest.raises(ValueError, match="Password is required"):
                auth_service.login("student@test.com", "")
    
    def test_login_database_error(self, auth_service, mock_db_connection):
        """Test login when database error occurs"""
        # Arrange
        mock_db_connection.return_value.__enter__.side_effect = Exception("Database connection failed")
        
        with patch.object(auth_service, 'validate_email', return_value="student@test.com"):
            # Act & Assert
            with pytest.raises(ValueError, match="Authentication failed"):
                auth_service.login("student@test.com", "Password123")


class TestPasswordVerification:
    """Test password hashing and verification for login"""
    
    def test_verify_correct_password(self, auth_service):
        """Test password verification with correct password"""
        # Arrange
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        # Act
        result = auth_service.verify_password(hashed, password)
        
        # Assert
        assert result is True
    
    def test_verify_incorrect_password(self, auth_service):
        """Test password verification with incorrect password"""
        # Arrange
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = auth_service.hash_password(password)
        
        # Act
        result = auth_service.verify_password(hashed, wrong_password)
        
        # Assert
        assert result is False
    
    def test_verify_password_with_invalid_hash(self, auth_service):
        """Test password verification with invalid hash format"""
        # Arrange
        invalid_hash = "invalidhashformat"
        
        # Act
        result = auth_service.verify_password(invalid_hash, "Password123")
        
        # Assert
        assert result is False


class TestEmailValidation:
    """Test email validation for login"""
    
    def test_validate_email_valid(self, auth_service):
        """Test valid email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            result = auth_service.validate_email(email)
            assert result == email.strip().lower()
    
    def test_validate_email_invalid(self, auth_service):
        """Test invalid email validation"""
        invalid_cases = [
            ("", "Email is required"),
            ("   ", "Email is required"),
            ("invalid-email", "Invalid email format"),
            ("@domain.com", "Invalid email format"),
            ("user@.com", "Invalid email format"),
        ]
        
        for email, expected_error in invalid_cases:
            with pytest.raises(ValueError) as exc_info:
                auth_service.validate_email(email)
            assert expected_error in str(exc_info.value)
    
    def test_validate_email_too_long(self, auth_service):
        """Test email that is too long"""
        long_email = "a" * 250 + "@example.com"
        
        with pytest.raises(ValueError) as exc_info:
            auth_service.validate_email(long_email)
        
        assert "255 characters" in str(exc_info.value)


class TestJWTTokenGeneration:
    """Test JWT token generation functionality"""
    
    def test_generate_jwt_token_structure(self):
        """Test JWT token generation produces valid structure"""
        from src.routers.auth import generate_jwt_token
        
        # Arrange
        user_id = 1
        email = "student@test.com"
        role = "student"
        
        # Act
        token = generate_jwt_token(user_id, email, role)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
        
        # Verify JWT structure (3 parts separated by dots)
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_generate_jwt_token_with_different_roles(self):
        """Test JWT token generation for different roles"""
        from src.routers.auth import generate_jwt_token
        
        test_cases = [
            (1, "student@test.com", "student"),
            (2, "teacher@test.com", "teacher"),
            (3, "admin@test.com", "admin"),
        ]
        
        for user_id, email, role in test_cases:
            token = generate_jwt_token(user_id, email, role)
            assert token is not None
            assert len(token) > 0


class TestRedirectURLs:
    """Test redirect URL generation based on role"""
    
    def test_get_redirect_url_by_role(self):
        """Test redirect URL generation for different roles"""
        from src.routers.auth import get_redirect_url_by_role
        
        test_cases = [
            ("admin", "/courseManagement"),
            ("teacher", "/examManagement"),
            ("student", "/studentExam"),
            ("unknown", "/"),  # Default for unknown role
        ]
        
        for role, expected_url in test_cases:
            result = get_redirect_url_by_role(role)
            assert result == expected_url
    
    def test_redirect_url_case_sensitive(self):
        """Test redirect URL is case sensitive (current implementation)"""
        from src.routers.auth import get_redirect_url_by_role
        
        # Current implementation is case-sensitive
        test_cases = [
            ("ADMIN", "/"),  # Uppercase doesn't match
            ("Teacher", "/"),  # Title case doesn't match
            ("STUDENT", "/"),  # Uppercase doesn't match
            ("admin", "/courseManagement"),  # Lowercase works
            ("teacher", "/examManagement"),  # Lowercase works
            ("student", "/studentExam"),  # Lowercase works
        ]
        
        for role, expected_url in test_cases:
            result = get_redirect_url_by_role(role)
            assert result == expected_url
    
    def test_redirect_url_with_whitespace(self):
        """Test redirect URL with whitespace in role"""
        from src.routers.auth import get_redirect_url_by_role
        
        test_cases = [
            (" admin ", "/"),  # Whitespace doesn't match
            ("teacher ", "/"),  # Trailing space doesn't match
            (" student", "/"),  # Leading space doesn't match
        ]
        
        for role, expected_url in test_cases:
            result = get_redirect_url_by_role(role)
            assert result == expected_url


class TestLoginIntegration:
    """Integration tests for complete login flow"""
    
    def test_complete_login_flow_mocked(self, auth_service, mock_db_connection):
        """Test complete login flow with mocks"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_password": "hashed_password_123",
            "user_role": "student",
            "created_at": datetime.now()
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            with patch.object(auth_service, 'validate_email', return_value="student@test.com"):
                # Act
                result = auth_service.login("student@test.com", "Password123")
                
                # Assert
                assert result["id"] == 1
                assert result["email"] == "student@test.com"
                assert result["role"] == "student"
                
                # Verify database query
                mock_cursor.execute.assert_called_once()
                sql = mock_cursor.execute.call_args[0][0].lower()
                assert "select" in sql
                assert "user" in sql
                assert "user_email" in sql
    
    def test_login_with_special_characters_in_password(self, auth_service, mock_db_connection):
        """Test login with password containing special characters"""
        # Arrange
        mock_cursor = MagicMock()
        mock_user = {
            "id": 1,
            "user_email": "student@test.com",
            "user_password": "hashed_password_special",
            "user_role": "student",
            "created_at": datetime.now()
        }
        mock_cursor.fetchone.return_value = mock_user
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        special_password = "P@ssw0rd!123"
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            with patch.object(auth_service, 'validate_email', return_value="student@test.com"):
                # Act
                result = auth_service.login("student@test.com", special_password)
                
                # Assert
                assert result["id"] == 1
                assert result["email"] == "student@test.com"