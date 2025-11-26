"""
Satellite Data Service
Handles Sentinel-2 imagery download and processing via Sentinel Hub API
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import numpy as np
from sentinelhub import (
    SHConfig,
    BBox,
    CRS,
    MimeType,
    SentinelHubRequest,
    DataCollection,
    bbox_to_dimensions,
)
import rasterio
from rasterio.transform import from_bounds
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class SatelliteService:
    """Service for downloading and processing satellite imagery"""

    def __init__(self):
        """Initialize Sentinel Hub configuration"""
        self.config = SHConfig()

        if settings.SENTINEL_HUB_CLIENT_ID and settings.SENTINEL_HUB_CLIENT_SECRET:
            self.config.sh_client_id = settings.SENTINEL_HUB_CLIENT_ID
            self.config.sh_client_secret = settings.SENTINEL_HUB_CLIENT_SECRET
            self.config.sh_base_url = "https://sh.dataspace.copernicus.eu"
            self.config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        else:
            logger.warning("Sentinel Hub credentials not configured")

    def download_sentinel2_image(
        self,
        bbox: BBox,
        time_interval: Tuple[datetime, datetime],
        resolution: int = 10,
        max_cloud_coverage: float = 0.2
    ) -> Optional[np.ndarray]:
        """
        Download Sentinel-2 imagery for given bounding box and time range

        Args:
            bbox: Bounding box (minx, miny, maxx, maxy) in WGS84
            time_interval: Tuple of (start_date, end_date)
            resolution: Spatial resolution in meters (10m default)
            max_cloud_coverage: Maximum acceptable cloud coverage (0-1)

        Returns:
            Numpy array with bands [B02, B03, B04, B08] (Blue, Green, Red, NIR)
            or None if no suitable image found
        """
        try:
            # Calculate image dimensions
            size = bbox_to_dimensions(bbox, resolution=resolution)

            # Define evalscript for band extraction
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: [{
                        bands: ["B02", "B03", "B04", "B08", "CLM"],
                        units: "DN"
                    }],
                    output: {
                        bands: 5,
                        sampleType: "UINT16"
                    }
                };
            }

            function evaluatePixel(sample) {
                return [sample.B02, sample.B03, sample.B04, sample.B08, sample.CLM];
            }
            """

            # Create request
            request = SentinelHubRequest(
                evalscript=evalscript,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=time_interval,
                        maxcc=max_cloud_coverage,
                    )
                ],
                responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
                bbox=bbox,
                size=size,
                config=self.config,
            )

            # Get data
            images = request.get_data()

            if not images or len(images) == 0:
                logger.warning(f"No images found for bbox {bbox} in time range {time_interval}")
                return None

            # Return the most recent image
            image = images[0]

            # Check cloud coverage
            cloud_mask = image[:, :, 4]  # CLM band
            cloud_coverage = np.sum(cloud_mask > 0) / cloud_mask.size

            if cloud_coverage > max_cloud_coverage:
                logger.warning(f"Cloud coverage {cloud_coverage:.2%} exceeds threshold {max_cloud_coverage:.2%}")
                return None

            # Return RGB + NIR bands (exclude cloud mask)
            return image[:, :, :4]

        except Exception as e:
            logger.error(f"Error downloading Sentinel-2 image: {e}")
            return None

    def calculate_ndvi(self, image: np.ndarray) -> np.ndarray:
        """
        Calculate NDVI from Sentinel-2 image

        Args:
            image: Numpy array with shape (height, width, bands)
                   Bands: [B02, B03, B04, B08] (Blue, Green, Red, NIR)

        Returns:
            NDVI array with shape (height, width)
            Values range from -1 to 1
        """
        # Extract Red (B04) and NIR (B08) bands
        red = image[:, :, 2].astype(float)
        nir = image[:, :, 3].astype(float)

        # Calculate NDVI: (NIR - Red) / (NIR + Red)
        # Add small epsilon to avoid division by zero
        denominator = nir + red + 1e-8
        ndvi = (nir - red) / denominator

        # Clip values to valid range
        ndvi = np.clip(ndvi, -1, 1)

        return ndvi

    def calculate_evi(self, image: np.ndarray) -> np.ndarray:
        """
        Calculate EVI (Enhanced Vegetation Index) from Sentinel-2 image

        EVI = 2.5 * ((NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1))

        Args:
            image: Numpy array with bands [B02, B03, B04, B08]

        Returns:
            EVI array with shape (height, width)
        """
        blue = image[:, :, 0].astype(float)
        red = image[:, :, 2].astype(float)
        nir = image[:, :, 3].astype(float)

        # Calculate EVI
        numerator = nir - red
        denominator = nir + 6 * red - 7.5 * blue + 1 + 1e-8
        evi = 2.5 * (numerator / denominator)

        # Clip to reasonable range
        evi = np.clip(evi, -1, 1)

        return evi

    def calculate_ndwi(self, image: np.ndarray) -> np.ndarray:
        """
        Calculate NDWI (Normalized Difference Water Index)

        NDWI = (Green - NIR) / (Green + NIR)

        Args:
            image: Numpy array with bands [B02, B03, B04, B08]

        Returns:
            NDWI array indicating water/moisture content
        """
        green = image[:, :, 1].astype(float)
        nir = image[:, :, 3].astype(float)

        denominator = green + nir + 1e-8
        ndwi = (green - nir) / denominator

        return np.clip(ndwi, -1, 1)

    def calculate_parcel_statistics(
        self,
        image: np.ndarray,
        parcel_mask: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate vegetation index statistics for a specific parcel

        Args:
            image: Sentinel-2 image array
            parcel_mask: Boolean mask indicating parcel pixels

        Returns:
            Dictionary with statistics (mean, std, min, max, percentiles)
        """
        # Calculate indices
        ndvi = self.calculate_ndvi(image)
        evi = self.calculate_evi(image)
        ndwi = self.calculate_ndwi(image)

        # Extract values within parcel
        ndvi_values = ndvi[parcel_mask]
        evi_values = evi[parcel_mask]
        ndwi_values = ndwi[parcel_mask]

        return {
            "ndvi_mean": float(np.mean(ndvi_values)),
            "ndvi_std": float(np.std(ndvi_values)),
            "ndvi_min": float(np.min(ndvi_values)),
            "ndvi_max": float(np.max(ndvi_values)),
            "ndvi_p25": float(np.percentile(ndvi_values, 25)),
            "ndvi_p50": float(np.percentile(ndvi_values, 50)),
            "ndvi_p75": float(np.percentile(ndvi_values, 75)),
            "evi_mean": float(np.mean(evi_values)),
            "evi_std": float(np.std(evi_values)),
            "ndwi_mean": float(np.mean(ndwi_values)),
            "valid_pixels": int(np.sum(parcel_mask)),
        }

    def get_parcel_bbox(self, geometry) -> BBox:
        """
        Extract bounding box from parcel geometry

        Args:
            geometry: Shapely geometry or GeoAlchemy2 geometry

        Returns:
            BBox object for Sentinel Hub
        """
        from geoalchemy2.shape import to_shape

        # Convert to Shapely if needed
        if not hasattr(geometry, 'bounds'):
            geometry = to_shape(geometry)

        minx, miny, maxx, maxy = geometry.bounds

        return BBox(bbox=[minx, miny, maxx, maxy], crs=CRS.WGS84)

    def create_parcel_mask(
        self,
        geometry,
        bbox: BBox,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Create binary mask for parcel within image

        Args:
            geometry: Parcel geometry (Shapely or GeoAlchemy2)
            bbox: Bounding box used for image
            image_shape: (height, width) of the image

        Returns:
            Boolean mask array
        """
        from geoalchemy2.shape import to_shape
        from rasterio.features import rasterize

        # Convert to Shapely if needed
        if not hasattr(geometry, 'bounds'):
            geometry = to_shape(geometry)

        # Create transform
        minx, miny, maxx, maxy = bbox.geometry.bounds
        transform = from_bounds(minx, miny, maxx, maxy, image_shape[1], image_shape[0])

        # Rasterize geometry
        mask = rasterize(
            [(geometry, 1)],
            out_shape=image_shape,
            transform=transform,
            fill=0,
            dtype=np.uint8
        )

        return mask.astype(bool)

    def save_image_to_storage(
        self,
        image: np.ndarray,
        parcel_id: str,
        date: datetime,
        index_type: str = "ndvi"
    ) -> str:
        """
        Save processed image to object storage

        Args:
            image: Image array to save
            parcel_id: Parcel UUID
            date: Acquisition date
            index_type: Type of index (ndvi, evi, etc.)

        Returns:
            Storage path/key
        """
        # This would integrate with MinIO/S3
        # For now, return a mock path
        date_str = date.strftime("%Y-%m-%d")
        path = f"processed/{index_type}/{date_str}/parcel-{parcel_id}_{index_type}.tif"

        # TODO: Implement actual S3/MinIO upload
        # boto3_client.upload_fileobj(...)

        logger.info(f"Saved image to {path}")
        return path


# Singleton instance
satellite_service = SatelliteService()
