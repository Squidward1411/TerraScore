# TerraScore Testing Guide

Complete guide to test all components of the TerraScore platform.

---

## Quick Start Testing (5 minutes)

### 1. Prerequisites

```bash
# Verify installations
docker --version          # Should be 20.10+
docker-compose --version  # Should be 2.0+
python --version         # Should be 3.11+
node --version           # Should be 18+
```

### 2. Start All Services

```bash
cd /home/user/TerraScore

# Start infrastructure with Docker Compose
docker-compose up -d

# Wait for services to be ready (~30 seconds)
docker-compose ps

# Check logs
docker-compose logs -f
```

You should see these services running:
- ✅ postgres (PostgreSQL + PostGIS)
- ✅ timescale (TimescaleDB)
- ✅ redis (Cache)
- ✅ minio (Object Storage)
- ✅ prometheus (Metrics)
- ✅ grafana (Dashboards)

---

## Testing Phase 1: Backend API

### Step 1: Set Up Backend Environment

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=test-secret-key-change-in-production-make-it-very-long-and-random
DATABASE_URL=postgresql://terrascore:terrascore_dev_password@localhost:5432/terrascore
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
EOF
```

### Step 2: Run Database Migrations

```bash
# Apply migrations
alembic upgrade head

# Verify migration
alembic current
# Should show: 001 (head)

# Check database
docker exec -it terrascore-postgres psql -U terrascore -d terrascore -c "\dt"
# Should list: users, parcels, credit_scores, alerts, api_logs
```

### Step 3: Start Backend API

```bash
# Start FastAPI server
uvicorn app.main:app --reload --port 8000

# In another terminal, test health endpoint
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

### Step 4: Test API Documentation

Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You should see all API endpoints documented!

---

## Testing Phase 2: Authentication & User Management

### Step 1: Register a Test User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@terrascore.rs",
    "username": "testuser",
    "password": "TestPass123!",
    "full_name": "Test User",
    "organization": "Test Bank"
  }'
```

Expected response:
```json
{
  "id": "uuid-here",
  "email": "test@terrascore.rs",
  "username": "testuser",
  "full_name": "Test User",
  "organization": "Test Bank",
  "role": "bank_user",
  "is_active": true,
  ...
}
```

### Step 2: Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123!"
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Save this token!** You'll need it for authenticated requests.

```bash
# Save token to variable
export TOKEN="your-access-token-here"
```

### Step 3: Test Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

Should return your user profile!

---

## Testing Phase 3: Parcel Management

### Step 1: Create a Test Parcel

```bash
curl -X POST "http://localhost:8000/api/v1/parcels/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cadastral_id": "TEST001",
    "parcel_name": "Demo Field 1",
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
    },
    "address": "Test Farm, Serbia",
    "municipality": "Belgrade",
    "soil_type": "loam",
    "soil_ph": 6.5,
    "soil_organic_carbon": 2.5,
    "has_irrigation": true,
    "planting_date": "2024-04-15T00:00:00Z"
  }'
```

**Save the parcel ID** from the response!

```bash
export PARCEL_ID="your-parcel-id-here"
```

### Step 2: List All Parcels

```bash
curl -X GET "http://localhost:8000/api/v1/parcels/" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Get Parcel Details

```bash
curl -X GET "http://localhost:8000/api/v1/parcels/$PARCEL_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Testing Phase 4: Credit Score Calculation

### Step 1: Calculate Credit Score

```bash
curl -X GET "http://localhost:8000/api/v1/credit-scores/$PARCEL_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response (may take a few seconds):
```json
{
  "id": "uuid",
  "parcel_id": "your-parcel-id",
  "score": 78.5,
  "risk_category": "LOW",
  "confidence_level": "MEDIUM",
  "components": {
    "crop_health": 82.3,
    "weather_risk": 75.0,
    "soil_quality": 80.0,
    "historical": 77.0
  },
  "yield_prediction": {
    "predicted_yield_tons_per_ha": 8.2,
    "confidence": 0.85,
    "lower_bound": 7.0,
    "upper_bound": 9.4
  },
  "loan_recommendation": {
    "recommended_amount": 31500.00,
    "suggested_interest_adjustment": -0.5,
    "max_loan_to_value_ratio": 71.4
  },
  "calculated_at": "2024-11-26T16:30:00Z"
}
```

### Step 2: Force Recalculation

```bash
curl -X GET "http://localhost:8000/api/v1/credit-scores/$PARCEL_ID?force_recalculate=true" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Batch Credit Scores

Create more parcels first, then:

```bash
curl -X POST "http://localhost:8000/api/v1/credit-scores/batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parcel_ids": ["parcel-id-1", "parcel-id-2"],
    "include_details": true,
    "force_recalculate": false
  }'
