from src.db import get_conn
from psycopg.rows import dict_row
from datetime import datetime, timedelta
import re
import hashlib
import secrets


class AuthService:
    """Service for authentication and user management"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using SHA-256 with salt.
        In production, use bcrypt or argon2!
        """
        salt = secrets.token_hex(32)
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}${hashed.hex()}"

    @staticmethod
    def verify_password(stored_hash: str, provided_password: str) -> bool:
        """
        Verify password against stored hash.
        Stored hash format: salt$hash
        """
        try:
            salt, hash_hex = stored_hash.split('$')
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return hashed.hex() == hash_hex
        except Exception as e:
            print(f"ERROR verifying password: {str(e)}")
            return False

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and normalize email address"""
        if not email or len(email.strip()) == 0:
            raise ValueError("Email is required")
        
        email = email.strip().lower()
        
        # Basic email regex validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 255:
            raise ValueError("Email must be 255 characters or less")
        
        return email

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Validate password strength.
        Requirements:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        """
        if not password:
            raise ValueError("Password is required")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        
        return password

    @staticmethod
    def validate_student_id(student_id: str) -> str:
        """
        Validate student ID format.
        Format: __XXX_____ (numbers and letters)
        Example: 12ABC34567
        """
        if not student_id or len(student_id.strip()) == 0:
            raise ValueError("Student ID is required")
        
        student_id = student_id.strip().upper()
        
        # Check length (10 characters)
        if len(student_id) != 10:
            raise ValueError("Student ID must be exactly 10 characters long")
        
        # Validate format: __XXX_____ (2 digits, 3 letters, 5 digits)
        pattern = r'^[0-9]{2}[A-Z]{3}[0-9]{5}$'
        if not re.match(pattern, student_id):
            raise ValueError("Student ID format must be: 2 digits + 3 letters + 5 digits (e.g., 12ABC34567)")
        
        return student_id

    def user_exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        try:
            email = email.strip().lower()
            sql = "SELECT id FROM \"user\" WHERE LOWER(user_email) = LOWER(%s) LIMIT 1;"
            
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (email,))
                    return cur.fetchone() is not None
        except Exception as e:
            print(f"ERROR checking if user exists: {str(e)}")
            return False

    def student_id_exists(self, student_id: str) -> bool:
        """Check if student ID already exists"""
        try:
            student_id = student_id.strip().upper()
            sql = "SELECT id FROM \"user\" WHERE UPPER(student_id) = UPPER(%s) LIMIT 1;"
            
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (student_id,))
                    return cur.fetchone() is not None
        except Exception as e:
            print(f"ERROR checking if student ID exists: {str(e)}")
            return False

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate user with email and password.
        Returns user data if successful.
        """
        print(f"🔍 login called with email: {email}")
        
        try:
            # Validate inputs
            email = self.validate_email(email)
            
            if not password:
                raise ValueError("Password is required")
            
            # Get user by email
            sql = """
                SELECT id, user_email, user_password, user_role, created_at
                FROM "user"
                WHERE LOWER(user_email) = LOWER(%s)
                LIMIT 1;
            """
            
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (email,))
                    user = cur.fetchone()
            
            if not user:
                print(f"❌ User not found: {email}")
                raise ValueError("Invalid email or password")
            
            # Verify password
            if not self.verify_password(user['user_password'], password):
                print(f"❌ Invalid password for user: {email}")
                raise ValueError("Invalid email or password")
            
            print(f"✅ User authenticated: {email}")
            
            return {
                "id": user["id"],
                "email": user["user_email"],
                "role": user["user_role"],
                "created_at": user["created_at"]
            }
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ ERROR in login: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError("Authentication failed. Please try again.")

    def register(self, email: str, password: str, role: str = "student", student_id: str = None) -> dict:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            role: User role (student, teacher, admin) - defaults to student
            student_id: Student ID (required for student role)
        
        Returns:
            User data dictionary
        """
        print(f"🔍 register called with email: {email}, role: {role}")
        
        try:
            # Validate inputs
            email = self.validate_email(email)
            password = self.validate_password(password)
            
            valid_roles = ["student", "teacher"]
            if role not in valid_roles:
                raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
            
            # Validate student ID for student role
            if role == "student":
                if not student_id:
                    raise ValueError("Student ID is required for student registration")
                student_id = self.validate_student_id(student_id)
                
                # Check if student ID already exists
                if self.student_id_exists(student_id):
                    raise ValueError(f"Student ID '{student_id}' is already registered")
            
            # Check if user already exists
            if self.user_exists_by_email(email):
                raise ValueError(f"User with email '{email}' already exists")
            
            # Hash password
            hashed_password = self.hash_password(password)
            
            # Insert user
            if role == "student":
                sql = """
                    INSERT INTO "user" (user_email, user_password, user_role, student_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id, user_email, user_role, student_id, created_at;
                """
                with get_conn() as conn:
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(sql, (email, hashed_password, role, student_id))
                        user = cur.fetchone()
            else:
                sql = """
                    INSERT INTO "user" (user_email, user_password, user_role, created_at)
                    VALUES (%s, %s, %s, NOW())
                    RETURNING id, user_email, user_role, created_at;
                """
                with get_conn() as conn:
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(sql, (email, hashed_password, role))
                        user = cur.fetchone()
            
            print(f"✅ User registered: {email} with role: {role}")
            
            result = {
                "id": user["id"],
                "email": user["user_email"],
                "role": user["user_role"],
                "created_at": user["created_at"]
            }
            
            if role == "student":
                result["student_id"] = user["student_id"]
            
            return result
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ ERROR in register: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError("Registration failed. Please try again.")

    def request_password_reset(self, email: str) -> dict:
        """
        Request password reset by email.
        Generates reset token and stores it in database.
        
        Returns token that should be sent via email to user.
        """
        print(f"🔍 request_password_reset called with email: {email}")
        
        try:
            email = self.validate_email(email)
            
            # Check if user exists
            if not self.user_exists_by_email(email):
                # For security, don't reveal if email exists
                # Still return success message
                print(f"⚠️ Email not found (not revealing for security): {email}")
                return {
                    "message": "If an account exists with this email, a password reset link will be sent"
                }
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
            
            # Token expires in 24 hours
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Store reset token in database
            sql = """
                UPDATE "user"
                SET password_reset_token = %s, password_reset_expires = %s
                WHERE LOWER(user_email) = LOWER(%s)
                RETURNING id, user_email;
            """
            
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (reset_token_hash, expires_at, email))
                    user = cur.fetchone()
            
            if not user:
                print(f"❌ User not found: {email}")
                return {
                    "message": "If an account exists with this email, a password reset link will be sent"
                }
            
            print(f"✅ Password reset requested for: {email}")
            
            return {
                "message": "If an account exists with this email, a password reset link will be sent",
                "reset_token": reset_token,  # Return token for API usage
                "user_id": user["id"]
            }
            
        except ValueError as e:
            print(f"⚠️ Validation error: {str(e)}")
            return {
                "message": "If an account exists with this email, a password reset link will be sent"
            }
        except Exception as e:
            print(f"❌ ERROR in request_password_reset: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "message": "If an account exists with this email, a password reset link will be sent"
            }

    def reset_password(self, reset_token: str, new_password: str) -> dict:
        """
        Reset password using reset token.
        
        Args:
            reset_token: Token received via email
            new_password: New password to set
        
        Returns:
            User data with updated password
        """
        print(f"🔍 reset_password called")
        
        try:
            # Validate new password
            new_password = self.validate_password(new_password)
            
            if not reset_token or len(reset_token.strip()) == 0:
                raise ValueError("Reset token is required")
            
            # Hash the token to compare with stored hash
            reset_token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
            
            # Find user with valid reset token
            sql = """
                SELECT id, user_email, password_reset_expires
                FROM "user"
                WHERE password_reset_token = %s
                AND password_reset_expires > NOW()
                LIMIT 1;
            """
            
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (reset_token_hash,))
                    user = cur.fetchone()
            
            if not user:
                print(f"❌ Invalid or expired reset token")
                raise ValueError("Invalid or expired reset token")
            
            # Hash new password
            hashed_password = self.hash_password(new_password)
            
            # Update password and clear reset token
            sql = """
                UPDATE "user"
                SET user_password = %s, password_reset_token = NULL, password_reset_expires = NULL
                WHERE id = %s
                RETURNING id, user_email, user_role, created_at;
            """
            
            with get_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, (hashed_password, user["id"]))
                    updated_user = cur.fetchone()
            
            print(f"✅ Password reset successful for: {user['user_email']}")
            
            return {
                "id": updated_user["id"],
                "email": updated_user["user_email"],
                "role": updated_user["user_role"],
                "message": "Password reset successfully. Please login with your new password."
            }
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ ERROR in reset_password: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError("Password reset failed. Please try again.")

    def get_user_by_id(self, user_id: int) -> dict:
        """Get user information by ID"""
        if not user_id or user_id <= 0:
            raise ValueError("User ID must be a positive integer")
        
        sql = """
            SELECT id, user_email, user_role, student_id, created_at
            FROM "user"
            WHERE id = %s
            LIMIT 1;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (user_id,))
                user = cur.fetchone()
        
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        return user

    def get_user_by_email(self, email: str) -> dict:
        """Get user information by email"""
        email = self.validate_email(email)
        
        sql = """
            SELECT id, user_email, user_role, student_id, created_at
            FROM "user"
            WHERE LOWER(user_email) = LOWER(%s)
            LIMIT 1;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (email,))
                user = cur.fetchone()
        
        if not user:
            raise ValueError(f"User with email {email} not found")
        
        return user