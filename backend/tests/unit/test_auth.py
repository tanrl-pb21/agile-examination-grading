import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
import jwt
import hashlib
import secrets

# Import the modules to test
from src.services.auth_service import AuthService
from routers.auth import (
    router, generate_jwt_token, get_redirect_url_by_role,
    LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest
)

# Create FastAPI app and include router for testing
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# ===== FIXTURES =====
@pytest.fixture
def auth_service():
    """Provide AuthService instance for testing"""
    return AuthService()


@pytest.fixture
def mock_db_conn():
    """Mock database connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    return mock_conn


@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        "id": 1,
        "user_email": "test@example.com",
        "user_password": "hashed_password",
        "user_role": "student",
        "student_id": "12ABC34567",
        "created_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing"""
    return generate_jwt_token(1, "test@example.com", "student")


# ===== AUTHSERVICE VALIDATION TESTS =====

class TestAuthServiceHashPassword:
    """Test password hashing"""
    
    def test_hash_password_generates_valid_hash(self, auth_service):
        """Test that password is hashed with salt"""
        password = "SecurePass123"
        hashed = auth_service.hash_password(password)
        
        assert "$" in hashed  # Should contain salt separator
        assert len(hashed) > len(password)
    
    def test_hash_password_different_salts(self, auth_service):
        """Test that same password produces different hashes"""
        password = "SecurePass123"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        assert hash1 != hash2  # Different salts should produce different hashes


class TestAuthServiceVerifyPassword:
    """Test password verification"""
    
    def test_verify_password_correct(self, auth_service):
        """Test verification with correct password"""
        password = "SecurePass123"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(hashed, password) is True
    
    def test_verify_password_incorrect(self, auth_service):
        """Test verification with incorrect password"""
        password = "SecurePass123"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(hashed, "WrongPassword123") is False
    
    def test_verify_password_invalid_format(self, auth_service):
        """Test verification with malformed hash"""
        assert auth_service.verify_password("invalid_hash_format", "password") is False


class TestAuthServiceValidateEmail:
    """Test email validation"""
    
    def test_validate_email_valid(self, auth_service):
        """Test valid email"""
        email = auth_service.validate_email("test@example.com")
        assert email == "test@example.com"
    
    def test_validate_email_uppercase_conversion(self, auth_service):
        """Test email is lowercased"""
        email = auth_service.validate_email("TEST@EXAMPLE.COM")
        assert email == "test@example.com"
    
    def test_validate_email_empty(self, auth_service):
        """Test empty email raises error"""
        with pytest.raises(ValueError, match="Email is required"):
            auth_service.validate_email("")
    
    def test_validate_email_whitespace_only(self, auth_service):
        """Test whitespace-only email"""
        with pytest.raises(ValueError, match="Email is required"):
            auth_service.validate_email("   ")
    
    def test_validate_email_invalid_format(self, auth_service):
        """Test invalid email format"""
        with pytest.raises(ValueError, match="Invalid email format"):
            auth_service.validate_email("invalid-email")
    
    def test_validate_email_too_long(self, auth_service):
        """Test email exceeding 255 characters"""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValueError, match="255 characters"):
            auth_service.validate_email(long_email)


class TestAuthServiceValidatePassword:
    """Test password validation"""
    
    def test_validate_password_valid(self, auth_service):
        """Test valid password"""
        password = auth_service.validate_password("SecurePass123")
        assert password == "SecurePass123"
    
    def test_validate_password_empty(self, auth_service):
        """Test empty password"""
        with pytest.raises(ValueError, match="Password is required"):
            auth_service.validate_password("")
    
    def test_validate_password_too_short(self, auth_service):
        """Test password less than 8 characters"""
        with pytest.raises(ValueError, match="at least 8 characters"):
            auth_service.validate_password("Short1A")
    
    def test_validate_password_no_uppercase(self, auth_service):
        """Test password without uppercase"""
        with pytest.raises(ValueError, match="uppercase"):
            auth_service.validate_password("nouppercase123")
    
    def test_validate_password_no_lowercase(self, auth_service):
        """Test password without lowercase"""
        with pytest.raises(ValueError, match="lowercase"):
            auth_service.validate_password("NOLOWERCASE123")
    
    def test_validate_password_no_digit(self, auth_service):
        """Test password without digit"""
        with pytest.raises(ValueError, match="digit"):
            auth_service.validate_password("NoDigitPassword")


