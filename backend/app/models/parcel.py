"""
Parcel model for farm land parcels
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import uuid

from app.db.base import Base


class Parcel(Base):
    """
    Farm parcel model with geospatial data
    Represents a single farm field/parcel
    """
    __tablename__ = "parcels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Identification
    cadastral_id = Column(String(100), unique=True, index=True, nullable=False)  # Official cadastral number
    parcel_name = Column(String(255), nullable=True)  # Optional friendly name

    # Owner/Farmer information
    owner_name = Column(String(255), nullable=True)
    owner_id_number = Column(String(50), nullable=True)  # Personal ID or tax number
    farmer_contact = Column(String(255), nullable=True)  # Phone or email

    # Location
    geometry = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)  # WGS84
    centroid = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    address = Column(String(500), nullable=True)
    municipality = Column(String(100), index=True, nullable=True)
    district = Column(String(100), index=True, nullable=True)
    region = Column(String(100), index=True, nullable=True)

    # Physical characteristics
    area_hectares = Column(Float, nullable=False)  # Calculated from geometry
    perimeter_meters = Column(Float, nullable=True)
    elevation_avg_meters = Column(Float, nullable=True)
    slope_avg_degrees = Column(Float, nullable=True)

    # Crop information
    current_crop_type = Column(String(100), index=True, nullable=True)  # maize, wheat, soybean, etc.
    planting_date = Column(DateTime(timezone=True), nullable=True)
    expected_harvest_date = Column(DateTime(timezone=True), nullable=True)
    crop_variety = Column(String(100), nullable=True)  # Specific variety of crop

    # Soil characteristics
    soil_type = Column(String(100), nullable=True)  # clay, loam, sandy, etc.
    soil_ph = Column(Float, nullable=True)
    soil_organic_carbon = Column(Float, nullable=True)  # Percentage
    soil_texture_class = Column(String(50), nullable=True)
    soil_drainage = Column(String(50), nullable=True)  # well-drained, poor, etc.

    # Infrastructure
    has_irrigation = Column(Boolean, default=False)
    irrigation_type = Column(String(50), nullable=True)  # drip, sprinkler, flood
    has_drainage = Column(Boolean, default=False)

    # Historical data
    historical_yields = Column(JSONB, nullable=True)  # {year: yield_tons_per_ha}
    historical_crops = Column(JSONB, nullable=True)   # {year: crop_type}

    # Current monitoring data (cached for performance)
    current_ndvi = Column(Float, nullable=True)
    current_evi = Column(Float, nullable=True)
    last_satellite_date = Column(DateTime(timezone=True), nullable=True)
    current_health_score = Column(Float, nullable=True)  # 0-100 scale

    # Risk indicators
    drought_risk = Column(Float, nullable=True)  # 0-1 probability
    flood_risk = Column(Float, nullable=True)
    pest_risk = Column(Float, nullable=True)
    disease_risk = Column(Float, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)  # Currently monitored
    is_insured = Column(Boolean, default=False)
    has_active_loan = Column(Boolean, default=False)

    # User association
    monitored_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    data_source = Column(String(100), nullable=True)  # cadastre, user_upload, etc.
    notes = Column(Text, nullable=True)

    # Additional attributes as JSON
    extra_attributes = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<Parcel {self.cadastral_id} ({self.area_hectares:.2f} ha)>"

    @property
    def area_acres(self) -> float:
        """Convert hectares to acres"""
        return self.area_hectares * 2.47105

    @property
    def latest_yield(self) -> float:
        """Get most recent historical yield"""
        if not self.historical_yields:
            return None
        years = sorted(self.historical_yields.keys(), reverse=True)
        return self.historical_yields.get(years[0]) if years else None
