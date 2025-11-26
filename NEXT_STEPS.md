# TerraScore - Next Steps

This document outlines the immediate next steps to move from MVP to a fully functional production system.

## Phase 2: Core Functionality Enhancement

### 1. Satellite Data Integration (High Priority)

**Task**: Implement automated satellite imagery download and processing

**Files to create:**
- `backend/app/services/satellite_service.py` - Sentinel-2 API integration
- `backend/app/services/ndvi_calculator.py` - Vegetation index calculations
- `infrastructure/airflow/dags/satellite_ingestion.py` - Daily data pipeline

**Implementation steps:**
```bash
# 1. Get Sentinel Hub credentials
# Visit: https://www.sentinel-hub.com/
# Add to .env: SENTINEL_HUB_CLIENT_ID and SENTINEL_HUB_CLIENT_SECRET

# 2. Implement satellite service
cd backend/app/services
# Create satellite_service.py with:
# - download_sentinel2_image()
# - process_satellite_image()
# - calculate_ndvi()
# - store_to_timescaledb()

# 3. Test with sample parcel
python scripts/test_satellite_download.py --parcel-id=TEST001
```

**Expected outcome:**
- Daily automated downloads of Sentinel-2 imagery
- NDVI/EVI calculation for all active parcels
- Time-series storage in TimescaleDB
- Updated parcel.current_ndvi values

### 2. ML Model Training (High Priority)

**Task**: Train XGBoost yield prediction and Random Forest risk classification models

**Files to create:**
- `ml/training/train_yield_model.py` - XGBoost training script
- `ml/training/train_risk_model.py` - Random Forest training
- `ml/training/prepare_data.py` - Feature engineering
- `ml/evaluation/evaluate_models.py` - Model evaluation

**Implementation steps:**
```bash
# 1. Gather training data
# - Historical yield data from Serbian Statistical Office
# - Sentinel-2 archive data (2016-present)
# - Weather data from OpenWeatherMap API
# - Soil data from ESDAC

# 2. Train models
cd ml/training
python prepare_data.py --years 2016-2023 --output train_data.csv
python train_yield_model.py --input train_data.csv --output ../models/yield_model.pkl
python train_risk_model.py --input train_data.csv --output ../models/risk_model.pkl

# 3. Evaluate models
cd ../evaluation
python evaluate_models.py --yield-model ../models/yield_model.pkl
```

**Expected outcome:**
- Trained XGBoost model (R² > 0.75)
- Trained Random Forest classifier (F1 > 0.70)
- Model files saved in ml/models/
- Integration with credit_score_calculator.py

### 3. Weather Data Integration (Medium Priority)

**Task**: Implement real-time and historical weather data collection

**Files to create:**
- `backend/app/services/weather_service.py` - Weather API integration
- `backend/app/services/risk_calculator.py` - Weather-based risk calculations
- `infrastructure/airflow/dags/weather_update.py` - Hourly weather updates

**Implementation steps:**
```bash
# 1. Get OpenWeatherMap API key
# Visit: https://openweathermap.org/api
# Add to .env: OPENWEATHER_API_KEY

# 2. Implement weather service
cd backend/app/services
# Create weather_service.py with:
# - get_current_weather()
# - get_weather_forecast()
# - calculate_drought_risk()
# - calculate_frost_risk()

# 3. Update credit score calculator
# Integrate real weather data into _calculate_weather_risk_score()
```

**Expected outcome:**
- Real-time weather monitoring for all parcels
- Accurate drought and frost risk calculations
- Weather-based alerts
- Historical weather data storage

### 4. Frontend Dashboard (Medium Priority)

**Task**: Build interactive dashboard for bank users

**Files to create:**
- `frontend/src/app/dashboard/page.tsx` - Main dashboard
- `frontend/src/app/dashboard/parcels/[id]/page.tsx` - Parcel detail
- `frontend/src/components/maps/ParcelMap.tsx` - Mapbox integration
- `frontend/src/components/charts/NDVIChart.tsx` - Time-series visualization
- `frontend/src/components/credit/ScoreCard.tsx` - Credit score display

