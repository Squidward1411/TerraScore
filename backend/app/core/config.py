"""
Core configuration settings for TerraScore API
Manages environment variables and application settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "TerraScore API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # Database
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")
    TIMESCALE_URL: Optional[PostgresDsn] = Field(None, env="TIMESCALE_URL")
    DB_ECHO: bool = False  # Log SQL queries

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CACHE_TTL: int = 3600  # 1 hour default cache TTL

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

    # External APIs
    SENTINEL_HUB_CLIENT_ID: Optional[str] = Field(None, env="SENTINEL_HUB_CLIENT_ID")
    SENTINEL_HUB_CLIENT_SECRET: Optional[str] = Field(None, env="SENTINEL_HUB_CLIENT_SECRET")
    OPENWEATHER_API_KEY: Optional[str] = Field(None, env="OPENWEATHER_API_KEY")

    # Object Storage (S3-compatible)
    S3_ENDPOINT_URL: Optional[str] = Field(None, env="S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID: Optional[str] = Field(None, env="S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="S3_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = Field(default="terrascore-data", env="S3_BUCKET_NAME")

    # ML Models
    ML_MODEL_PATH: str = Field(default="/app/ml/models", env="ML_MODEL_PATH")
    MLFLOW_TRACKING_URI: Optional[str] = Field(None, env="MLFLOW_TRACKING_URI")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Monitoring
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    ENABLE_METRICS: bool = True

    # Geospatial
    DEFAULT_SRID: int = 4326  # WGS84
    PARCEL_BUFFER_METERS: float = 10.0

    # Processing
    MAX_PARCEL_SIZE_HA: float = 1000.0  # Maximum parcel size in hectares
    MIN_PARCEL_SIZE_HA: float = 0.1     # Minimum parcel size

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".csv", ".geojson", ".kml", ".shp"]

    # Email (for alerts)
    SMTP_HOST: Optional[str] = Field(None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@terrascore.rs", env="EMAIL_FROM")

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()
