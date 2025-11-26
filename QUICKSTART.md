# TerraScore - Quick Start Guide

This guide will help you get TerraScore up and running on your local machine in minutes.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Git**
- **Python** 3.11+ (for local development)
- **Node.js** 18+ (for frontend development)

## Quick Setup with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/Squidward1411/TerraScore.git
cd TerraScore
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your configuration. For local development, the defaults should work fine. You'll need to add:

- **SECRET_KEY**: Generate a secure random string
- **SENTINEL_HUB_CLIENT_ID** and **SENTINEL_HUB_CLIENT_SECRET**: Get from [Sentinel Hub](https://www.sentinel-hub.com/)
- **OPENWEATHER_API_KEY**: Get from [OpenWeatherMap](https://openweathermap.org/api)

### 3. Start All Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL + PostGIS (port 5432)
- TimescaleDB (port 5433)
- Redis (port 6379)
- MinIO (port 9000, 9001)
- FastAPI Backend (port 8000)
- Celery Worker
- Next.js Frontend (port 3000)
- Prometheus (port 9090)
- Grafana (port 3001)

### 4. Run Database Migrations

```bash
docker-compose exec api alembic upgrade head
```

### 5. Create Initial Admin User

```bash
docker-compose exec api python scripts/create_admin.py
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **Grafana**: http://localhost:3001 (admin/admin)
- **MinIO Console**: http://localhost:9001 (admin/minio_dev_password)

## Local Development Setup (Without Docker)

### Backend Setup

1. **Create virtual environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL with PostGIS**:
```bash
# Using Docker
docker run -d \
  --name terrascore-postgres \
  -e POSTGRES_USER=terrascore \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=terrascore \
  -p 5432:5432 \
  postgis/postgis:15-3.3
```

4. **Run migrations**:
```bash
alembic upgrade head
```

5. **Start the API server**:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Start development server**:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Initial Configuration

### 1. Register Your First User

Go to http://localhost:3000/auth/register and create an account.

### 2. Generate API Key

After logging in, go to your profile and generate an API key for programmatic access.

### 3. Add Your First Parcel

Use the API or frontend to add a farm parcel:

```bash
curl -X POST "http://localhost:8000/api/v1/parcels/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cadastral_id": "DEMO001",
    "parcel_name": "Demo Field",
    "area_hectares": 10.5,
    "current_crop_type": "maize",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [20.4489, 44.7866],
        [20.4589, 44.7866],
        [20.4589, 44.7966],
        [20.4489, 44.7966],
        [20.4489, 44.7866]
      ]]
    }
  }'
```

### 4. Calculate Credit Score

```bash
curl -X GET "http://localhost:8000/api/v1/credit-scores/{parcel_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
```

### Restart Services

```bash
docker-compose restart api
docker-compose restart frontend
```

### Stop All Services

```bash
docker-compose down
```

### Clean Up (Remove Data)

```bash
docker-compose down -v  # Warning: This deletes all data!
```

## Testing the Platform

### 1. Backend Tests

```bash
cd backend
pytest tests/ -v
```

### 2. Frontend Tests

```bash
cd frontend
npm test
```

### 3. API Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

## Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Ensure PostgreSQL is running:
```bash
docker-compose ps postgres
```

2. Check logs:
```bash
docker-compose logs postgres
```

3. Verify connection string in `.env`

### Frontend Not Loading

1. Clear Next.js cache:
```bash
cd frontend
rm -rf .next
npm run dev
```

2. Check if port 3000 is already in use

### API Errors

1. Check API logs:
```bash
docker-compose logs api
```

2. Verify environment variables are set correctly

3. Ensure database migrations are up to date:
```bash
docker-compose exec api alembic current
```

## Next Steps

- Read the [Full Documentation](./docs/README.md)
- Explore the [API Documentation](http://localhost:8000/docs)
- Set up [Satellite Data Integration](./docs/satellite-integration.md)
- Configure [Weather Data Sources](./docs/weather-integration.md)
- Train [ML Models](./ml/training/README.md)

## Getting Help

- **Issues**: https://github.com/Squidward1411/TerraScore/issues
- **Discussions**: https://github.com/Squidward1411/TerraScore/discussions
- **Email**: info@terrascore.rs

## Production Deployment

For production deployment instructions, see [DEPLOYMENT.md](./docs/DEPLOYMENT.md)
