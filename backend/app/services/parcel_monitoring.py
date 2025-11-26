"""
Parcel Monitoring Service
Combines satellite and weather data for comprehensive parcel monitoring
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
from sqlalchemy.orm import Session

from app.models.parcel import Parcel
from app.services.satellite_service import satellite_service
from app.services.weather_service import weather_service
from geoalchemy2.shape import to_shape

logger = logging.getLogger(__name__)


class ParcelMonitoringService:
    """Service for monitoring parcel conditions"""

    async def update_parcel_data(
        self,
        db: Session,
        parcel: Parcel
    ) -> Dict:
        """
        Update parcel with latest satellite and weather data

        Args:
            db: Database session
            parcel: Parcel model instance

        Returns:
            Dictionary with updated metrics
        """
        try:
            # Get parcel geometry
            geometry = to_shape(parcel.geometry)
            centroid = geometry.centroid

            # Get bounding box
            bbox = satellite_service.get_parcel_bbox(parcel.geometry)

            # Download latest satellite image (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            image = satellite_service.download_sentinel2_image(
                bbox=bbox,
                time_interval=(start_date, end_date),
                resolution=10,
                max_cloud_coverage=0.3
            )

            if image is not None:
                # Create parcel mask
                mask = satellite_service.create_parcel_mask(
                    geometry=parcel.geometry,
                    bbox=bbox,
                    image_shape=image.shape[:2]
                )

                # Calculate statistics
                stats = satellite_service.calculate_parcel_statistics(image, mask)

                # Update parcel
                parcel.current_ndvi = stats["ndvi_mean"]
                parcel.current_evi = stats["evi_mean"]
                parcel.last_satellite_date = end_date

                logger.info(f"Updated satellite data for parcel {parcel.id}: NDVI={stats['ndvi_mean']:.3f}")

            # Get weather data
            weather_summary = await weather_service.get_weather_summary_for_parcel(
                lat=centroid.y,
                lon=centroid.x
            )

            # Calculate weather-based risks
            if weather_summary["current"]:
                # Get historical precipitation (simplified - would use actual historical data)
                precipitation_60days = weather_summary.get("forecast_precipitation_7days", 0) * 8.5  # Estimate

                drought_risk = weather_service.calculate_drought_risk(
                    precipitation_60days=precipitation_60days,
                    temperature_avg=weather_summary["current"]["temperature"],
                    humidity_avg=weather_summary["forecast_avg_humidity"],
                    soil_type=parcel.soil_type or "loam"
                )

                # Calculate frost risk if applicable
                if weather_summary["forecast"]:
                    forecast_temps = [f["temp_min"] for f in weather_summary["forecast"]]
                    frost_risk = weather_service.calculate_frost_risk(
                        forecast_temps=forecast_temps,
                        crop_growth_stage="vegetative"  # Would determine from planting date
                    )
                else:
                    frost_risk = 0.0

                # Update parcel risks
                parcel.drought_risk = drought_risk
                # parcel.frost_risk = frost_risk  # Add this field if needed

                logger.info(f"Updated weather risks for parcel {parcel.id}: drought={drought_risk:.2f}")

            # Commit updates
            db.commit()
            db.refresh(parcel)

            return {
                "parcel_id": str(parcel.id),
                "ndvi": parcel.current_ndvi,
                "evi": parcel.current_evi,
                "drought_risk": parcel.drought_risk,
                "last_updated": datetime.now().isoformat(),
                "weather_summary": weather_summary,
            }

        except Exception as e:
            logger.error(f"Error updating parcel {parcel.id}: {e}")
            db.rollback()
            raise

    async def check_parcel_alerts(
        self,
        db: Session,
        parcel: Parcel
    ) -> list:
        """
        Check parcel for alert conditions

        Args:
            db: Database session
            parcel: Parcel model instance

        Returns:
            List of alert dictionaries
        """
        alerts = []

        # Check NDVI decline
        if parcel.current_ndvi is not None and parcel.current_ndvi < 0.4:
            alerts.append({
                "type": "CROP_STRESS",
                "severity": "WARNING",
                "message": f"Low NDVI detected: {parcel.current_ndvi:.2f}. Crop may be stressed.",
                "recommendation": "Investigate crop health. Consider irrigation or fertilization."
            })

        # Check drought risk
        if parcel.drought_risk is not None and parcel.drought_risk > 0.6:
            alerts.append({
                "type": "DROUGHT_RISK",
                "severity": "CRITICAL" if parcel.drought_risk > 0.8 else "WARNING",
                "message": f"High drought risk: {parcel.drought_risk:.2%}",
                "recommendation": "Implement irrigation if available. Monitor soil moisture."
            })

        # Check for irrigation recommendation
        if not parcel.has_irrigation and parcel.drought_risk and parcel.drought_risk > 0.5:
            alerts.append({
                "type": "INFRASTRUCTURE",
                "severity": "INFO",
                "message": "Parcel lacks irrigation infrastructure",
                "recommendation": "Consider installing irrigation system for drought resilience."
            })

        return alerts


# Singleton instance
monitoring_service = ParcelMonitoringService()
