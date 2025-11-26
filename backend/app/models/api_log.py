"""
API log model for usage tracking and billing
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class APILog(Base):
    """
    API usage log for tracking requests and billing
    Records every API call for analytics and billing purposes
    """
    __tablename__ = "api_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User identification
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    api_key = Column(String(64), index=True, nullable=True)

    # Request details
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=False)
    query_params = Column(JSONB, nullable=True)

    # Request identification
    request_id = Column(String(100), unique=True, index=True, nullable=False)
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Response details
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds

    # Billing information
    is_billable = Column(Boolean, default=True, nullable=False)
    cost_credits = Column(Float, nullable=True)  # Cost in billing credits

    # Resource accessed
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True, index=True)
    resource_type = Column(String(50), nullable=True)  # 'credit_score', 'yield_prediction', etc.

    # Error information (if applicable)
    error_message = Column(String(1000), nullable=True)
    error_type = Column(String(100), nullable=True)

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Rate limiting
    rate_limit_remaining = Column(Integer, nullable=True)
    rate_limit_exceeded = Column(Boolean, default=False, nullable=False)

    # Additional metadata
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<APILog {self.method} {self.endpoint} status={self.status_code}>"

    @property
    def is_successful(self) -> bool:
        """Check if request was successful"""
        return 200 <= self.status_code < 300

    @property
    def is_error(self) -> bool:
        """Check if request resulted in error"""
        return self.status_code >= 400
