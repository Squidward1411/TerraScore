"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-11-26 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('organization', sa.String(255)),
        sa.Column('phone_number', sa.String(20)),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String)),
        sa.Column('api_key', sa.String(64), unique=True, index=True),
        sa.Column('api_key_created_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean, nullable=False, default=False),
        sa.Column('is_superuser', sa.Boolean, nullable=False, default=False),
        sa.Column('subscription_tier', sa.String(50), default='starter'),
        sa.Column('rate_limit_per_minute', sa.Integer, default=60),
        sa.Column('rate_limit_per_hour', sa.Integer, default=1000),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('notes', sa.Text),
    )

    # Create parcels table
    op.create_table('parcels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cadastral_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('parcel_name', sa.String(255)),
        sa.Column('owner_name', sa.String(255)),
        sa.Column('owner_id_number', sa.String(50)),
        sa.Column('farmer_contact', sa.String(255)),
        sa.Column('geometry', geoalchemy2.Geometry('POLYGON', srid=4326), nullable=False),
        sa.Column('centroid', geoalchemy2.Geometry('POINT', srid=4326)),
        sa.Column('address', sa.String(500)),
        sa.Column('municipality', sa.String(100), index=True),
        sa.Column('district', sa.String(100), index=True),
        sa.Column('region', sa.String(100), index=True),
        sa.Column('area_hectares', sa.Float, nullable=False),
        sa.Column('perimeter_meters', sa.Float),
        sa.Column('elevation_avg_meters', sa.Float),
        sa.Column('slope_avg_degrees', sa.Float),
        sa.Column('current_crop_type', sa.String(100), index=True),
        sa.Column('planting_date', sa.DateTime(timezone=True)),
        sa.Column('expected_harvest_date', sa.DateTime(timezone=True)),
        sa.Column('crop_variety', sa.String(100)),
        sa.Column('soil_type', sa.String(100)),
        sa.Column('soil_ph', sa.Float),
        sa.Column('soil_organic_carbon', sa.Float),
        sa.Column('soil_texture_class', sa.String(50)),
        sa.Column('soil_drainage', sa.String(50)),
        sa.Column('has_irrigation', sa.Boolean, default=False),
        sa.Column('irrigation_type', sa.String(50)),
        sa.Column('has_drainage', sa.Boolean, default=False),
        sa.Column('historical_yields', postgresql.JSONB),
        sa.Column('historical_crops', postgresql.JSONB),
        sa.Column('current_ndvi', sa.Float),
        sa.Column('current_evi', sa.Float),
        sa.Column('last_satellite_date', sa.DateTime(timezone=True)),
        sa.Column('current_health_score', sa.Float),
        sa.Column('drought_risk', sa.Float),
        sa.Column('flood_risk', sa.Float),
        sa.Column('pest_risk', sa.Float),
        sa.Column('disease_risk', sa.Float),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True, index=True),
        sa.Column('is_insured', sa.Boolean, default=False),
        sa.Column('has_active_loan', sa.Boolean, default=False),
        sa.Column('monitored_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('data_source', sa.String(100)),
        sa.Column('notes', sa.Text),
        sa.Column('extra_attributes', postgresql.JSONB),
    )

    # Create credit_scores table
    op.create_table('credit_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('parcels.id'), nullable=False, index=True),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('risk_category', sa.String(20), nullable=False),
        sa.Column('crop_health_score', sa.Float, nullable=False),
        sa.Column('weather_risk_score', sa.Float, nullable=False),
        sa.Column('soil_quality_score', sa.Float, nullable=False),
        sa.Column('historical_performance_score', sa.Float, nullable=False),
        sa.Column('weights', postgresql.JSONB),
        sa.Column('ndvi_current', sa.Float),
        sa.Column('ndvi_30day_avg', sa.Float),
        sa.Column('ndvi_seasonal_deviation', sa.Float),
        sa.Column('drought_probability', sa.Float),
        sa.Column('frost_risk', sa.Float),
        sa.Column('extreme_weather_score', sa.Float),
        sa.Column('cumulative_precipitation_60days', sa.Float),
        sa.Column('avg_temperature_60days', sa.Float),
        sa.Column('predicted_yield_tons_per_ha', sa.Float),
        sa.Column('yield_prediction_confidence', sa.Float),
        sa.Column('yield_prediction_lower_bound', sa.Float),
        sa.Column('yield_prediction_upper_bound', sa.Float),
        sa.Column('recommended_loan_amount', sa.Float),
        sa.Column('suggested_interest_rate_adjustment', sa.Float),
        sa.Column('max_loan_to_value_ratio', sa.Float),
        sa.Column('confidence_level', sa.String(20), nullable=False),
        sa.Column('data_quality_score', sa.Float),
        sa.Column('data_completeness', sa.Float),
        sa.Column('active_risk_factors', postgresql.JSONB),
        sa.Column('model_version', sa.String(50)),
        sa.Column('calculation_method', sa.String(100)),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('calculated_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('calculation_duration_ms', sa.Integer),
        sa.Column('previous_score', sa.Float),
        sa.Column('score_change', sa.Float),
        sa.Column('raw_features', postgresql.JSONB),
        sa.Column('explanation', sa.Text),
    )

    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('parcels.id'), nullable=False, index=True),
        sa.Column('alert_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('recommendation', sa.Text),
        sa.Column('risk_score', sa.Float),
        sa.Column('confidence', sa.Float),
        sa.Column('supporting_data', postgresql.JSONB),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('event_start_date', sa.DateTime(timezone=True)),
        sa.Column('event_end_date', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True, index=True),
        sa.Column('is_acknowledged', sa.Boolean, nullable=False, default=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True)),
        sa.Column('acknowledged_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('is_resolved', sa.Boolean, nullable=False, default=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('notification_sent', sa.Boolean, nullable=False, default=False),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True)),
        sa.Column('notification_channels', postgresql.JSONB),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), index=True),
        sa.Column('source', sa.String(100)),
        sa.Column('model_version', sa.String(50)),
    )

    # Create api_logs table
    op.create_table('api_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), index=True),
        sa.Column('api_key', sa.String(64), index=True),
        sa.Column('endpoint', sa.String(255), nullable=False, index=True),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('request_path', sa.String(500), nullable=False),
        sa.Column('query_params', postgresql.JSONB),
        sa.Column('request_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('client_ip', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('status_code', sa.Integer, nullable=False, index=True),
        sa.Column('response_time_ms', sa.Integer),
        sa.Column('is_billable', sa.Boolean, nullable=False, default=True),
        sa.Column('cost_credits', sa.Float),
        sa.Column('parcel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('parcels.id'), index=True),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('error_message', sa.String(1000)),
        sa.Column('error_type', sa.String(100)),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('rate_limit_remaining', sa.Integer),
        sa.Column('rate_limit_exceeded', sa.Boolean, nullable=False, default=False),
        sa.Column('metadata', postgresql.JSONB),
    )

    # Create spatial indexes
    op.execute('CREATE INDEX idx_parcels_geometry ON parcels USING GIST (geometry);')
    op.execute('CREATE INDEX idx_parcels_centroid ON parcels USING GIST (centroid);')


def downgrade() -> None:
    op.drop_table('api_logs')
    op.drop_table('alerts')
    op.drop_table('credit_scores')
    op.drop_table('parcels')
    op.drop_table('users')
