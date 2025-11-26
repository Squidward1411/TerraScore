"""
User model for authentication and authorization
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    BANK_USER = "bank_user"
    INSURER_USER = "insurer_user"
    GOVERNMENT_USER = "government_user"
    API_CLIENT = "api_client"


class User(Base):
    """
    User model for authentication and authorization
    Supports both interactive users and API clients
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # User profile
    full_name = Column(String(255))
    organization = Column(String(255))  # Bank name, insurance company, etc.
    phone_number = Column(String(20))

    # Role and permissions
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.BANK_USER)
    permissions = Column(ARRAY(String), default=[])  # List of specific permissions

    # API access
    api_key = Column(String(64), unique=True, index=True, nullable=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Subscription tier (for billing)
    subscription_tier = Column(String(50), default="starter")  # starter, professional, enterprise

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Notes (internal use)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def can_access_api(self) -> bool:
        """Check if user can access API"""
        return self.is_active and self.is_verified
