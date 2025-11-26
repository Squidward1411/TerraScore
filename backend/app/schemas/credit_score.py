"""
Pydantic schemas for CreditScore model
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class CreditScoreComponents(BaseModel):
    """Component scores breakdown"""
    crop_health: float = Field(..., ge=0, le=100)
    weather_risk: float = Field(..., ge=0, le=100)
    soil_quality: float = Field(..., ge=0, le=100)
    historical: float = Field(..., ge=0, le=100)


class YieldPrediction(BaseModel):
    """Yield prediction data"""
    predicted_yield_tons_per_ha: float
    confidence: float = Field(..., ge=0, le=1)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class LoanRecommendation(BaseModel):
    """Loan recommendation data"""
    recommended_amount: float
    suggested_interest_adjustment: float
    max_loan_to_value_ratio: float


class CreditScoreBase(BaseModel):
    """Base credit score schema"""
    score: float = Field(..., ge=0, le=100, description="Overall credit score (0-100)")
    risk_category: str = Field(..., description="Risk category: LOW, MEDIUM, HIGH")
    confidence_level: str = Field(..., description="Confidence level: HIGH, MEDIUM, LOW")


class CreditScoreCreate(BaseModel):
    """Schema for creating credit score"""
    parcel_id: UUID
    score: float
    risk_category: str
    crop_health_score: float
    weather_risk_score: float
    soil_quality_score: float
    historical_performance_score: float
    confidence_level: str

    # Optional detailed data
    predicted_yield_tons_per_ha: Optional[float] = None
    recommended_loan_amount: Optional[float] = None
    active_risk_factors: Optional[List[str]] = None


class CreditScoreResponse(CreditScoreBase):
    """Detailed credit score response"""
    id: UUID
    parcel_id: UUID

    # Component scores
    components: CreditScoreComponents

    # Yield prediction
    yield_prediction: Optional[YieldPrediction] = None

    # Loan recommendation
    loan_recommendation: Optional[LoanRecommendation] = None

    # Risk factors
    active_risk_factors: Optional[List[str]] = None

    # NDVI metrics
    ndvi_current: Optional[float] = None
    ndvi_30day_avg: Optional[float] = None
    ndvi_seasonal_deviation: Optional[float] = None

    # Weather metrics
    drought_probability: Optional[float] = None
    frost_risk: Optional[float] = None

    # Metadata
    calculated_at: datetime
    model_version: Optional[str] = None
    data_quality_score: Optional[float] = None

    # Comparison
    previous_score: Optional[float] = None
    score_change: Optional[float] = None

    class Config:
        from_attributes = True


class CreditScoreSimple(BaseModel):
    """Simplified credit score for list views"""
    id: UUID
    parcel_id: UUID
    score: float
    risk_category: str
    confidence_level: str
    calculated_at: datetime

    class Config:
        from_attributes = True


class BatchCreditScoreRequest(BaseModel):
    """Request for batch credit score calculation"""
    parcel_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    include_details: bool = True
    force_recalculate: bool = False


class BatchCreditScoreResponse(BaseModel):
    """Response for batch credit scores"""
    results: List[CreditScoreResponse]
    total: int
    successful: int
    failed: int
    errors: Optional[Dict[str, str]] = None
