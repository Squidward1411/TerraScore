"""
Pydantic schemas for Parcel model
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class ParcelBase(BaseModel):
    """Base parcel schema"""
    cadastral_id: str = Field(..., min_length=1, max_length=100)
    parcel_name: Optional[str] = None
    current_crop_type: Optional[str] = None
    area_hectares: float = Field(..., gt=0)


class ParcelCreate(ParcelBase):
    """Schema for creating a new parcel"""
    geometry: Dict[str, Any]  # GeoJSON geometry
    owner_name: Optional[str] = None
    address: Optional[str] = None
    municipality: Optional[str] = None
    soil_type: Optional[str] = None
    has_irrigation: bool = False
    planting_date: Optional[datetime] = None

    @validator('geometry')
    def validate_geometry(cls, v):
        """Validate GeoJSON geometry"""
        if not isinstance(v, dict):
            raise ValueError('Geometry must be a GeoJSON object')
        if 'type' not in v or 'coordinates' not in v:
            raise ValueError('Geometry must have type and coordinates')
        if v['type'] not in ['Polygon', 'MultiPolygon']:
            raise ValueError('Geometry type must be Polygon or MultiPolygon')
        return v


class ParcelUpdate(BaseModel):
    """Schema for updating parcel"""
    parcel_name: Optional[str] = None
    current_crop_type: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    owner_name: Optional[str] = None
    has_irrigation: Optional[bool] = None
    is_active: Optional[bool] = None


class ParcelInDB(ParcelBase):
    """Schema for parcel in database"""
    id: UUID
    centroid: Optional[Dict[str, Any]] = None
    address: Optional[str] = None
    municipality: Optional[str] = None
    region: Optional[str] = None

    # Physical characteristics
    perimeter_meters: Optional[float] = None
    elevation_avg_meters: Optional[float] = None
    slope_avg_degrees: Optional[float] = None

    # Soil
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None
    soil_organic_carbon: Optional[float] = None

    # Current monitoring data
    current_ndvi: Optional[float] = None
    current_evi: Optional[float] = None
    last_satellite_date: Optional[datetime] = None
    current_health_score: Optional[float] = None

    # Risk indicators
    drought_risk: Optional[float] = None
    flood_risk: Optional[float] = None

    # Status
    is_active: bool
    has_active_loan: bool
    is_insured: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ParcelResponse(ParcelInDB):
    """Full parcel response with geometry"""
    geometry: Dict[str, Any]  # GeoJSON
    historical_yields: Optional[Dict[int, float]] = None


class ParcelSimple(BaseModel):
    """Simplified parcel for list views"""
    id: UUID
    cadastral_id: str
    parcel_name: Optional[str] = None
    area_hectares: float
    current_crop_type: Optional[str] = None
    current_health_score: Optional[float] = None
    municipality: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class ParcelListResponse(BaseModel):
    """Paginated list of parcels"""
    items: List[ParcelSimple]
    total: int
    page: int
    page_size: int
    pages: int


class ParcelHealthStatus(BaseModel):
    """Current health status of parcel"""
    parcel_id: UUID
    current_ndvi: Optional[float] = None
    current_evi: Optional[float] = None
    health_score: float = Field(..., ge=0, le=100)
    health_trend: str  # IMPROVING, STABLE, DECLINING
    last_updated: datetime
    comparison_to_average: float  # Percentage difference from regional average


class ParcelRiskSummary(BaseModel):
    """Risk summary for parcel"""
    parcel_id: UUID
    overall_risk: str  # LOW, MEDIUM, HIGH
    drought_risk: float = Field(..., ge=0, le=1)
    flood_risk: float = Field(..., ge=0, le=1)
    pest_risk: float = Field(..., ge=0, le=1)
    disease_risk: float = Field(..., ge=0, le=1)
    active_alerts: int
    recommendations: List[str]
