# TerraScore - Agricultural Risk Intelligence Platform

**Transform satellite imagery, weather data, and soil characteristics into financial-grade credit scores for farm parcels.**

## Overview

TerraScore is a B2B agricultural risk intelligence platform that enables banks, insurers, and government agencies to assess agricultural lending risk without physical site inspections.

## Features

### MVP (Version 1.0)
- ✅ **CreditLens™** - Bank portal for credit risk assessment
- ✅ Credit scoring (0-100 scale) for farm parcels
- ✅ Yield prediction for maize crops
- ✅ NDVI-based crop health monitoring
- ✅ PDF report generation
- ✅ RESTful API with JWT authentication
- ✅ Real-time satellite data integration

## Architecture

```
TerraScore/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── core/      # Configuration, security
│   │   ├── db/        # Database connections
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── ml/        # ML model serving
│   └── tests/         # Backend tests
├── frontend/          # Next.js application
│   └── src/
│       ├── app/       # Next.js 14 app directory
│       ├── components/# React components
│       └── lib/       # Utilities
├── ml/                # Machine learning
│   ├── models/        # Trained models
│   ├── training/      # Training scripts
│   └── notebooks/     # Jupyter notebooks
├── infrastructure/    # DevOps
│   ├── docker/        # Dockerfiles
│   ├── nginx/         # Nginx configs
│   └── airflow/       # Data pipelines
└── docs/              # Documentation
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL + PostGIS** - Geospatial database
- **TimescaleDB** - Time-series data (NDVI history)
- **Redis** - Caching and task queue
- **Celery** - Asynchronous task processing
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations

### Frontend
- **Next.js 14** - React framework with SSR
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Mapbox GL JS** - Interactive maps
- **Recharts** - Data visualization

### ML & Data Processing
- **scikit-learn** - Machine learning
- **XGBoost** - Yield prediction
- **GDAL/rasterio** - Geospatial data processing
- **sentinelhub-py** - Sentinel-2 API
- **Apache Airflow** - Data pipeline orchestration

### Infrastructure
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **Prometheus + Grafana** - Monitoring
- **GitHub Actions** - CI/CD

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with PostGIS

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/TerraScore.git
cd TerraScore
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
cd backend
alembic upgrade head
```

5. **Access the application**
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Grafana: http://localhost:3001

### Manual Setup (Without Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Documentation

### Authentication
```bash
# Get access token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

### Get Credit Score
```bash
curl -X GET "http://localhost:8000/api/v1/parcels/12345/credit-score" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response
```json
{
  "score": 78.5,
  "components": {
    "crop_health": 82.3,
    "weather_risk": 75.0,
    "soil_quality": 80.0,
    "historical": 77.0
  },
  "risk_category": "LOW",
  "recommended_loan_amount": 150000,
  "confidence_level": "HIGH"
}
```

## Data Pipeline

The system runs automated daily tasks:
- **02:00** - Download Sentinel-2 imagery
- **03:00** - Calculate NDVI/EVI indices
- **04:00** - Run ML predictions
- **05:00** - Generate risk alerts
- **06:00** - Refresh cache

## ML Models

### Yield Prediction Model
- **Algorithm**: XGBoost Regressor
- **Features**: NDVI, weather, soil, temporal data
- **Performance**: R² = 0.82, RMSE = 0.9 tons/ha
- **Training Data**: 5 years of historical yields

### Risk Classification Model
- **Algorithm**: Random Forest Classifier
- **Classes**: LOW, MEDIUM, HIGH risk
- **Performance**: F1 Score = 0.70

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Deployment

### Production Deployment

1. **Build Docker images**
```bash
docker-compose -f docker-compose.prod.yml build
```

2. **Deploy to server**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Set up SSL with Let's Encrypt**
```bash
./scripts/setup-ssl.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Contact

- **Email**: info@terrascore.rs
- **Website**: https://terrascore.rs
- **Documentation**: https://docs.terrascore.rs

## Acknowledgments

- Sentinel-2 data provided by ESA Copernicus program
- Weather data from OpenWeatherMap
- Soil data from ESDAC (European Soil Data Centre)
- Built with support from Serbian National AI Platform
