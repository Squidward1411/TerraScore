"""
Pydantic schemas package
"""
from app.schemas.user import (
    User,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserWithAPIKey,
    Token,
    TokenPayload,
    APIKeyResponse,
)
from app.schemas.parcel import (
    ParcelCreate,
    ParcelUpdate,
    ParcelResponse,
    ParcelSimple,
    ParcelListResponse,
    ParcelHealthStatus,
    ParcelRiskSummary,
)
from app.schemas.credit_score import (
    CreditScoreResponse,
    CreditScoreSimple,
    CreditScoreComponents,
    YieldPrediction,
    LoanRecommendation,
    BatchCreditScoreRequest,
    BatchCreditScoreResponse,
)

__all__ = [
    # User schemas
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserWithAPIKey",
    "Token",
    "TokenPayload",
    "APIKeyResponse",
    # Parcel schemas
    "ParcelCreate",
    "ParcelUpdate",
    "ParcelResponse",
    "ParcelSimple",
    "ParcelListResponse",
    "ParcelHealthStatus",
    "ParcelRiskSummary",
    # Credit score schemas
    "CreditScoreResponse",
    "CreditScoreSimple",
    "CreditScoreComponents",
    "YieldPrediction",
    "LoanRecommendation",
    "BatchCreditScoreRequest",
    "BatchCreditScoreResponse",
]