class TestAuthServiceValidateStudentId:
    """Test student ID validation"""
    
    def test_validate_student_id_valid(self, auth_service):
        """Test valid student ID"""
        student_id = auth_service.validate_student_id("12ABC34567")
        assert student_id == "12ABC34567"
    
    def test_validate_student_id_empty(self, auth_service):
        """Test empty student ID"""
        with pytest.raises(ValueError, match="Student ID is required"):
            auth_service.validate_student_id("")
    
    def test_validate_student_id_invalid_length(self, auth_service):
        """Test student ID with wrong length"""
        with pytest.raises(ValueError, match="exactly 10 characters"):
            auth_service.validate_student_id("12ABC345")
    
    def test_validate_student_id_invalid_format(self, auth_service):
        """Test student ID with invalid format"""
        with pytest.raises(ValueError, match="2 digits \\+ 3 letters \\+ 5 digits"):
            auth_service.validate_student_id("ABC1234567")
    
    def test_validate_student_id_lowercase_conversion(self, auth_service):
        """Test student ID is converted to uppercase"""
        student_id = auth_service.validate_student_id("12abc34567")
        assert student_id == "12ABC34567"


class TestAuthServiceValidateStaffId:
    """Test staff ID validation"""
    
    def test_validate_staff_id_valid(self, auth_service):
        """Test valid staff ID"""
        staff_id = auth_service.validate_staff_id("12DEF34567")
        assert staff_id == "12DEF34567"
    
    def test_validate_staff_id_empty(self, auth_service):
        """Test empty staff ID"""
        with pytest.raises(ValueError, match="Staff ID is required"):
            auth_service.validate_staff_id("")
    
    def test_validate_staff_id_invalid_format(self, auth_service):
        """Test staff ID with invalid format"""
        with pytest.raises(ValueError, match="2 digits \\+ 3 letters \\+ 5 digits"):
            auth_service.validate_staff_id("ABC1234567")


class TestAuthServiceUserExists:
    """Test user existence check"""
    
    @patch('src.services.auth_service.get_conn')
    def test_user_exists_by_email_true(self, mock_get_conn, auth_service):
        """Test user exists"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        result = auth_service.user_exists_by_email("test@example.com")
        assert result is True
    
    @patch('src.services.auth_service.get_conn')
    def test_user_exists_by_email_false(self, mock_get_conn, auth_service):
        """Test user does not exist"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        result = auth_service.user_exists_by_email("nonexistent@example.com")
        assert result is False
    
    @patch('src.services.auth_service.get_conn')
    def test_user_exists_by_email_exception(self, mock_get_conn, auth_service):
        """Test user exists with database error"""
        mock_get_conn.side_effect = Exception("DB Error")
        
        result = auth_service.user_exists_by_email("test@example.com")
        assert result is False
    
    @patch('src.services.auth_service.get_conn')
    def test_student_id_exists_true(self, mock_get_conn, auth_service):
        """Test student ID exists"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        result = auth_service.student_id_exists("12ABC34567")
        assert result is True
    
    @patch('src.services.auth_service.get_conn')
    def test_staff_id_exists_false(self, mock_get_conn, auth_service):
        """Test staff ID does not exist"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        result = auth_service.staff_id_exists("12XYZ34567")
        assert result is False


class TestAuthServiceLogin:
    """Test user login"""
    
    @patch('src.services.auth_service.get_conn')
    def test_login_success(self, mock_get_conn, auth_service):
        """Test successful login"""
        password = "SecurePass123"
        hashed_password = auth_service.hash_password(password)
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "user_email": "test@example.com",
            "user_password": hashed_password,
            "user_role": "student",
            "created_at": datetime.now(timezone.utc)
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        user = auth_service.login("test@example.com", password)
        
        assert user["email"] == "test@example.com"
        assert user["role"] == "student"
        assert user["id"] == 1
    
    @patch('src.services.auth_service.get_conn')
    def test_login_invalid_email(self, mock_get_conn, auth_service):
        """Test login with non-existent email"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_service.login("nonexistent@example.com", "SecurePass123")
    
    @patch('src.services.auth_service.get_conn')
    def test_login_invalid_password(self, mock_get_conn, auth_service):
        """Test login with wrong password"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "user_email": "test@example.com",
            "user_password": auth_service.hash_password("SecurePass123"),
            "user_role": "student",
            "created_at": datetime.now(timezone.utc)
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_service.login("test@example.com", "WrongPassword123")
    
    def test_login_empty_password(self, auth_service):
        """Test login with empty password"""
        with pytest.raises(ValueError):
            auth_service.login("test@example.com", "")


