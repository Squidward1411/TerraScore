"""
Credit score model for storing parcel risk assessments
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class CreditScore(Base):
    """
    Credit score calculation results for parcels
    Historical records of risk assessments
    """
    __tablename__ = "credit_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relationship to parcel
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False, index=True)

    # Overall score
    score = Column(Float, nullable=False)  # 0-100 scale (higher = lower risk)
    risk_category = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH

    # Component scores
    crop_health_score = Column(Float, nullable=False)  # 0-100
    weather_risk_score = Column(Float, nullable=False)  # 0-100
    soil_quality_score = Column(Float, nullable=False)  # 0-100
    historical_performance_score = Column(Float, nullable=False)  # 0-100

    # Component weights used
    weights = Column(JSONB, nullable=True)  # Store weights for transparency

    # Detailed breakdown
    ndvi_current = Column(Float, nullable=True)
    ndvi_30day_avg = Column(Float, nullable=True)
    ndvi_seasonal_deviation = Column(Float, nullable=True)

    # Weather factors
    drought_probability = Column(Float, nullable=True)  # 0-1
    frost_risk = Column(Float, nullable=True)
    extreme_weather_score = Column(Float, nullable=True)
    cumulative_precipitation_60days = Column(Float, nullable=True)  # mm
    avg_temperature_60days = Column(Float, nullable=True)  # °C

    # Yield prediction
    predicted_yield_tons_per_ha = Column(Float, nullable=True)
    yield_prediction_confidence = Column(Float, nullable=True)  # 0-1
    yield_prediction_lower_bound = Column(Float, nullable=True)
    yield_prediction_upper_bound = Column(Float, nullable=True)

    # Loan recommendations
    recommended_loan_amount = Column(Float, nullable=True)  # EUR
    suggested_interest_rate_adjustment = Column(Float, nullable=True)  # Percentage points
    max_loan_to_value_ratio = Column(Float, nullable=True)  # Percentage

    # Confidence and data quality
    confidence_level = Column(String(20), nullable=False)  # HIGH, MEDIUM, LOW
    data_quality_score = Column(Float, nullable=True)  # 0-100
    data_completeness = Column(Float, nullable=True)  # Percentage of available data

    # Risk factors (active warnings)
    active_risk_factors = Column(JSONB, nullable=True)  # List of current risks

    # Model information
    model_version = Column(String(50), nullable=True)
    calculation_method = Column(String(100), nullable=True)

    # Calculation metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    calculated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    calculation_duration_ms = Column(Integer, nullable=True)

    # For comparison
    previous_score = Column(Float, nullable=True)
    score_change = Column(Float, nullable=True)

    # Additional data
    raw_features = Column(JSONB, nullable=True)  # Store all input features
    explanation = Column(Text, nullable=True)  # Human-readable explanation

    def __repr__(self):
        return f"<CreditScore parcel={self.parcel_id} score={self.score:.1f} ({self.risk_category})>"

    @property
    def is_high_risk(self) -> bool:
        """Check if parcel is high risk"""
        return self.risk_category == "HIGH" or self.score < 50

    @property
    def is_creditworthy(self) -> bool:
        """Check if parcel is suitable for lending"""
        return self.score >= 60 and self.confidence_level in ["HIGH", "MEDIUM"]
