"""
Authentication API endpoints
JWT token generation, login, registration
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User
from app.schemas.user import UserCreate, User as UserSchema, Token, APIKeyResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    generate_api_key,
    get_current_user_token
)

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    - **email**: Valid email address
    - **username**: Unique username (3-100 characters)
    - **password**: Strong password (min 8 characters, 1 digit, 1 uppercase)
    - **full_name**: Optional full name
    - **organization**: Optional organization name
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        organization=user_data.organization,
        phone_number=user_data.phone_number,
        role=user_data.role,
        permissions=user_data.permissions,
        is_active=True,
        is_verified=False,  # Requires email verification in production
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login

    Get an access token for future requests using username and password
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Update last login
    user.last_login_at = datetime.now()
    db.commit()

    # Create tokens
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "permissions": user.permissions
        }
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 86400  # 24 hours
    }


@router.post("/api-key", response_model=APIKeyResponse)
async def generate_user_api_key(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Generate API key for current user

    API keys can be used for programmatic access instead of JWT tokens
    """
    # Get user from database
    user = db.query(User).filter(User.id == current_user["sub"]).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate new API key
    api_key = generate_api_key()

    # Update user
    user.api_key = api_key
    user.api_key_created_at = datetime.now()
    db.commit()

    return {
        "api_key": api_key,
        "created_at": user.api_key_created_at,
        "expires_at": None  # API keys don't expire by default
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Refresh access token

    Use refresh token to get a new access token
    """
    # Verify it's a refresh token
    if current_user.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user
    user = db.query(User).filter(User.id == current_user["sub"]).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "permissions": user.permissions
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400
    }


@router.get("/me", response_model=UserSchema)
async def get_current_user(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get current user information

    Returns the profile of the currently authenticated user
    """
    user = db.query(User).filter(User.id == current_user["sub"]).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.post("/logout")
async def logout():
    """
    Logout (client-side token deletion)

    JWT tokens are stateless, so logout is handled client-side by deleting the token
    """
    return {"message": "Successfully logged out"}