class TestAuthServiceRegister:
    """Test user registration"""
    
    @patch('src.services.auth_service.AuthService.student_id_exists')
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    @patch('src.services.auth_service.get_conn')
    def test_register_student_success(self, mock_get_conn, mock_user_exists, mock_student_exists, auth_service):
        """Test successful student registration"""
        mock_user_exists.return_value = False
        mock_student_exists.return_value = False
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "user_email": "newstudent@example.com",
            "user_role": "student",
            "student_id": "12ABC34567",
            "created_at": datetime.now(timezone.utc)
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        user = auth_service.register(
            email="newstudent@example.com",
            password="SecurePass123",
            role="student",
            student_id="12ABC34567"
        )
        
        assert user["email"] == "newstudent@example.com"
        assert user["role"] == "student"
        assert user["student_id"] == "12ABC34567"
    
    @patch('src.services.auth_service.AuthService.staff_id_exists')
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    @patch('src.services.auth_service.get_conn')
    def test_register_teacher_success(self, mock_get_conn, mock_user_exists, mock_staff_exists, auth_service):
        """Test successful teacher registration"""
        mock_user_exists.return_value = False
        mock_staff_exists.return_value = False
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 2,
            "user_email": "newteacher@example.com",
            "user_role": "teacher",
            "lecturer_id": "12XYZ34567",
            "created_at": datetime.now(timezone.utc)
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        user = auth_service.register(
            email="newteacher@example.com",
            password="SecurePass123",
            role="teacher",
            staff_id="12XYZ34567"
        )
        
        assert user["email"] == "newteacher@example.com"
        assert user["role"] == "teacher"
        assert user["staff_id"] == "12XYZ34567"
    
    @patch('src.services.auth_service.AuthService.student_id_exists')
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    def test_register_student_without_id(self, mock_user_exists, mock_student_exists, auth_service):
        """Test student registration without student ID"""
        mock_user_exists.return_value = False
        mock_student_exists.return_value = False
        
        with pytest.raises(ValueError, match="Student ID is required"):
            auth_service.register(
                email="test@example.com",
                password="SecurePass123",
                role="student"
            )
    
    @patch('src.services.auth_service.AuthService.staff_id_exists')
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    def test_register_teacher_without_id(self, mock_user_exists, mock_staff_exists, auth_service):
        """Test teacher registration without staff ID"""
        mock_user_exists.return_value = False
        mock_staff_exists.return_value = False
        
        with pytest.raises(ValueError, match="Staff ID is required"):
            auth_service.register(
                email="test@example.com",
                password="SecurePass123",
                role="teacher"
            )
    
    @patch('src.services.auth_service.AuthService.student_id_exists')
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    def test_register_student_id_exists(self, mock_user_exists, mock_student_exists, auth_service):
        """Test registration with existing student ID"""
        mock_user_exists.return_value = False
        mock_student_exists.return_value = True  # Student ID already exists
        
        with pytest.raises(ValueError, match="already registered"):
            auth_service.register(
                email="new@example.com",
                password="SecurePass123",
                role="student",
                student_id="12ABC34567"
            )
    
    @patch('src.services.auth_service.AuthService.student_id_exists')
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    def test_register_email_exists(self, mock_user_exists, mock_student_exists, auth_service):
        """Test registration with existing email"""
        mock_user_exists.return_value = True  # Email already exists
        mock_student_exists.return_value = False
        
        with pytest.raises(ValueError, match="already exists"):
            auth_service.register(
                email="existing@example.com",
                password="SecurePass123",
                role="student",
                student_id="12ABC34567"
            )
    
    @patch('src.services.auth_service.AuthService.student_id_exists')
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    def test_register_invalid_role(self, mock_user_exists, mock_student_exists, auth_service):
        """Test registration with invalid role"""
        mock_user_exists.return_value = False
        mock_student_exists.return_value = False
        
        with pytest.raises(ValueError, match="Role must be one of"):
            auth_service.register(
                email="test@example.com",
                password="SecurePass123",
                role="admin",  # Invalid role
                student_id="12ABC34567"
            )


