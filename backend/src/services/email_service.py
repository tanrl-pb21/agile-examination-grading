import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "Exam Management System")
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email
            text_content: Plain text version of email (optional)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add plain text version if provided
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            print(f"✅ Email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email to {to_email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset email with reset link.
        
        Args:
            to_email: User's email address
            reset_token: Password reset token
        
        Returns:
            True if email sent successfully, False otherwise
        """
        reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #ffffff;
                }}
                .header {{
                    background: linear-gradient(135deg, #4a6cf7 0%, #3a5ce5 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 40px 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .content p {{
                    margin: 15px 0;
                    color: #1a1a2e;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 16px 40px;
                    background: linear-gradient(135deg, #4a6cf7 0%, #3a5ce5 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 15px rgba(74, 108, 247, 0.4);
                }}
                .button:hover {{
                    background: linear-gradient(135deg, #3a5ce5 0%, #2a4cd5 100%);
                }}
                .link-box {{
                    background: white;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                    word-break: break-all;
                    font-size: 14px;
                    color: #4a6cf7;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px 20px;
                    margin: 25px 0;
                    border-radius: 5px;
                }}
                .warning strong {{
                    display: block;
                    margin-bottom: 10px;
                    color: #856404;
                }}
                .warning ul {{
                    margin: 10px 0 0 0;
                    padding-left: 20px;
                    color: #856404;
                }}
                .warning li {{
                    margin: 5px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 30px;
                    color: #6c757d;
                    font-size: 13px;
                }}
                .footer p {{
                    margin: 5px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>We received a request to reset your password for your <strong>Exam Management System</strong> account.</p>
                    <p>Click the button below to reset your password:</p>
                    
                    <div class="button-container">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <div class="link-box">
                        {reset_link}
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important Security Information:</strong>
                        <ul>
                            <li>This link will expire in <strong>24 hours</strong></li>
                            <li>If you didn't request this reset, please ignore this email and your password will remain unchanged</li>
                            <li>Never share this link with anyone</li>
                            <li>Your password won't change until you create a new one</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 30px;">If you're having trouble with the button above, copy and paste the URL into your web browser.</p>
                    
                    <p style="margin-top: 20px; color: #6c757d; font-size: 14px;">
                        If you have any questions or concerns, please contact our support team.
                    </p>
                </div>
                <div class="footer">
                    <p><strong>© 2024 Exam Management System</strong></p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
Password Reset Request - Exam Management System

Hello,

We received a request to reset your password for your Exam Management System account.

Click the link below to reset your password:
{reset_link}

IMPORTANT SECURITY INFORMATION:
- This link will expire in 24 hours
- If you didn't request this reset, please ignore this email
- Never share this link with anyone
- Your password won't change until you create a new one

If you're having trouble, copy and paste the URL above into your web browser.

© 2024 Exam Management System
This is an automated message, please do not reply.
        """
        
        return self.send_email(
            to_email=to_email,
            subject="Password Reset Request - Exam Management System",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_welcome_email(self, to_email: str, user_name: str = None) -> bool:
        """
        Send welcome email to new users.
        
        Args:
            to_email: User's email address
            user_name: User's name (optional)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        greeting = f"Hello {user_name}!" if user_name else "Hello!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #ffffff;
                }}
                .header {{
                    background: linear-gradient(135deg, #4a6cf7 0%, #3a5ce5 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .footer {{
                    text-align: center;
                    padding: 30px;
                    color: #6c757d;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to Exam Management System!</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Thank you for registering with the <strong>Exam Management System</strong>.</p>
                    <p>Your account has been successfully created and you can now log in to access the platform.</p>
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                </div>
                <div class="footer">
                    <p><strong>© 2024 Exam Management System</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Welcome to Exam Management System!

{greeting}

Thank you for registering with the Exam Management System.

Your account has been successfully created and you can now log in to access the platform.

If you have any questions or need assistance, please contact our support team.

© 2024 Exam Management System
        """
        
        return self.send_email(
            to_email=to_email,
            subject="Welcome to Exam Management System!",
            html_content=html_content,
            text_content=text_content
        )