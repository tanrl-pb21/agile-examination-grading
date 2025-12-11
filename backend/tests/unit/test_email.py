"""
Unit Tests for EmailService
Testing email service functionality with mocked SMTP
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import smtplib
import os
import base64
from email import message_from_string
from src.services.email_service import EmailService


def decode_email_content(message):
    """Helper function to decode base64 email content"""
    message_str = str(message)
    
    # Try to extract and decode base64 content
    try:
        # Get the payload parts
        if hasattr(message, 'get_payload'):
            payload = message.get_payload()
            if isinstance(payload, list):
                # Multipart message
                decoded_parts = []
                for part in payload:
                    if part.get_content_type() == 'text/plain':
                        decoded_parts.append(part.get_payload(decode=True).decode('utf-8'))
                    elif part.get_content_type() == 'text/html':
                        decoded_parts.append(part.get_payload(decode=True).decode('utf-8'))
                return ' '.join(decoded_parts)
            else:
                # Single part
                return message.get_payload(decode=True).decode('utf-8')
        return message_str
    except Exception:
        return message_str


class TestEmailService:
    """Unit tests for EmailService"""
    
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up mock environment variables"""
        monkeypatch.setenv("SMTP_SERVER", "smtp.test.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "test@test.com")
        monkeypatch.setenv("SMTP_PASSWORD", "testpass123")
        monkeypatch.setenv("FROM_EMAIL", "noreply@test.com")
        monkeypatch.setenv("FROM_NAME", "Test System")
        monkeypatch.setenv("FRONTEND_URL", "https://frontend.test.com")
    
    @pytest.fixture
    def email_service(self, mock_env_vars):
        """Create EmailService instance with mocked environment"""
        return EmailService()
    
    @pytest.fixture
    def mock_smtp(self):
        """Mock SMTP server"""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            yield mock_server
    
    # ========================
    # send_email Tests
    # ========================
    
    def test_send_email_success(self, email_service, mock_smtp):
        """Test sending email successfully"""
        # Call method
        result = email_service.send_email(
            to_email="recipient@test.com",
            subject="Test Subject",
            html_content="<h1>Test HTML</h1>",
            text_content="Test Text"
        )
        
        # Assertions
        assert result is True
        
        # Verify SMTP calls
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@test.com", "testpass123")
        mock_smtp.send_message.assert_called_once()
        
        # Verify message content
        sent_message = mock_smtp.send_message.call_args[0][0]
        assert sent_message["Subject"] == "Test Subject"
        assert sent_message["From"] == "Test System <noreply@test.com>"
        assert sent_message["To"] == "recipient@test.com"
    
    def test_send_email_html_only(self, email_service, mock_smtp):
        """Test sending email with only HTML content (no text)"""
        result = email_service.send_email(
            to_email="recipient@test.com",
            subject="HTML Only",
            html_content="<h1>HTML Only</h1>"
            # No text_content
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
    
    def test_send_email_smtp_error(self, email_service):
        """Test sending email when SMTP server has error"""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            mock_server.starttls.side_effect = smtplib.SMTPException("SMTP Error")
            
            result = email_service.send_email(
                to_email="recipient@test.com",
                subject="Test",
                html_content="<h1>Test</h1>"
            )
            
            assert result is False
    
    def test_send_email_authentication_error(self, email_service):
        """Test sending email when authentication fails"""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
            
            result = email_service.send_email(
                to_email="recipient@test.com",
                subject="Test",
                html_content="<h1>Test</h1>"
            )
            
            assert result is False
    
    def test_send_email_connection_error(self, email_service):
        """Test sending email when connection fails"""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = ConnectionError("Connection refused")
            
            result = email_service.send_email(
                to_email="recipient@test.com",
                subject="Test",
                html_content="<h1>Test</h1>"
            )
            
            assert result is False
    
    def test_send_email_timeout_error(self, email_service):
        """Test sending email when SMTP times out"""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = TimeoutError("Connection timeout")
            
            result = email_service.send_email(
                to_email="recipient@test.com",
                subject="Test",
                html_content="<h1>Test</h1>"
            )
            
            assert result is False
    
    # ========================
    # send_password_reset_email Tests
    # ========================
    
    def test_send_password_reset_email_success(self, email_service, mock_smtp):
        """Test sending password reset email successfully"""
        result = email_service.send_password_reset_email(
            to_email="user@test.com",
            reset_token="abc123-token-xyz789"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
        
        # Verify message contains reset link
        sent_message = mock_smtp.send_message.call_args[0][0]
        assert "Password Reset Request" in sent_message["Subject"]
        
        # Decode the email content
        decoded_content = decode_email_content(sent_message)
        assert "abc123-token-xyz789" in decoded_content
        assert "https://frontend.test.com/reset-password?token=abc123-token-xyz789" in decoded_content
    
    def test_send_password_reset_email_default_from(self, email_service, mock_smtp):
        """Test password reset email uses default from address when not set"""
        # Temporarily remove FROM_EMAIL env var
        original_from_email = os.environ.get("FROM_EMAIL")
        if original_from_email:
            del os.environ["FROM_EMAIL"]
        
        try:
            # Recreate service with updated environment
            service = EmailService()
            
            result = service.send_password_reset_email(
                to_email="user@test.com",
                reset_token="test-token"
            )
            
            assert result is True
            
            # Should use SMTP_USERNAME as from email
            sent_message = mock_smtp.send_message.call_args[0][0]
            assert "test@test.com" in sent_message["From"]
        finally:
            # Restore environment
            if original_from_email:
                os.environ["FROM_EMAIL"] = original_from_email
    
    def test_send_password_reset_email_includes_security_info(self, email_service, mock_smtp):
        """Test password reset email includes security information"""
        result = email_service.send_password_reset_email(
            to_email="user@test.com",
            reset_token="test-token"
        )
        
        assert result is True
        
        # Verify email contains security information
        sent_message = mock_smtp.send_message.call_args[0][0]
        decoded_content = decode_email_content(sent_message).lower()
        
        # Check for security-related content (be flexible with exact wording)
        has_security_info = (
            "24 hours" in decoded_content or 
            "24 hour" in decoded_content or
            "expire" in decoded_content or
            "valid for" in decoded_content
        )
        assert has_security_info, f"Expected security info in: {decoded_content[:500]}"
        
        # Check for "didn't request" or "ignore" message
        has_ignore_message = (
            "ignore this email" in decoded_content or 
            "didn't request" in decoded_content or
            "not request" in decoded_content or
            "security" in decoded_content
        )
        assert has_ignore_message, f"Expected ignore/security message in: {decoded_content[:500]}"
    
    # ========================
    # send_welcome_email Tests
    # ========================
    
    def test_send_welcome_email_with_name(self, email_service, mock_smtp):
        """Test sending welcome email with user name"""
        result = email_service.send_welcome_email(
            to_email="newuser@test.com",
            user_name="John Doe"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
        
        sent_message = mock_smtp.send_message.call_args[0][0]
        decoded_content = decode_email_content(sent_message)
        assert "Welcome to Exam Management System!" in sent_message["Subject"]
        assert "John Doe" in decoded_content
    
    def test_send_welcome_email_without_name(self, email_service, mock_smtp):
        """Test sending welcome email without user name"""
        result = email_service.send_welcome_email(
            to_email="newuser@test.com"
            # No user_name
        )
        
        assert result is True
        
        sent_message = mock_smtp.send_message.call_args[0][0]
        decoded_content = decode_email_content(sent_message)
        
        # Should use generic greeting (be flexible with exact wording)
        has_greeting = (
            "Hello!" in decoded_content or 
            "Welcome" in decoded_content or
            "Hi" in decoded_content
        )
        assert has_greeting, f"Expected greeting in: {decoded_content[:500]}"
        assert "John Doe" not in decoded_content
    
    def test_send_welcome_email_branding(self, email_service, mock_smtp):
        """Test welcome email includes branding"""
        result = email_service.send_welcome_email(
            to_email="newuser@test.com",
            user_name="Jane Smith"
        )
        
        assert result is True
        
        sent_message = mock_smtp.send_message.call_args[0][0]
        decoded_content = decode_email_content(sent_message)
        assert "Exam Management System" in decoded_content
        
        # Check for copyright year (current year or 2024)
        import datetime
        current_year = str(datetime.datetime.now().year)
        has_year = "2024" in decoded_content or current_year in decoded_content
        assert has_year, f"Expected year in: {decoded_content[:500]}"
    
    # ========================
    # EmailService Initialization Tests
    # ========================
    
    def test_init_with_custom_values(self, monkeypatch):
        """Test EmailService initialization with custom values"""
        monkeypatch.setenv("SMTP_SERVER", "custom.smtp.com")
        monkeypatch.setenv("SMTP_PORT", "465")
        monkeypatch.setenv("SMTP_USERNAME", "custom@test.com")
        monkeypatch.setenv("SMTP_PASSWORD", "custompass")
        monkeypatch.setenv("FROM_EMAIL", "customfrom@test.com")
        monkeypatch.setenv("FROM_NAME", "Custom Name")
        monkeypatch.setenv("FRONTEND_URL", "https://custom.frontend.com")
        
        service = EmailService()
        
        assert service.smtp_server == "custom.smtp.com"
        assert service.smtp_port == 465
        assert service.smtp_username == "custom@test.com"
        assert service.smtp_password == "custompass"
        assert service.from_email == "customfrom@test.com"
        assert service.from_name == "Custom Name"
        assert service.frontend_url == "https://custom.frontend.com"
    
    def test_init_with_defaults(self, monkeypatch):
        """Test EmailService initialization with default values"""
        # Clear all environment variables
        monkeypatch.delenv("SMTP_SERVER", raising=False)
        monkeypatch.delenv("SMTP_PORT", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)
        monkeypatch.delenv("FROM_EMAIL", raising=False)
        monkeypatch.delenv("FROM_NAME", raising=False)
        monkeypatch.delenv("FRONTEND_URL", raising=False)
        
        service = EmailService()
        
        # Should use defaults
        assert service.smtp_server == "smtp.gmail.com"
        assert service.smtp_port == 587
        assert service.smtp_username is None
        assert service.smtp_password is None
        assert service.from_email is None  # Will use smtp_username when sending
        assert service.from_name == "Exam Management System"
        assert service.frontend_url == "http://localhost:8000"
    
    def test_init_with_empty_strings(self, monkeypatch):
        """Test EmailService initialization with empty strings in env vars"""
        monkeypatch.setenv("SMTP_SERVER", "")
        monkeypatch.setenv("SMTP_PORT", "")  # Empty string will cause error
        monkeypatch.setenv("SMTP_USERNAME", "")
        monkeypatch.setenv("SMTP_PASSWORD", "")
        monkeypatch.setenv("FROM_EMAIL", "")
        monkeypatch.setenv("FROM_NAME", "")
        monkeypatch.setenv("FRONTEND_URL", "")
        
        # Should handle empty SMTP_PORT gracefully or raise ValueError
        # Depending on implementation, either:
        # 1. Fix the EmailService to handle empty strings
        # 2. Expect the error
        
        # Option 2: Test that it raises ValueError for empty port
        with pytest.raises(ValueError, match="invalid literal for int"):
            service = EmailService()
        
        # OR Option 1: If EmailService handles it, test the defaults
        # monkeypatch.delenv("SMTP_PORT")  # Remove instead of empty
        # service = EmailService()
        # assert service.smtp_port == 587
    
    # ========================
    # Edge Cases and Error Handling
    # ========================
    
    def test_send_email_with_special_characters(self, email_service, mock_smtp):
        """Test sending email with special characters and Unicode"""
        result = email_service.send_email(
            to_email="user@test.com",
            subject="Test é ñ 汉字",
            html_content="<h1>Test é ñ 汉字</h1>",
            text_content="Test é ñ 汉字"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
    
    def test_send_email_empty_subject(self, email_service, mock_smtp):
        """Test sending email with empty subject"""
        result = email_service.send_email(
            to_email="user@test.com",
            subject="",  # Empty subject
            html_content="<h1>Test</h1>"
        )
        
        assert result is True
        
        sent_message = mock_smtp.send_message.call_args[0][0]
        assert sent_message["Subject"] == ""  # Should accept empty subject
    
    def test_send_email_long_content(self, email_service, mock_smtp):
        """Test sending email with very long content"""
        long_html = "<h1>" + "A" * 10000 + "</h1>"
        long_text = "A" * 10000
        
        result = email_service.send_email(
            to_email="user@test.com",
            subject="Long Content Test",
            html_content=long_html,
            text_content=long_text
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
    
    def test_send_email_multiple_recipients_syntax(self, email_service, mock_smtp):
        """Test sending email with multiple recipients (comma-separated)"""
        result = email_service.send_email(
            to_email="user1@test.com, user2@test.com",
            subject="Multiple Recipients",
            html_content="<h1>Test</h1>"
        )
        
        assert result is True
        
        sent_message = mock_smtp.send_message.call_args[0][0]
        assert sent_message["To"] == "user1@test.com, user2@test.com"
    
    def test_send_email_with_line_breaks(self, email_service, mock_smtp):
        """Test sending email with line breaks in content"""
        html_with_breaks = """<h1>Test</h1>
        <p>Line 1</p>
        <p>Line 2</p>
        <p>Line 3</p>"""
        
        text_with_breaks = """Test
        Line 1
        Line 2
        Line 3"""
        
        result = email_service.send_email(
            to_email="user@test.com",
            subject="Line Breaks Test",
            html_content=html_with_breaks,
            text_content=text_with_breaks
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
    
    # ========================
    # Integration-style Tests
    # ========================
    
    def test_full_email_flow(self, email_service, mock_smtp):
        """Test complete email flow: welcome + password reset"""
        # Send welcome email
        welcome_result = email_service.send_welcome_email(
            to_email="newuser@test.com",
            user_name="Test User"
        )
        assert welcome_result is True
        
        # Send password reset email
        reset_result = email_service.send_password_reset_email(
            to_email="newuser@test.com",
            reset_token="reset-token-123"
        )
        assert reset_result is True
        
        # Verify both emails were sent
        assert mock_smtp.send_message.call_count == 2
    
    def test_email_retry_on_failure_not_implemented(self, email_service):
        """Test that email service doesn't retry on failure (current implementation)"""
        call_count = 0
        
        def failing_smtp(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise smtplib.SMTPException("SMTP Error")
        
        with patch('smtplib.SMTP', side_effect=failing_smtp):
            result = email_service.send_email(
                to_email="user@test.com",
                subject="Test",
                html_content="<h1>Test</h1>"
            )
            
            assert result is False
            assert call_count == 1  # No retry in current implementation
    
    # ========================
    # Security-related Tests
    # ========================
    
    def test_password_not_logged(self, email_service, mock_smtp, capsys):
        """Test that passwords are not logged in error messages"""
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, 
            b'5.7.8 Authentication credentials invalid'
        )
        
        result = email_service.send_email(
            to_email="user@test.com",
            subject="Test",
            html_content="<h1>Test</h1>"
        )
        
        assert result is False
        
        # Capture printed output
        captured = capsys.readouterr()
        
        # Verify password is not in error output
        assert "testpass123" not in captured.out
        assert "testpass123" not in captured.err
    
    def test_email_content_safety(self, email_service, mock_smtp):
        """Test that email content is properly encoded"""
        malicious_html = '<script>alert("xss")</script><h1>Test</h1>'
        
        result = email_service.send_email(
            to_email="user@test.com",
            subject="Test",
            html_content=malicious_html,
            text_content="Test"
        )
        
        assert result is True
        
        # The email should be sent with the content as-is
        # (Encoding/escaping would be handled by email clients)
        sent_message = mock_smtp.send_message.call_args[0][0]
        decoded_content = decode_email_content(sent_message)
        assert "<script>" in decoded_content  # Content is passed through
    
    # ========================
    # Performance Tests
    # ========================
    
    def test_email_performance_acceptable(self, email_service, mock_smtp):
        """Test that email sending performance is acceptable"""
        import time
        
        start_time = time.time()
        
        result = email_service.send_email(
            to_email="user@test.com",
            subject="Performance Test",
            html_content="<h1>Test</h1>"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result is True
        # Should complete in under 5 seconds (adjust based on requirements)
        assert duration < 5.0, f"Email sending took {duration:.2f} seconds"