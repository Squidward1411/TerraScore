"""
Parcel API endpoints
Manage farm parcels (create, read, update, delete)
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import shape, mapping
import json

from app.db.base import get_db
from app.models.parcel import Parcel
from app.schemas.parcel import (
    ParcelCreate,
    ParcelUpdate,
    ParcelResponse,
    ParcelSimple,
    ParcelListResponse,
    ParcelHealthStatus,
    ParcelRiskSummary
)
from app.core.security import get_current_user_token

router = APIRouter()


@router.post("/", response_model=ParcelResponse, status_code=status.HTTP_201_CREATED)
async def create_parcel(
    parcel_data: ParcelCreate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Create a new parcel

    **Required fields:**
    - cadastral_id: Official cadastral identification number
    - geometry: GeoJSON polygon geometry (WGS84 coordinates)
    - area_hectares: Parcel area in hectares

    **Optional fields:**
    - parcel_name: Friendly name for the parcel
    - owner_name: Parcel owner name
    - current_crop_type: Current crop (maize, wheat, etc.)
    - soil_type: Soil classification
    - has_irrigation: Whether parcel has irrigation
    """
    # Check if cadastral_id already exists
    existing = db.query(Parcel).filter(
        Parcel.cadastral_id == parcel_data.cadastral_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parcel with cadastral_id {parcel_data.cadastral_id} already exists"
        )

    # Convert GeoJSON to WKT for PostGIS
    geom_shape = shape(parcel_data.geometry)
    wkt_geom = f"SRID=4326;{geom_shape.wkt}"

    # Calculate centroid
    centroid = geom_shape.centroid
    wkt_centroid = f"SRID=4326;{centroid.wkt}"

    # Create parcel
    parcel = Parcel(
        cadastral_id=parcel_data.cadastral_id,
        parcel_name=parcel_data.parcel_name,
        area_hectares=parcel_data.area_hectares,
        current_crop_type=parcel_data.current_crop_type,
        geometry=wkt_geom,
        centroid=wkt_centroid,
        owner_name=parcel_data.owner_name,
        address=parcel_data.address,
        municipality=parcel_data.municipality,
        soil_type=parcel_data.soil_type,
        has_irrigation=parcel_data.has_irrigation,
        planting_date=parcel_data.planting_date,
        is_active=True,
        monitored_by_user_id=current_user["sub"]
    )

    db.add(parcel)
    db.commit()
    db.refresh(parcel)

    # Convert geometry back to GeoJSON for response
    parcel_geom = to_shape(parcel.geometry)

    return ParcelResponse(
        **parcel.__dict__,
        geometry=mapping(parcel_geom)
    )


