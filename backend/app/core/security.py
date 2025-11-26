"""
Security utilities for authentication and authorization
Handles JWT tokens, password hashing, and API key validation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
import secrets

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")

# HTTPBearer for API key authentication
security = HTTPBearer()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token with longer expiration

    Args:
        data: Payload data to encode in token

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Check if token has expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise credentials_exception

        return payload

    except JWTError:
        raise credentials_exception


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """
    Generate a secure random API key

    Returns:
        32-character hexadecimal API key
    """
    return secrets.token_hex(32)


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key format

    Args:
        api_key: API key to verify

    Returns:
        True if valid format, False otherwise
    """
    # Basic validation - should be 64 characters (32 bytes hex)
    return len(api_key) == 64 and all(c in "0123456789abcdef" for c in api_key.lower())


async def get_current_user_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Dependency to get current user from JWT token

    Args:
        token: JWT token from Authorization header

    Returns:
        User information from token payload

    Raises:
        HTTPException: If token is invalid
    """
    payload = verify_token(token)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    return payload


async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Dependency to extract and validate API key from request

    Args:
        credentials: HTTP authorization credentials

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    api_key = credentials.credentials

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )

    return api_key


def has_permission(user_permissions: list, required_permission: str) -> bool:
    """
    Check if user has required permission

    Args:
        user_permissions: List of user's permissions
        required_permission: Permission required for action

    Returns:
        True if user has permission, False otherwise
    """
    return required_permission in user_permissions or "admin" in user_permissions


class PermissionChecker:
    """Dependency class for checking user permissions"""

    def __init__(self, required_permissions: list):
        self.required_permissions = required_permissions

    async def __call__(self, current_user: Dict = Depends(get_current_user_token)):
        user_permissions = current_user.get("permissions", [])

        for permission in self.required_permissions:
            if not has_permission(user_permissions, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )

        return current_user