```

---

## Testing Phase 5: Frontend Dashboard

### Step 1: Install Frontend Dependencies

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your-mapbox-token-optional
EOF
```

### Step 2: Start Frontend Development Server

```bash
npm run dev
```

Open your browser: **http://localhost:3000**

### Step 3: Test Frontend Features

1. **Landing Page** (http://localhost:3000)
   - ✅ See TerraScore branding
   - ✅ Click "Go to Dashboard"

2. **Sign In** (http://localhost:3000/auth/login)
   - ✅ Login with: testuser / TestPass123!

3. **Dashboard** (http://localhost:3000/dashboard)
   - ✅ See parcel list
   - ✅ Search for "TEST001"
   - ✅ Filter by crop type
   - ✅ See statistics cards
   - ✅ Click on a parcel row

4. **Parcel Detail** (http://localhost:3000/dashboard/parcels/[id])
   - ✅ See credit score (large number)
   - ✅ See component scores (bars)
   - ✅ See NDVI chart
   - ✅ See yield prediction
   - ✅ See loan recommendation
   - ✅ Click "Recalculate" button
   - ✅ Click "Export Report" (ready for implementation)

---

## Testing Phase 6: Backend Services (Optional - Requires API Keys)

### Test Satellite Service

**Note**: Requires Sentinel Hub API credentials

```bash
cd ../backend

# Add to .env
echo "SENTINEL_HUB_CLIENT_ID=your-client-id" >> .env
echo "SENTINEL_HUB_CLIENT_SECRET=your-client-secret" >> .env

# Test satellite download
python << 'EOF'
from app.services.satellite_service import satellite_service
from sentinelhub import BBox, CRS
from datetime import datetime, timedelta

# Test location (Belgrade area)
bbox = BBox([20.4489, 44.7866, 20.4589, 44.7966], CRS.WGS84)
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print("Downloading Sentinel-2 image...")
image = satellite_service.download_sentinel2_image(
    bbox=bbox,
    time_interval=(start_date, end_date),
    resolution=10,
    max_cloud_coverage=0.3
)

if image is not None:
    print(f"✅ Success! Image shape: {image.shape}")

    # Calculate NDVI
    ndvi = satellite_service.calculate_ndvi(image)
    print(f"✅ NDVI calculated! Range: {ndvi.min():.3f} to {ndvi.max():.3f}")
else:
    print("❌ No suitable image found (likely too cloudy)")
EOF
```

### Test Weather Service

**Note**: Requires OpenWeatherMap API key

```bash
# Add to .env
echo "OPENWEATHER_API_KEY=your-api-key" >> .env

# Test weather service
python << 'EOF'
import asyncio
from app.services.weather_service import weather_service

async def test_weather():
    # Belgrade coordinates
    lat, lon = 44.7866, 20.4489

    print("Fetching current weather...")
    weather = await weather_service.get_current_weather(lat, lon)

    if weather:
        print(f"✅ Temperature: {weather['temperature']}°C")
        print(f"✅ Humidity: {weather['humidity']}%")
        print(f"✅ Description: {weather['description']}")
    else:
        print("❌ Failed to fetch weather data")

asyncio.run(test_weather())
EOF
```

---

## Testing Phase 7: Machine Learning (Optional)

### Test Data Preparation

```bash
cd ../ml/training

# Test with mock data
python prepare_data.py
```

Check output in `ml/data/`:
- `prepared_data_train.pkl`
- `prepared_data_test.pkl`

### Test Model Training

```bash
# Train yield model (takes ~5-10 minutes)
python train_yield_model.py

# Check outputs in ml/models/
ls ../models/
# Should see:
# - yield_model.joblib
# - yield_model_metadata.json
# - feature_importance.png
# - predictions_plot.png
```

### Test Model Loading

```bash
python << 'EOF'
from joblib import load
import json

# Load model
model = load('../models/yield_model.joblib')
print(f"✅ Model loaded: {type(model)}")

# Load metadata
with open('../models/yield_model_metadata.json') as f:
    metadata = json.load(f)
    print(f"✅ Model trained: {metadata['training_date']}")
    print(f"✅ Features: {metadata['n_features']}")
EOF
```

---

## Testing Phase 8: Database Checks

### Test Database Structure

```bash
# Connect to PostgreSQL
docker exec -it terrascore-postgres psql -U terrascore -d terrascore

# Inside psql:
\dt                          # List tables
\d parcels                   # Describe parcels table
SELECT COUNT(*) FROM users;  # Count users
SELECT COUNT(*) FROM parcels; # Count parcels
SELECT COUNT(*) FROM credit_scores; # Count scores

# Check PostGIS
SELECT PostGIS_version();

# Check parcel geometries
SELECT cadastral_id, ST_AsText(centroid) FROM parcels LIMIT 5;

# Exit
\q
```

### Test Redis Cache

```bash
# Connect to Redis
docker exec -it terrascore-redis redis-cli

# Inside redis-cli:
PING                         # Should return PONG
KEYS *                       # List all keys
GET score:your-parcel-id     # Check cached score
INFO stats                   # Get statistics
EXIT
```

---

## Testing Phase 9: Automated Tests

### Backend Unit Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test
pytest tests/test_credit_score.py -v

# Open coverage report
# open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
```

### Frontend Tests (when implemented)

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

---

## Testing Phase 10: API Testing with Postman

### Import Postman Collection

Create a file `TerraScore.postman_collection.json`:

```json
{
  "info": {
    "name": "TerraScore API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Register",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"test@terrascore.rs\",\n  \"username\": \"testuser\",\n  \"password\": \"TestPass123!\",\n  \"full_name\": \"Test User\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "http://localhost:8000/api/v1/auth/register",
              "protocol": "http",
              "host": ["localhost"],
              "port": "8000",
              "path": ["api", "v1", "auth", "register"]
            }
          }
        },
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "urlencoded",
              "urlencoded": [
                {
                  "key": "username",
                  "value": "testuser",
                  "type": "text"
                },
                {
                  "key": "password",
                  "value": "TestPass123!",
                  "type": "text"
                }
              ]
            },
            "url": {
              "raw": "http://localhost:8000/api/v1/auth/token",
              "protocol": "http",
              "host": ["localhost"],
              "port": "8000",
              "path": ["api", "v1", "auth", "token"]
            }
          }
        }
      ]
    },
    {
      "name": "Parcels",
      "item": [
        {
          "name": "Create Parcel",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{token}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"cadastral_id\": \"TEST001\",\n  \"area_hectares\": 10.5,\n  \"current_crop_type\": \"maize\",\n  \"geometry\": {\n    \"type\": \"Polygon\",\n    \"coordinates\": [[\n      [20.4489, 44.7866],\n      [20.4589, 44.7866],\n      [20.4589, 44.7966],\n      [20.4489, 44.7966],\n      [20.4489, 44.7866]\n    ]]\n  }\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "http://localhost:8000/api/v1/parcels/",
              "protocol": "http",
              "host": ["localhost"],
              "port": "8000",
              "path": ["api", "v1", "parcels", ""]
            }
          }
        }
      ]
    }
  ]
}
```

Import this into Postman and test all endpoints!

---

## Testing Phase 11: Performance Testing (Optional)

### Load Testing with Locust

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class TerraScoreUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/token", data={
            "username": "testuser",
            "password": "TestPass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_parcels(self):
        self.client.get("/api/v1/parcels/", headers=self.headers)

    @task(2)
    def get_credit_score(self):
        # Replace with actual parcel ID
        self.client.get(f"/api/v1/credit-scores/{self.parcel_id}",
                       headers=self.headers)

    @task(1)
    def health_check(self):
        self.client.get("/health")
EOF

# Run load test
locust -f locustfile.py --host http://localhost:8000
```

