"""
Credit Score API endpoints
Calculate and retrieve credit scores for parcels
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.parcel import Parcel
from app.models.credit_score import CreditScore
from app.schemas.credit_score import (
    CreditScoreResponse,
    CreditScoreSimple,
    BatchCreditScoreRequest,
    BatchCreditScoreResponse
)
from app.services.credit_score_calculator import CreditScoreCalculator
from app.core.security import get_current_user_token
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/{parcel_id}", response_model=CreditScoreResponse)
async def get_credit_score(
    parcel_id: UUID,
    force_recalculate: bool = Query(False, description="Force recalculation even if recent score exists"),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get credit score for a specific parcel

    Returns the most recent credit score, or calculates a new one if:
    - No score exists
    - Score is older than 24 hours
    - force_recalculate is True

    **Response includes:**
    - Overall score (0-100)
    - Risk category (LOW, MEDIUM, HIGH)
    - Component scores breakdown
    - Yield prediction
    - Loan recommendations
    - Active risk factors
    """
    # Get parcel
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID {parcel_id} not found"
        )

    # Check if parcel is active
    if not parcel.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parcel is not active"
        )

    # Calculate or retrieve credit score
    calculator = CreditScoreCalculator(db)
    credit_score = calculator.calculate_credit_score(parcel, force_recalculate)

    # Format response
    response = CreditScoreResponse(
        id=credit_score.id,
        parcel_id=credit_score.parcel_id,
        score=credit_score.score,
        risk_category=credit_score.risk_category,
        confidence_level=credit_score.confidence_level,
        components={
            "crop_health": credit_score.crop_health_score,
            "weather_risk": credit_score.weather_risk_score,
            "soil_quality": credit_score.soil_quality_score,
            "historical": credit_score.historical_performance_score
        },
        yield_prediction={
            "predicted_yield_tons_per_ha": credit_score.predicted_yield_tons_per_ha,
            "confidence": credit_score.yield_prediction_confidence,
            "lower_bound": credit_score.yield_prediction_lower_bound,
            "upper_bound": credit_score.yield_prediction_upper_bound
        } if credit_score.predicted_yield_tons_per_ha else None,
        loan_recommendation={
            "recommended_amount": credit_score.recommended_loan_amount,
            "suggested_interest_adjustment": credit_score.suggested_interest_rate_adjustment,
            "max_loan_to_value_ratio": credit_score.max_loan_to_value_ratio
        } if credit_score.recommended_loan_amount else None,
        active_risk_factors=credit_score.active_risk_factors,
        ndvi_current=credit_score.ndvi_current,
        ndvi_30day_avg=credit_score.ndvi_30day_avg,
        ndvi_seasonal_deviation=credit_score.ndvi_seasonal_deviation,
        drought_probability=credit_score.drought_probability,
        frost_risk=credit_score.frost_risk,
        calculated_at=credit_score.calculated_at,
        model_version=credit_score.model_version,
        data_quality_score=credit_score.data_quality_score,
        previous_score=credit_score.previous_score,
        score_change=credit_score.score_change
    )

    return response


@router.get("/parcel/{parcel_id}/history", response_model=List[CreditScoreSimple])
async def get_credit_score_history(
    parcel_id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Number of historical scores to return"),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get historical credit scores for a parcel

    Returns a list of past credit score calculations ordered by most recent first
    """
    # Verify parcel exists
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID {parcel_id} not found"
        )

    # Get historical scores
    scores = (
        db.query(CreditScore)
        .filter(CreditScore.parcel_id == parcel_id)
        .order_by(CreditScore.calculated_at.desc())
        .limit(limit)
        .all()
    )

    return scores


@router.post("/batch", response_model=BatchCreditScoreResponse)
async def batch_credit_scores(
    request: BatchCreditScoreRequest,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Calculate credit scores for multiple parcels in batch

    Maximum 100 parcels per request.

    Useful for:
    - Portfolio risk assessment
    - Bulk loan processing
    - Risk monitoring of multiple properties
    """
    results = []
    errors = {}
    successful = 0
    failed = 0

    calculator = CreditScoreCalculator(db)

    for parcel_id in request.parcel_ids:
        try:
            # Get parcel
            parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

            if not parcel:
                errors[str(parcel_id)] = "Parcel not found"
                failed += 1
                continue

            if not parcel.is_active:
                errors[str(parcel_id)] = "Parcel is not active"
                failed += 1
                continue

            # Calculate credit score
            credit_score = calculator.calculate_credit_score(
                parcel,
                force_recalculate=request.force_recalculate
            )

            # Format response
            if request.include_details:
                response = CreditScoreResponse(
                    id=credit_score.id,
                    parcel_id=credit_score.parcel_id,
                    score=credit_score.score,
                    risk_category=credit_score.risk_category,
                    confidence_level=credit_score.confidence_level,
                    components={
                        "crop_health": credit_score.crop_health_score,
                        "weather_risk": credit_score.weather_risk_score,
                        "soil_quality": credit_score.soil_quality_score,
                        "historical": credit_score.historical_performance_score
                    },
                    calculated_at=credit_score.calculated_at
                )
            else:
                response = CreditScoreSimple(
                    id=credit_score.id,
                    parcel_id=credit_score.parcel_id,
                    score=credit_score.score,
                    risk_category=credit_score.risk_category,
                    confidence_level=credit_score.confidence_level,
                    calculated_at=credit_score.calculated_at
                )

            results.append(response)
            successful += 1

        except Exception as e:
            errors[str(parcel_id)] = str(e)
            failed += 1

    return BatchCreditScoreResponse(
        results=results,
        total=len(request.parcel_ids),
        successful=successful,
        failed=failed,
        errors=errors if errors else None
    )


@router.get("/{score_id}/details", response_model=CreditScoreResponse)
async def get_credit_score_details(
    score_id: UUID,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific credit score record

    Useful for viewing historical calculations
    """
    credit_score = db.query(CreditScore).filter(CreditScore.id == score_id).first()

    if not credit_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit score with ID {score_id} not found"
        )

    return credit_score