**Implementation steps:**
```bash
cd frontend

# 1. Install additional dependencies
npm install react-map-gl mapbox-gl recharts date-fns

# 2. Create dashboard pages
mkdir -p src/app/dashboard/parcels
# Create page.tsx files for each route

# 3. Implement components
mkdir -p src/components/{maps,charts,credit}
# Create reusable components

# 4. Test locally
npm run dev
```

**Expected outcome:**
- Interactive map showing all parcels
- Parcel detail page with credit score
- NDVI time-series chart
- Risk indicators and alerts
- Batch processing interface

### 5. Database Migrations (High Priority)

**Task**: Create Alembic migrations for production deployment

**Files to create:**
- `backend/alembic/versions/001_initial_schema.py` - Initial migration
- `backend/alembic/versions/002_add_indexes.py` - Performance indexes
- `backend/alembic/versions/003_add_alerts.py` - Alerts table

**Implementation steps:**
```bash
cd backend

# 1. Initialize Alembic (already done in structure)
alembic init alembic

# 2. Create migrations
alembic revision --autogenerate -m "initial schema"
alembic revision -m "add geospatial indexes"
alembic revision -m "add composite indexes for performance"

# 3. Apply migrations
alembic upgrade head

# 4. Test rollback
alembic downgrade -1
alembic upgrade head
```

**Expected outcome:**
- Version-controlled database schema
- Automated migrations on deployment
- Rollback capability
- Performance-optimized indexes

## Phase 3: Advanced Features

### 6. PDF Report Generation (Medium Priority)

**Task**: Generate professional PDF credit reports

**Files to create:**
- `backend/app/services/pdf_generator.py` - ReportLab integration
- `backend/app/templates/credit_report.html` - Report template

**Implementation:**
- Use ReportLab library
- Include company logo, parcel map, charts
- Add detailed score breakdown
- Generate downloadable PDF via API endpoint

### 7. Batch Processing UI (Low Priority)

**Task**: Web interface for batch credit score calculation

**Files to create:**
- `frontend/src/app/dashboard/batch/page.tsx`
- `frontend/src/components/batch/FileUpload.tsx`
- `frontend/src/components/batch/ResultsTable.tsx`

**Features:**
- Upload CSV of parcel IDs
- Progress tracking
- Download results as Excel
- Error handling

### 8. Alert System (Medium Priority)

**Task**: Email/SMS notifications for risk events

**Files to create:**
- `backend/app/services/notification_service.py`
- `backend/app/workers/alert_processor.py`
- `infrastructure/airflow/dags/risk_monitoring.py`

**Features:**
- Daily risk monitoring
- Automated alert generation
- Email notifications
- SMS via Twilio (optional)

## Phase 4: Production Deployment

### 9. Production Environment Setup

**Tasks:**
1. **Domain & SSL**
   ```bash
   # Register domain: terrascore.rs
   # Configure DNS
   # Set up Let's Encrypt
   certbot --nginx -d api.terrascore.rs -d app.terrascore.rs
   ```

2. **Server Provisioning**
   - Rent VPS (Hetzner/DigitalOcean)
   - 32GB RAM, 8 CPU cores minimum
   - Ubuntu 22.04 LTS
   - Configure firewall (UFW)

3. **Environment Variables**
   - Move secrets to environment variables
   - Use HashiCorp Vault or AWS Secrets Manager
   - Never commit secrets to git

4. **Monitoring Setup**
   - Configure Prometheus alerts
   - Set up Grafana dashboards
   - Add Sentry for error tracking
   - Configure log aggregation

5. **Backup Strategy**
   - Daily PostgreSQL backups
   - S3/MinIO backup to separate storage
   - Test restore procedures

### 10. Performance Optimization

**Tasks:**
1. **Database Optimization**
   - Add composite indexes
   - Optimize slow queries
   - Set up connection pooling
   - Configure read replicas (if needed)