Open: http://localhost:8089

---

## Common Issues & Troubleshooting

### Issue: "Connection refused" to PostgreSQL

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs terrascore-postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Issue: "Module not found" errors

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt --force-reinstall

cd ../frontend
npm install --force
```

### Issue: Alembic migration fails

```bash
# Check current migration
alembic current

# Downgrade and re-upgrade
alembic downgrade base
alembic upgrade head

# Or stamp to specific version
alembic stamp head
```

### Issue: Frontend won't start

```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run dev
```

### Issue: API returns 401 Unauthorized

```bash
# Token might be expired, get a new one
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123!"
```

---

## Success Checklist

After testing, you should have:

- ✅ All Docker services running
- ✅ Database with migrations applied
- ✅ Backend API responding at :8000
- ✅ Frontend dashboard at :3000
- ✅ Test user created
- ✅ Test parcel created
- ✅ Credit score calculated
- ✅ Dashboard showing parcel data
- ✅ API documentation accessible

---

## Next Steps

1. **Add real API keys** for Sentinel Hub and OpenWeather
2. **Train ML models** with actual historical data
3. **Configure Airflow** for automated pipelines
4. **Set up monitoring** with Grafana dashboards
5. **Deploy to production** server

---

## Need Help?

- Check logs: `docker-compose logs -f [service-name]`
- API docs: http://localhost:8000/docs
- Database: `docker exec -it terrascore-postgres psql -U terrascore -d terrascore`
- Redis: `docker exec -it terrascore-redis redis-cli`

Happy testing! 🚀
