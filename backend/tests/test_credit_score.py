"""
Tests for credit score calculation
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.credit_score_calculator import CreditScoreCalculator
from app.models.parcel import Parcel


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def sample_parcel():
    """Sample parcel for testing"""
    return Parcel(
        id="test-parcel-id",
        cadastral_id="TEST123",
        area_hectares=10.5,
        current_crop_type="maize",
        current_ndvi=0.75,
        current_evi=0.65,
        soil_type="loam",
        soil_ph=6.5,
        soil_organic_carbon=2.5,
        drought_risk=0.2,
        flood_risk=0.1,
        has_irrigation=True,
        historical_yields={
            2020: 8.5,
            2021: 9.0,
            2022: 8.8,
            2023: 9.2
        }
    )


def test_calculate_crop_health_score(mock_db, sample_parcel):
    """Test crop health score calculation"""
    calculator = CreditScoreCalculator(mock_db)
    score = calculator._calculate_crop_health_score(sample_parcel)

    assert 0 <= score <= 100
    assert score > 80  # High NDVI should result in high score


def test_calculate_weather_risk_score(mock_db, sample_parcel):
    """Test weather risk score calculation"""
    calculator = CreditScoreCalculator(mock_db)
    score = calculator._calculate_weather_risk_score(sample_parcel)

    assert 0 <= score <= 100
    assert score > 70  # Low risk values should result in high score


def test_calculate_soil_quality_score(mock_db, sample_parcel):
    """Test soil quality score calculation"""
    calculator = CreditScoreCalculator(mock_db)
    score = calculator._calculate_soil_quality_score(sample_parcel)

    assert 0 <= score <= 100
    assert score > 70  # Good soil properties should result in high score


def test_calculate_historical_performance_score(mock_db, sample_parcel):
    """Test historical performance score calculation"""
    calculator = CreditScoreCalculator(mock_db)
    score = calculator._calculate_historical_performance_score(sample_parcel)

    assert 0 <= score <= 100
    # Stable yields should result in high score
    assert score > 70


def test_categorize_risk(mock_db):
    """Test risk categorization"""
    calculator = CreditScoreCalculator(mock_db)

    assert calculator._categorize_risk(80) == "LOW"
    assert calculator._categorize_risk(60) == "MEDIUM"
    assert calculator._categorize_risk(40) == "HIGH"


def test_calculate_confidence(mock_db, sample_parcel):
    """Test confidence calculation"""
    calculator = CreditScoreCalculator(mock_db)
    confidence, data_quality = calculator._calculate_confidence(sample_parcel)

    assert confidence in ["HIGH", "MEDIUM", "LOW"]
    assert 0 <= data_quality <= 100


def test_predict_yield(mock_db, sample_parcel):
    """Test yield prediction"""
    calculator = CreditScoreCalculator(mock_db)
    prediction = calculator._predict_yield(sample_parcel)

    assert prediction is not None
    assert "predicted" in prediction
    assert "confidence" in prediction
    assert prediction["predicted"] > 0
    assert 0 <= prediction["confidence"] <= 1


def test_calculate_recommended_loan(mock_db):
    """Test loan amount calculation"""
    calculator = CreditScoreCalculator(mock_db)
    loan = calculator._calculate_recommended_loan(score=75, area_ha=10)

    assert loan > 0
    assert isinstance(loan, float)


def test_identify_risk_factors(mock_db, sample_parcel):
    """Test risk factor identification"""
    calculator = CreditScoreCalculator(mock_db)
    risks = calculator._identify_risk_factors(sample_parcel)

    assert isinstance(risks, list)
    # With good parcel conditions, should have no or few risks
    assert len(risks) <= 2


@pytest.mark.parametrize("ndvi,expected_min_score", [
    (0.8, 90),
    (0.6, 70),
    (0.4, 40),
    (0.2, 20),
])
def test_crop_health_score_ranges(mock_db, sample_parcel, ndvi, expected_min_score):
    """Test crop health score calculation for various NDVI values"""
    calculator = CreditScoreCalculator(mock_db)
    sample_parcel.current_ndvi = ndvi
    score = calculator._calculate_crop_health_score(sample_parcel)

    assert score >= expected_min_score
