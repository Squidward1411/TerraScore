"""
Pydantic schemas for User model
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    organization: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.BANK_USER
    permissions: List[str] = []

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    organization: Optional[str] = None
    phone_number: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for user in database"""
    id: UUID
    role: UserRole
    permissions: List[str]
    is_active: bool
    is_verified: bool
    is_superuser: bool
    subscription_tier: str
    api_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    """Public user schema (without sensitive data)"""
    pass


class UserWithAPIKey(User):
    """User schema with API key (only for user themselves)"""
    api_key: Optional[str] = None


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # User ID
    exp: datetime
    iat: datetime
    type: str  # access or refresh


class APIKeyResponse(BaseModel):
    """API key generation response"""
    api_key: str
    created_at: datetime
    expires_at: Optional[datetime] = None
