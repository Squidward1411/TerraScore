"""
Credit Score Calculation Service
Core business logic for calculating agricultural credit scores
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session

from app.models.parcel import Parcel
from app.models.credit_score import CreditScore
from app.schemas.credit_score import CreditScoreComponents


class CreditScoreCalculator:
    """
    Calculate credit scores for agricultural parcels
    Combines crop health, weather risk, soil quality, and historical performance
    """

    # Component weights (must sum to 1.0)
    WEIGHTS = {
        "crop_health": 0.40,
        "weather_risk": 0.30,
        "soil_quality": 0.15,
        "historical": 0.15,
    }

    # Risk category thresholds
    RISK_THRESHOLDS = {
        "HIGH": (0, 50),
        "MEDIUM": (50, 70),
        "LOW": (70, 100),
    }

    def __init__(self, db: Session):
        self.db = db

    def calculate_credit_score(
        self,
        parcel: Parcel,
        force_recalculate: bool = False
    ) -> CreditScore:
        """
        Calculate comprehensive credit score for a parcel

        Args:
            parcel: Parcel model instance
            force_recalculate: Force recalculation even if recent score exists

        Returns:
            CreditScore model instance
        """
        start_time = datetime.now()

        # Check for recent score (within last 24 hours)
        if not force_recalculate:
            recent_score = self._get_recent_score(parcel.id)
            if recent_score:
                return recent_score

        # Calculate component scores
        crop_health_score = self._calculate_crop_health_score(parcel)
        weather_risk_score = self._calculate_weather_risk_score(parcel)
        soil_quality_score = self._calculate_soil_quality_score(parcel)
        historical_score = self._calculate_historical_performance_score(parcel)

        # Calculate weighted overall score
        overall_score = (
            crop_health_score * self.WEIGHTS["crop_health"] +
            weather_risk_score * self.WEIGHTS["weather_risk"] +
            soil_quality_score * self.WEIGHTS["soil_quality"] +
            historical_score * self.WEIGHTS["historical"]
        )

        # Determine risk category
        risk_category = self._categorize_risk(overall_score)

        # Calculate confidence level
        confidence_level, data_quality = self._calculate_confidence(parcel)

        # Get previous score for comparison
        previous_score_obj = self._get_previous_score(parcel.id)
        previous_score = previous_score_obj.score if previous_score_obj else None
        score_change = overall_score - previous_score if previous_score else None

        # Calculate yield prediction
        yield_pred = self._predict_yield(parcel)

        # Calculate loan recommendations
        loan_amount = self._calculate_recommended_loan(overall_score, parcel.area_hectares)
        interest_adjustment = self._calculate_interest_adjustment(overall_score, risk_category)

        # Identify active risk factors
        active_risks = self._identify_risk_factors(parcel)

        # Create credit score record
        credit_score = CreditScore(
            parcel_id=parcel.id,
            score=round(overall_score, 1),
            risk_category=risk_category,
            crop_health_score=round(crop_health_score, 1),
            weather_risk_score=round(weather_risk_score, 1),
            soil_quality_score=round(soil_quality_score, 1),
            historical_performance_score=round(historical_score, 1),
            weights=self.WEIGHTS,
            confidence_level=confidence_level,
            data_quality_score=data_quality,
            previous_score=previous_score,
            score_change=score_change,
            # NDVI metrics
            ndvi_current=parcel.current_ndvi,
            # Yield prediction
            predicted_yield_tons_per_ha=yield_pred["predicted"] if yield_pred else None,
            yield_prediction_confidence=yield_pred["confidence"] if yield_pred else None,
            yield_prediction_lower_bound=yield_pred["lower_bound"] if yield_pred else None,
            yield_prediction_upper_bound=yield_pred["upper_bound"] if yield_pred else None,
            # Loan recommendations
            recommended_loan_amount=loan_amount,
            suggested_interest_rate_adjustment=interest_adjustment,
            max_loan_to_value_ratio=self._calculate_ltv_ratio(overall_score),
            # Risk factors
            active_risk_factors=active_risks,
            # Metadata
            model_version="1.0.0",
            calculation_method="weighted_component_scoring",
            calculation_duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            calculated_at=datetime.now(),
        )

        # Save to database
        self.db.add(credit_score)
        self.db.commit()
        self.db.refresh(credit_score)

        # Update parcel cached health score
        parcel.current_health_score = crop_health_score
        self.db.commit()

        return credit_score

    def _calculate_crop_health_score(self, parcel: Parcel) -> float:
        """
        Calculate crop health score based on NDVI and vegetation indices

        Higher NDVI = healthier crop = higher score
        Score range: 0-100
        """
        if not parcel.current_ndvi:
            return 50.0  # Default neutral score if no data

        ndvi = parcel.current_ndvi

        # NDVI typically ranges from 0.2 (bare soil) to 0.9 (dense vegetation)
        # For crops, healthy range is 0.5-0.8
        if ndvi >= 0.7:
            base_score = 90 + (ndvi - 0.7) * 50  # 90-100 for excellent health
        elif ndvi >= 0.5:
            base_score = 70 + (ndvi - 0.5) * 100  # 70-90 for good health
        elif ndvi >= 0.3:
            base_score = 40 + (ndvi - 0.3) * 150  # 40-70 for moderate health
        else:
            base_score = ndvi * 133  # 0-40 for poor health

        # Adjust based on EVI if available
        if parcel.current_evi:
            evi_adjustment = (parcel.current_evi - 0.3) * 20
            base_score += evi_adjustment

        return np.clip(base_score, 0, 100)

    def _calculate_weather_risk_score(self, parcel: Parcel) -> float:
        """
        Calculate weather risk score
        Lower risk = higher score

        Considers:
        - Drought risk
        - Flood risk
        - Temperature extremes
        """
        risk_score = 100.0  # Start with perfect score

        # Deduct for drought risk
        if parcel.drought_risk:
            risk_score -= parcel.drought_risk * 50  # Up to -50 points

        # Deduct for flood risk
        if parcel.flood_risk:
            risk_score -= parcel.flood_risk * 30  # Up to -30 points

        return np.clip(risk_score, 0, 100)

    def _calculate_soil_quality_score(self, parcel: Parcel) -> float:
        """
        Calculate soil quality score based on soil characteristics

        Considers:
        - Soil type suitability for crop
        - Soil pH
        - Organic carbon content
        - Drainage
        """
        if not parcel.soil_type:
            return 60.0  # Default if no soil data

        base_score = 70.0  # Start with average

        # Adjust for soil pH (optimal range 6.0-7.5 for most crops)
        if parcel.soil_ph:
            if 6.0 <= parcel.soil_ph <= 7.5:
                ph_adjustment = 15
            elif 5.5 <= parcel.soil_ph < 6.0 or 7.5 < parcel.soil_ph <= 8.0:
                ph_adjustment = 5
            else:
                ph_adjustment = -10
            base_score += ph_adjustment

        # Adjust for organic carbon (higher is better)
        if parcel.soil_organic_carbon:
            if parcel.soil_organic_carbon >= 2.0:
                oc_adjustment = 15
            elif parcel.soil_organic_carbon >= 1.0:
                oc_adjustment = 10
            else:
                oc_adjustment = 0
            base_score += oc_adjustment

        # Bonus for good drainage
        if parcel.soil_drainage == "well-drained":
            base_score += 5

        return np.clip(base_score, 0, 100)

    def _calculate_historical_performance_score(self, parcel: Parcel) -> float:
        """
        Calculate score based on historical yield performance

        More stable yields = higher score
        """
        if not parcel.historical_yields or len(parcel.historical_yields) < 2:
            return 65.0  # Default for insufficient history

        yields = list(parcel.historical_yields.values())

        # Calculate coefficient of variation (CV)
        mean_yield = np.mean(yields)
        std_yield = np.std(yields)
        cv = std_yield / mean_yield if mean_yield > 0 else 1.0

        # Lower CV = more stable = higher score
        # CV < 0.1: excellent stability (90-100)
        # CV 0.1-0.2: good stability (70-90)
        # CV 0.2-0.3: moderate stability (50-70)
        # CV > 0.3: poor stability (0-50)
        if cv < 0.1:
            score = 90 + (0.1 - cv) * 100
        elif cv < 0.2:
            score = 70 + (0.2 - cv) * 200
        elif cv < 0.3:
            score = 50 + (0.3 - cv) * 200
        else:
            score = 50 - (cv - 0.3) * 100

        return np.clip(score, 0, 100)

    def _categorize_risk(self, score: float) -> str:
        """Categorize risk level based on score"""
        for category, (min_score, max_score) in self.RISK_THRESHOLDS.items():
            if min_score <= score < max_score:
                return category
        return "LOW"  # Default for scores >= 70

    def _calculate_confidence(self, parcel: Parcel) -> Tuple[str, float]:
        """
        Calculate confidence level in the score

        Returns:
            Tuple of (confidence_level, data_quality_score)
        """
        data_points = 0
        max_points = 10

        # Check data availability
        if parcel.current_ndvi is not None:
            data_points += 2
        if parcel.soil_type:
            data_points += 1
        if parcel.soil_ph is not None:
            data_points += 1
        if parcel.historical_yields and len(parcel.historical_yields) >= 3:
            data_points += 2
        if parcel.last_satellite_date and \
           (datetime.now() - parcel.last_satellite_date).days < 7:
            data_points += 2
        if parcel.drought_risk is not None:
            data_points += 1
        if parcel.elevation_avg_meters is not None:
            data_points += 1

        data_quality = (data_points / max_points) * 100

        if data_quality >= 80:
            confidence = "HIGH"
        elif data_quality >= 60:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return confidence, data_quality

    def _predict_yield(self, parcel: Parcel) -> Optional[Dict]:
        """
        Predict crop yield (simplified version)
        In production, this would use the ML model
        """
        if not parcel.current_ndvi or not parcel.current_crop_type:
            return None

        # Simplified yield prediction based on NDVI
        # Real implementation would use trained XGBoost model
        base_yield = 8.0  # Average maize yield in tons/ha

        # Adjust based on NDVI
        ndvi_factor = parcel.current_ndvi / 0.7  # 0.7 is optimal NDVI
        predicted_yield = base_yield * ndvi_factor

        # Confidence decreases with deviation from optimal
        confidence = 1.0 - abs(parcel.current_ndvi - 0.7) * 2

        return {
            "predicted": round(predicted_yield, 2),
            "confidence": np.clip(confidence, 0.3, 1.0),
            "lower_bound": round(predicted_yield * 0.85, 2),
            "upper_bound": round(predicted_yield * 1.15, 2),
        }

    def _calculate_recommended_loan(self, score: float, area_ha: float) -> float:
        """
        Calculate recommended loan amount based on score and parcel size

        Formula: Base amount per hectare * area * score factor
        """
        base_per_hectare = 3000  # EUR per hectare

        # Score factor: 0.5 to 1.5
        score_factor = 0.5 + (score / 100)

        loan_amount = base_per_hectare * area_ha * score_factor

        return round(loan_amount, 2)

    def _calculate_interest_adjustment(self, score: float, risk_category: str) -> float:
        """
        Calculate suggested interest rate adjustment

        Returns:
            Adjustment in percentage points (e.g., -0.5 for 0.5% reduction)
        """
        if risk_category == "LOW":
            return -0.5  # Reduce rate by 0.5%
        elif risk_category == "MEDIUM":
            return 0.0  # No adjustment
        else:
            return 1.0  # Increase rate by 1%

    def _calculate_ltv_ratio(self, score: float) -> float:
        """
        Calculate maximum loan-to-value ratio

        Higher score = higher LTV allowed
        """
        # LTV range: 40% to 80%
        ltv = 40 + (score / 100) * 40
        return round(ltv, 1)

    def _identify_risk_factors(self, parcel: Parcel) -> list:
        """Identify active risk factors for the parcel"""
        risks = []

        if parcel.current_ndvi and parcel.current_ndvi < 0.4:
            risks.append("LOW_CROP_HEALTH")

        if parcel.drought_risk and parcel.drought_risk > 0.6:
            risks.append("HIGH_DROUGHT_RISK")

        if parcel.flood_risk and parcel.flood_risk > 0.5:
            risks.append("FLOOD_RISK")

        if not parcel.has_irrigation and parcel.drought_risk and parcel.drought_risk > 0.4:
            risks.append("NO_IRRIGATION_INFRASTRUCTURE")

        return risks

    def _get_recent_score(self, parcel_id) -> Optional[CreditScore]:
        """Get most recent credit score if calculated within last 24 hours"""
        cutoff = datetime.now() - timedelta(hours=24)

        return (
            self.db.query(CreditScore)
            .filter(
                CreditScore.parcel_id == parcel_id,
                CreditScore.calculated_at >= cutoff
            )
            .order_by(CreditScore.calculated_at.desc())
            .first()
        )

    def _get_previous_score(self, parcel_id) -> Optional[CreditScore]:
        """Get previous credit score for comparison"""
        return (
            self.db.query(CreditScore)
            .filter(CreditScore.parcel_id == parcel_id)
            .order_by(CreditScore.calculated_at.desc())
            .offset(1)
            .first()
        )