class TestAuthServicePasswordReset:
    """Test password reset functionality"""
    
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    @patch('src.services.auth_service.get_conn')
    def test_request_password_reset_success(self, mock_get_conn, mock_user_exists, auth_service):
        """Test successful password reset request"""
        mock_user_exists.return_value = True
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "user_email": "test@example.com"
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        result = auth_service.request_password_reset("test@example.com")
        
        assert "reset_token" in result
        assert result["user_id"] == 1
    
    @patch('src.services.auth_service.AuthService.user_exists_by_email')
    def test_request_password_reset_nonexistent_email(self, mock_user_exists, auth_service):
        """Test password reset with non-existent email (security)"""
        mock_user_exists.return_value = False
        
        result = auth_service.request_password_reset("nonexistent@example.com")
        
        assert "reset_token" not in result
        assert "If an account exists" in result["message"]
    
    @patch('src.services.auth_service.get_conn')
    def test_reset_password_success(self, mock_get_conn, auth_service):
        """Test successful password reset"""
        new_password = "NewSecurePass456"
        reset_token = "valid_reset_token_12345"
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "user_email": "test@example.com",
                "password_reset_expires": datetime.now(timezone.utc) + timedelta(hours=1)
            },
            {
                "id": 1,
                "user_email": "test@example.com",
                "user_role": "student",
                "created_at": datetime.now(timezone.utc)
            }
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        result = auth_service.reset_password(reset_token, new_password)
        
        assert result["email"] == "test@example.com"
        assert "Password reset successfully" in result["message"]
    
    @patch('src.services.auth_service.get_conn')
    def test_reset_password_invalid_token(self, mock_get_conn, auth_service):
        """Test password reset with invalid token"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        with pytest.raises(ValueError, match="Invalid or expired"):
            auth_service.reset_password("invalid_token", "NewSecurePass456")
    
    def test_reset_password_empty_token(self, auth_service):
        """Test password reset with empty token"""
        with pytest.raises(ValueError):
            auth_service.reset_password("", "NewSecurePass456")


class TestAuthServiceGetUser:
    """Test get user functionality"""
    
    @patch('src.services.auth_service.get_conn')
    def test_get_user_by_id_success(self, mock_get_conn, auth_service):
        """Test getting user by ID"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "user_email": "test@example.com",
            "user_role": "student",
            "student_id": "12ABC34567",
            "created_at": datetime.now(timezone.utc)
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        user = auth_service.get_user_by_id(1)
        assert user["user_email"] == "test@example.com"
        assert user["user_role"] == "student"
    
    @patch('src.services.auth_service.get_conn')
    def test_get_user_by_id_not_found(self, mock_get_conn, auth_service):
        """Test getting non-existent user"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        with pytest.raises(ValueError, match="not found"):
            auth_service.get_user_by_id(999)
    
    def test_get_user_by_id_invalid(self, auth_service):
        """Test getting user with invalid ID"""
        with pytest.raises(ValueError, match="positive integer"):
            auth_service.get_user_by_id(-1)
    
    @patch('src.services.auth_service.get_conn')
    def test_get_user_by_email_success(self, mock_get_conn, auth_service):
        """Test getting user by email"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "user_email": "test@example.com",
            "user_role": "student",
            "student_id": "12ABC34567",
            "created_at": datetime.now(timezone.utc)
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        user = auth_service.get_user_by_email("test@example.com")
        assert user["user_email"] == "test@example.com"
        assert user["id"] == 1
    
    @patch('src.services.auth_service.get_conn')
    def test_get_user_by_email_not_found(self, mock_get_conn, auth_service):
        """Test getting user by non-existent email"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_get_conn.return_value = mock_conn
        
        with pytest.raises(ValueError, match="not found"):
            auth_service.get_user_by_email("nonexistent@example.com")


# ===== JWT AND ROUTER TESTS =====

class TestJWTGeneration:
    """Test JWT token generation"""
    
    def test_generate_jwt_token_valid(self):
        """Test valid JWT token generation"""
        token = generate_jwt_token(1, "test@example.com", "student")
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_generate_jwt_token_payload(self):
        """Test JWT token contains correct payload"""
        user_id = 1
        email = "test@example.com"
        role = "student"
        
        token = generate_jwt_token(user_id, email, role)
        
        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role
        assert "exp" in payload
        assert "iat" in payload


class TestGetRedirectUrlByRole:
    """Test redirect URL generation by role"""
    
    def test_redirect_admin(self):
        """Test admin redirect URL"""
        url = get_redirect_url_by_role("admin")
        assert url == "/courseManagement"
    
    def test_redirect_teacher(self):
        """Test teacher redirect URL"""
        url = get_redirect_url_by_role("teacher")
        assert url == "/examManagement"
    
    def test_redirect_student(self):
        """Test student redirect URL"""
        url = get_redirect_url_by_role("student")
        assert url == "/studentExam"
    
    def test_redirect_unknown_role(self):
        """Test unknown role defaults to home"""
        url = get_redirect_url_by_role("unknown")
        assert url == "/"


# ===== ENDPOINT TESTS =====

class TestLoginEndpoint:
    """Test login endpoint"""
    
    @patch('routers.auth.auth_service.login')
    def test_login_success(self, mock_login):
        """Test successful login endpoint"""
        mock_login.return_value = {
            "id": 1,
            "email": "test@example.com",
            "role": "student"
        }
        
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "SecurePass123"}
        )
        
        assert response.status_code == 200
        assert response.json()["token"] is not None
        assert response.json()["user"]["email"] == "test@example.com"
        assert response.json()["redirect_url"] == "/studentExam"
    
    @patch('routers.auth.auth_service.login')
    def test_login_invalid_credentials(self, mock_login):
        """Test login with invalid credentials"""
        mock_login.side_effect = ValueError("Invalid email or password")
        
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "WrongPassword"}
        )
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    @patch('routers.auth.auth_service.login')
    def test_login_server_error(self, mock_login):
        """Test login with server error"""
        mock_login.side_effect = Exception("Database error")
        
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "SecurePass123"}
        )
        
        assert response.status_code == 500


class TestRegisterEndpoint:
    """Test register endpoint"""
    
    @patch('routers.auth.auth_service.register')
    @patch('routers.auth.auth_service.student_id_exists')
    @patch('routers.auth.email_service.send_welcome_email')
    def test_register_student_success(self, mock_email, mock_student_exists, mock_register):
        """Test successful student registration endpoint"""
        mock_student_exists.return_value = False
        mock_register.return_value = {
            "id": 1,
            "email": "newstudent@example.com",
            "role": "student",
            "student_id": "12ABC34567"
        }
        mock_email.return_value = True
        
        response = client.post(
            "/auth/register",
            json={
                "email": "newstudent@example.com",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
                "role": "student",
                "student_id": "12ABC34567"
            }
        )
        
        assert response.status_code == 200
        assert "Registration successful" in response.json()["message"]
        assert response.json()["redirect_url"] == "/login"
    
    @patch('routers.auth.auth_service.register')
    @patch('routers.auth.auth_service.student_id_exists')
    def test_register_password_mismatch(self, mock_student_exists, mock_register):
        """Test register with mismatched passwords"""
        mock_student_exists.return_value = False
        
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "confirm_password": "DifferentPass456",
                "role": "student",
                "student_id": "12ABC34567"
            }
        )
        
        assert response.status_code == 400
    
    @patch('routers.auth.auth_service.student_id_exists')
    def test_register_student_id_exists(self, mock_student_exists):
        """Test register with existing student ID"""
        mock_student_exists.return_value = True
        
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
                "role": "student",
                "student_id": "12ABC34567"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestForgotPasswordEndpoint:
    """Test forgot password endpoint"""
    
    @patch('routers.auth.auth_service.request_password_reset')
    @patch('routers.auth.email_service.send_password_reset_email')
    def test_forgot_password_success(self, mock_email, mock_reset):
        """Test successful forgot password request"""
        mock_reset.return_value = {
            "message": "If an account exists with this email, a password reset link will be sent",
            "reset_token": "token123",
            "user_id": 1
        }
        mock_email.return_value = True
        
        response = client.post(
            "/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        assert "password reset link will be sent" in response.json()["message"]
    
    @patch('routers.auth.auth_service.request_password_reset')
    def test_forgot_password_no_user(self, mock_reset):
        """Test forgot password with non-existent email"""
        mock_reset.return_value = {
            "message": "If an account exists with this email, a password reset link will be sent"
        }
        
        response = client.post(
            "/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 200
        assert "password reset link will be sent" in response.json()["message"]


class TestResetPasswordEndpoint:
    """Test reset password endpoint"""
    
    @patch('routers.auth.auth_service.reset_password')
    def test_reset_password_success(self, mock_reset):
        """Test successful password reset"""
        mock_reset.return_value = {
            "id": 1,
            "email": "test@example.com",
            "role": "student",
            "message": "Password reset successfully. Please login with your new password."
        }
        
        response = client.post(
            "/auth/reset-password",
            json={
                "reset_token": "valid_token",
                "new_password": "NewSecurePass456",
                "confirm_password": "NewSecurePass456"
            }
        )
        
        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]
    
    @patch('routers.auth.auth_service.reset_password')
    def test_reset_password_mismatch(self, mock_reset):
        """Test reset password with mismatched passwords"""
        response = client.post(
            "/auth/reset-password",
            json={
                "reset_token": "valid_token",
                "new_password": "NewSecurePass456",
                "confirm_password": "DifferentPass789"
            }
        )
        
        assert response.status_code == 400
    
    @patch('routers.auth.auth_service.reset_password')
    def test_reset_password_invalid_token(self, mock_reset):
        """Test reset password with invalid token"""
        mock_reset.side_effect = ValueError("Invalid or expired reset token")
        
        response = client.post(
            "/auth/reset-password",
            json={
                "reset_token": "invalid_token",
                "new_password": "NewSecurePass456",
                "confirm_password": "NewSecurePass456"
            }
        )
        
        assert response.status_code == 400




class TestLogoutEndpoint:
    """Test logout endpoint"""
    
    def test_logout_success(self):
        """Test successful logout"""
        response = client.post("/auth/logout")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Logout successful"
        assert response.json()["redirect_url"] == "/login"


class TestGetUserEndpoint:
    """Test get user endpoint"""
    
    @patch('routers.auth.auth_service.get_user_by_id')
    def test_get_user_success(self, mock_get_user):
        """Test get user by ID"""
        mock_get_user.return_value = {
            "id": 1,
            "user_email": "test@example.com",
            "user_role": "student",
            "student_id": "12ABC34567",
            "created_at": datetime.now(timezone.utc)
        }
        
        response = client.get("/auth/user/1")
        
        assert response.status_code == 200
        assert response.json()["user_email"] == "test@example.com"
    
    @patch('routers.auth.auth_service.get_user_by_id')
    def test_get_user_not_found(self, mock_get_user):
        """Test get non-existent user"""
        mock_get_user.side_effect = ValueError("User with id 999 not found")
        
        response = client.get("/auth/user/999")
        
        assert response.status_code == 404
    
    @patch('routers.auth.auth_service.get_user_by_id')
    def test_get_user_server_error(self, mock_get_user):
        """Test get user with server error"""
        mock_get_user.side_effect = Exception("Database error")
        
        response = client.get("/auth/user/1")
        
        assert response.status_code == 500


# ===== REQUEST VALIDATION TESTS =====

class TestLoginRequestValidation:
    """Test LoginRequest validation"""
    
    def test_login_request_valid(self):
        """Test valid login request"""
        req = LoginRequest(email="test@example.com", password="SecurePass123")
        assert req.email == "test@example.com"
    
    def test_login_request_email_lowercase(self):
        """Test email is lowercased"""
        req = LoginRequest(email="TEST@EXAMPLE.COM", password="SecurePass123")
        assert req.email == "test@example.com"
    
    def test_login_request_empty_email(self):
        """Test login request with empty email"""
        with pytest.raises(ValueError):
            LoginRequest(email="", password="SecurePass123")


class TestRegisterRequestValidation:
    """Test RegisterRequest validation"""
    
    def test_register_request_valid(self):
        """Test valid register request"""
        req = RegisterRequest(
            email="test@example.com",
            password="SecurePass123",
            confirm_password="SecurePass123",
            role="student",
            student_id="12ABC34567"
        )
        assert req.email == "test@example.com"
        assert req.role == "student"


class TestForgotPasswordRequestValidation:
    """Test ForgotPasswordRequest validation"""
    
    def test_forgot_password_request_valid(self):
        """Test valid forgot password request"""
        req = ForgotPasswordRequest(email="test@example.com")
        assert req.email == "test@example.com"


class TestResetPasswordRequestValidation:
    """Test ResetPasswordRequest validation"""
    
    def test_reset_password_request_valid(self):
        """Test valid reset password request"""
        req = ResetPasswordRequest(
            reset_token="valid_token",
            new_password="NewSecurePass456",
            confirm_password="NewSecurePass456"
        )
        assert req.reset_token == "valid_token"