2. **API Optimization**
   - Implement Redis caching
   - Add CDN for static assets
   - Enable gzip compression
   - Optimize N+1 queries

3. **Load Testing**
   ```bash
   # Install Locust
   pip install locust

   # Create load test
   # File: tests/load/locustfile.py

   # Run load test
   locust -f tests/load/locustfile.py --host http://localhost:8000
   ```

### 11. Security Hardening

**Tasks:**
1. **API Security**
   - Enable rate limiting (already configured)
   - Add request validation
   - Implement IP whitelisting (optional)
   - Set up WAF (Web Application Firewall)

2. **Database Security**
   - Use SSL connections
   - Rotate credentials regularly
   - Implement row-level security
   - Enable audit logging

3. **Secrets Management**
   - Never use default passwords
   - Generate strong SECRET_KEY
   - Rotate API keys regularly
   - Use environment-specific credentials

## Phase 5: Future Enhancements

### 12. ClaimWatch™ (Insurance Module)

**Features to implement:**
- Insurance policy management
- Automated claim verification
- Before/after satellite comparison
- Damage assessment calculation

### 13. FarmPulse™ (Farmer Portal)

**Features to implement:**
- Farmer registration
- Parcel ownership claims
- AI chatbot (YugoGPT integration)
- SMS alerts
- Mobile app (React Native)

### 14. Multi-Crop Support

**Tasks:**
- Add crop-specific NDVI thresholds
- Train separate ML models per crop
- Implement crop rotation tracking
- Add planting recommendations

### 15. Advanced Analytics

**Features:**
- Regional yield comparisons
- Climate change impact analysis
- Subsidy optimization (government)
- Portfolio risk analysis (banks)

## Immediate Action Items (This Week)

1. ✅ Review the MVP codebase
2. ⬜ Get Sentinel Hub API credentials
3. ⬜ Get OpenWeatherMap API key
4. ⬜ Set up local development environment
5. ⬜ Test API endpoints with Postman/curl
6. ⬜ Start collecting training data for ML models
7. ⬜ Create first parcel in the system
8. ⬜ Calculate first credit score
9. ⬜ Document any issues or improvements
10. ⬜ Plan Phase 2 sprint

## Resources & Links

**Documentation:**
- Sentinel Hub: https://docs.sentinel-hub.com/
- OpenWeatherMap: https://openweathermap.org/api
- PostGIS: https://postgis.net/documentation/
- FastAPI: https://fastapi.tiangolo.com/
- Next.js: https://nextjs.org/docs

**Data Sources:**
- Sentinel-2: https://scihub.copernicus.eu/
- ESDAC Soil: https://esdac.jrc.ec.europa.eu/
- Serbian Cadastre: https://rgz.gov.rs/
- Statistical Office: https://www.stat.gov.rs/

**Tools:**
- Postman (API testing): https://www.postman.com/
- DBeaver (Database GUI): https://dbeaver.io/
- pgAdmin (PostgreSQL): https://www.pgadmin.org/

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs -f api`
2. Review the error in Sentry (when configured)
3. Search existing issues: https://github.com/Squidward1411/TerraScore/issues
4. Create new issue with reproduction steps
5. Contact: info@terrascore.rs

## Success Metrics

**Phase 2 Success Criteria:**
- [ ] Satellite data pipeline running daily
- [ ] ML models trained with R² > 0.75
- [ ] Weather data updating hourly
- [ ] Dashboard fully functional
- [ ] All tests passing (>80% coverage)

**Production Readiness:**
- [ ] SSL certificates configured
- [ ] Monitoring dashboards operational
- [ ] Backup strategy tested
- [ ] Load testing completed (>100 req/s)
- [ ] Security audit passed

---

**Current Status**: MVP Complete ✅
**Next Milestone**: Satellite Integration & ML Models
**Target Date**: 2 weeks from now

Good luck! 🚀
