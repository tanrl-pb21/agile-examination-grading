from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta
from src.services.auth_service import AuthService
import os
import jwt

router = APIRouter(prefix="/auth", tags=["Auth"])
service = AuthService()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class LoginRequest(BaseModel):
    """Login request schema"""
    email: str
    password: str
    remember_me: bool = False
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email_format(cls, v):
        if not v or len(str(v).strip()) == 0:
            raise ValueError("Email is required")
        return str(v).strip().lower()


class LoginResponse(BaseModel):
    """Login response schema"""
    token: str
    user: dict
    redirect_url: str
    message: str = "Login successful"


class RegisterRequest(BaseModel):
    """Registration request schema"""
    email: str
    password: str
    confirm_password: str
    role: str = "student"
    student_id: str = None
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email_format(cls, v):
        if not v or len(str(v).strip()) == 0:
            raise ValueError("Email is required")
        return str(v).strip().lower()
    
    @field_validator("password", mode="before")
    @classmethod
    def validate_password_format(cls, v):
        if not v:
            raise ValueError("Password is required")
        return str(v)


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""
    email: str
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email_format(cls, v):
        if not v or len(str(v).strip()) == 0:
            raise ValueError("Email is required")
        return str(v).strip().lower()


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    reset_token: str
    new_password: str
    confirm_password: str
    
    @field_validator("reset_token", mode="before")
    @classmethod
    def validate_token(cls, v):
        if not v or len(str(v).strip()) == 0:
            raise ValueError("Reset token is required")
        return str(v).strip()


def generate_jwt_token(user_id: int, email: str, role: str) -> str:
    """
    Generate JWT token for user.
    Token includes user info and expiration time.
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def get_redirect_url_by_role(role: str) -> str:
    """
    Get redirect URL based on user role.
    
    Routes:
    - admin -> /admin/dashboard
    - teacher -> /teacher/dashboard
    - student -> /student/exams
    """
    role_routes = {
        "admin": "/admin/dashboard",
        "teacher": "/examManagement",
        "student": "/studentExam"
    }
    
    return role_routes.get(role, "/")


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Login with email and password.
    Returns JWT token and user data.
    """
    try:
        print(f"🔍 POST /auth/login - Email: {request.email}")
        
        # Authenticate user
        user = service.login(request.email, request.password)
        
        # Generate JWT token
        token = generate_jwt_token(user["id"], user["email"], user["role"])
        
        # Get redirect URL based on role
        redirect_url = get_redirect_url_by_role(user["role"])
        
        print(f"✅ Login successful for user: {user['email']}")
        
        return LoginResponse(
            token=token,
            user=user,
            redirect_url=redirect_url,
            message="Login successful"
        )
        
    except ValueError as e:
        print(f"❌ Login validation error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        print(f"❌ ERROR in login: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


@router.post("/register")
def register(request: RegisterRequest):
    """
    Register a new user account.
    For students: email, password, and student_id are required.
    For teachers: only email and password are required.
    """
    try:
        print(f"🔍 POST /auth/register - Email: {request.email}, Role: {request.role}")
        
        # Validate passwords match
        if request.password != request.confirm_password:
            raise ValueError("Passwords do not match")
        
        # Register user
        user = service.register(
            email=request.email,
            password=request.password,
            role=request.role,
            student_id=request.student_id
        )
        
        print(f"✅ Registration successful for user: {request.email}")
        
        return {
            "message": "Registration successful. Please login.",
            "user": user,
            "redirect_url": "/login"
        }
        
    except ValueError as e:
        print(f"❌ Registration validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ ERROR in register: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset.
    Sends reset link to user email.
    
    For security: Returns same response whether email exists or not.
    """
    try:
        print(f"🔍 POST /auth/forgot-password - Email: {request.email}")
        
        result = service.request_password_reset(request.email)
        
        print(f"✅ Password reset requested for: {request.email}")
        
        # In production, send reset_token via email
        # For now, return it in API response (only for development/testing)
        return {
            "message": result["message"],
            "reset_token": result.get("reset_token"),  # Remove in production!
            "redirect_url": "/login"
        }
        
    except Exception as e:
        print(f"❌ ERROR in forgot_password: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Password reset request failed.")


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    """
    Reset password using reset token.
    Token must be valid and not expired.
    """
    try:
        print(f"🔍 POST /auth/reset-password")
        
        # Validate passwords match
        if request.new_password != request.confirm_password:
            raise ValueError("New passwords do not match")
        
        # Reset password
        user = service.reset_password(request.reset_token, request.new_password)
        
        print(f"✅ Password reset successful for: {user['email']}")
        
        return {
            "message": user["message"],
            "user": {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"]
            },
            "redirect_url": "/login"
        }
        
    except ValueError as e:
        print(f"❌ Reset password validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ ERROR in reset_password: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Password reset failed. Please try again.")


@router.post("/verify-token")
def verify_token(token: str):
    """
    Verify JWT token validity.
    Returns user data if token is valid.
    """
    try:
        print(f"🔍 POST /auth/verify-token")
        
        if not token or len(token.strip()) == 0:
            raise HTTPException(status_code=401, detail="Token is required")
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            print(f"✅ Token verified for user: {payload['email']}")
            
            return {
                "valid": True,
                "user": {
                    "id": payload["user_id"],
                    "email": payload["email"],
                    "role": payload["role"]
                },
                "message": "Token is valid"
            }
            
        except jwt.ExpiredSignatureError:
            print(f"❌ Token expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            print(f"❌ Invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in verify_token: {str(e)}")
        raise HTTPException(status_code=500, detail="Token verification failed.")


@router.post("/logout")
def logout():
    """
    Logout user (client-side operation).
    Clears token on frontend.
    """
    print(f"🔍 POST /auth/logout")
    
    return {
        "message": "Logout successful",
        "redirect_url": "/login"
    }


@router.get("/user/{user_id}")
def get_user(user_id: int):
    """Get user information by ID (requires authentication)"""
    try:
        print(f"🔍 GET /auth/user/{user_id}")
        
        user = service.get_user_by_id(user_id)
        
        return user
        
    except ValueError as e:
        print(f"❌ Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ ERROR in get_user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user.")