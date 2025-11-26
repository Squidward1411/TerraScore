"""
Alert model for risk notifications
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class AlertType(str, enum.Enum):
    """Alert type enumeration"""
    DROUGHT_RISK = "drought_risk"
    FLOOD_RISK = "flood_risk"
    FROST_WARNING = "frost_warning"
    DISEASE_DETECTED = "disease_detected"
    PEST_DETECTED = "pest_detected"
    CROP_STRESS = "crop_stress"
    HARVEST_READY = "harvest_ready"
    LOAN_DEFAULT_RISK = "loan_default_risk"
    INSURANCE_CLAIM = "insurance_claim"


class AlertSeverity(str, enum.Enum):
    """Alert severity enumeration"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(Base):
    """
    Alert/notification model for risk warnings
    Sent to users when risk conditions are detected
    """
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relationship to parcel
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False, index=True)

    # Alert classification
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, default=AlertSeverity.WARNING)

    # Alert content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)  # Suggested action

    # Risk metrics
    risk_score = Column(Float, nullable=True)  # 0-1 probability or 0-100 score
    confidence = Column(Float, nullable=True)  # 0-1 confidence in alert

    # Data supporting the alert
    supporting_data = Column(JSONB, nullable=True)  # NDVI values, weather data, etc.

    # Timing
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    event_start_date = Column(DateTime(timezone=True), nullable=True)  # When the risk event started
    event_end_date = Column(DateTime(timezone=True), nullable=True)  # Predicted or actual end

    # Status tracking
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Notification delivery
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    notification_channels = Column(JSONB, nullable=True)  # ['email', 'sms', 'push']

    # Recipient
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Source of alert
    source = Column(String(100), nullable=True)  # 'satellite_monitoring', 'weather_api', 'ml_model'
    model_version = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<Alert {self.alert_type} for parcel={self.parcel_id} severity={self.severity}>"

    @property
    def is_critical(self) -> bool:
        """Check if alert is critical"""
        return self.severity == AlertSeverity.CRITICAL

    @property
    def needs_immediate_action(self) -> bool:
        """Check if alert requires immediate action"""
        return self.is_active and self.severity == AlertSeverity.CRITICAL and not self.is_acknowledged