@router.get("/", response_model=ParcelListResponse)
async def list_parcels(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    crop_type: Optional[str] = Query(None, description="Filter by crop type"),
    municipality: Optional[str] = Query(None, description="Filter by municipality"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in cadastral_id or parcel_name"),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    List all parcels with pagination and filters

    Supports filtering by:
    - Crop type
    - Municipality
    - Active status
    - Search by cadastral ID or name
    """
    # Build query
    query = db.query(Parcel)

    # Apply filters
    if crop_type:
        query = query.filter(Parcel.current_crop_type == crop_type)

    if municipality:
        query = query.filter(Parcel.municipality == municipality)

    if is_active is not None:
        query = query.filter(Parcel.is_active == is_active)

    if search:
        search_filter = or_(
            Parcel.cadastral_id.ilike(f"%{search}%"),
            Parcel.parcel_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    parcels = query.order_by(Parcel.created_at.desc()).offset(offset).limit(page_size).all()

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    return ParcelListResponse(
        items=parcels,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{parcel_id}", response_model=ParcelResponse)
async def get_parcel(
    parcel_id: UUID,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific parcel

    Returns all parcel data including:
    - Geometry (GeoJSON)
    - Physical characteristics
    - Soil information
    - Current crop details
    - Historical yields
    - Current health metrics
    """
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID {parcel_id} not found"
        )

    # Convert geometry to GeoJSON
    parcel_geom = to_shape(parcel.geometry)

    return ParcelResponse(
        **parcel.__dict__,
        geometry=mapping(parcel_geom)
    )


@router.put("/{parcel_id}", response_model=ParcelResponse)
async def update_parcel(
    parcel_id: UUID,
    parcel_data: ParcelUpdate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Update parcel information

    Can update:
    - Parcel name
    - Current crop type
    - Planting/harvest dates
    - Owner information
    - Active status
    """
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID {parcel_id} not found"
        )

    # Update fields
    update_data = parcel_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(parcel, field, value)

    db.commit()
    db.refresh(parcel)

    # Convert geometry to GeoJSON
    parcel_geom = to_shape(parcel.geometry)

    return ParcelResponse(
        **parcel.__dict__,
        geometry=mapping(parcel_geom)
    )


@router.delete("/{parcel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parcel(
    parcel_id: UUID,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Delete a parcel (soft delete - sets is_active to False)

    Note: This does not permanently delete the parcel from the database,
    but marks it as inactive to preserve historical data
    """
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID {parcel_id} not found"
        )

    # Soft delete
    parcel.is_active = False
    db.commit()

    return None


@router.get("/{parcel_id}/health", response_model=ParcelHealthStatus)
async def get_parcel_health(
    parcel_id: UUID,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get current health status for a parcel

    Returns:
    - Current NDVI and EVI values
    - Overall health score (0-100)
    - Health trend (IMPROVING, STABLE, DECLINING)
    - Comparison to regional average
    """
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID {parcel_id} not found"
        )

    # Calculate health trend (simplified - would use historical data in production)
    health_trend = "STABLE"  # Default
    if parcel.current_ndvi:
        if parcel.current_ndvi > 0.7:
            health_trend = "IMPROVING"
        elif parcel.current_ndvi < 0.4:
            health_trend = "DECLINING"

    # Calculate regional average comparison (mock data)
    regional_avg_ndvi = 0.65
    comparison = ((parcel.current_ndvi or 0.5) - regional_avg_ndvi) / regional_avg_ndvi * 100

    return ParcelHealthStatus(
        parcel_id=parcel.id,
        current_ndvi=parcel.current_ndvi,
        current_evi=parcel.current_evi,
        health_score=parcel.current_health_score or 65.0,
        health_trend=health_trend,
        last_updated=parcel.last_satellite_date or parcel.updated_at,
        comparison_to_average=round(comparison, 1)
    )


@router.get("/{parcel_id}/risks", response_model=ParcelRiskSummary)
async def get_parcel_risks(
    parcel_id: UUID,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get risk summary for a parcel

    Returns:
    - Overall risk level (LOW, MEDIUM, HIGH)
    - Individual risk probabilities
    - Active alerts count
    - Risk mitigation recommendations
    """
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID {parcel_id} not found"
        )

    # Determine overall risk
    max_risk = max(
        parcel.drought_risk or 0,
        parcel.flood_risk or 0,
        parcel.pest_risk or 0,
        parcel.disease_risk or 0
    )

    if max_risk > 0.6:
        overall_risk = "HIGH"
    elif max_risk > 0.3:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    # Generate recommendations
    recommendations = []
    if parcel.drought_risk and parcel.drought_risk > 0.5:
        recommendations.append("Consider irrigation or drought-resistant crop varieties")
    if not parcel.has_irrigation and overall_risk == "HIGH":
        recommendations.append("Install irrigation system to mitigate water stress")
    if parcel.pest_risk and parcel.pest_risk > 0.4:
        recommendations.append("Implement integrated pest management strategies")

    return ParcelRiskSummary(
        parcel_id=parcel.id,
        overall_risk=overall_risk,
        drought_risk=parcel.drought_risk or 0.0,
        flood_risk=parcel.flood_risk or 0.0,
        pest_risk=parcel.pest_risk or 0.0,
        disease_risk=parcel.disease_risk or 0.0,
        active_alerts=0,  # Would query alerts table in production
        recommendations=recommendations
    )


@router.get("/by-cadastral/{cadastral_id}", response_model=ParcelResponse)
async def get_parcel_by_cadastral_id(
    cadastral_id: str,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get parcel by cadastral ID

    Useful for integrating with cadastral systems
    """
    parcel = db.query(Parcel).filter(Parcel.cadastral_id == cadastral_id).first()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with cadastral_id {cadastral_id} not found"
        )

    # Convert geometry to GeoJSON
    parcel_geom = to_shape(parcel.geometry)

    return ParcelResponse(
        **parcel.__dict__,
        geometry=mapping(parcel_geom)
    )
