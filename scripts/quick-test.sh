#!/bin/bash

# TerraScore Quick Test Script
# Tests the entire platform in one go

set -e  # Exit on error

echo "🚀 TerraScore Quick Test Script"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    error "Please run this script from the TerraScore root directory"
    exit 1
fi

# Step 1: Check Docker services
echo "Step 1: Checking Docker services..."
if docker-compose ps | grep -q "Up"; then
    success "Docker services are running"
else
    info "Starting Docker services..."
    docker-compose up -d
    info "Waiting for services to be ready..."
    sleep 10
    success "Docker services started"
fi

# Step 2: Check database
echo ""
echo "Step 2: Checking database..."
if docker exec terrascore-postgres psql -U terrascore -d terrascore -c "SELECT 1" > /dev/null 2>&1; then
    success "Database is accessible"
else
    error "Database is not accessible"
    exit 1
fi

# Step 3: Check if backend is running
echo ""
echo "Step 3: Checking backend API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    success "Backend API is running"
else
    info "Backend API is not running. You need to start it manually:"
    echo "  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    error "Backend API is not accessible"
    exit 1
fi

# Step 4: Test API health
echo ""
echo "Step 4: Testing API health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    success "API health check passed"
    echo "   Response: $HEALTH_RESPONSE"
else
    error "API health check failed"
    exit 1
fi

# Step 5: Check if user exists, create if not
echo ""
echo "Step 5: Setting up test user..."
TOKEN=""

# Try to login
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123!" 2>/dev/null)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    success "Test user exists, logged in successfully"
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
else
    info "Creating test user..."
    REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/register" \
      -H "Content-Type: application/json" \
      -d '{
        "email": "test@terrascore.rs",
        "username": "testuser",
        "password": "TestPass123!",
        "full_name": "Test User",
        "organization": "Test Bank"
      }')

    if echo "$REGISTER_RESPONSE" | grep -q "id"; then
        success "Test user created"

        # Now login
        LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
          -H "Content-Type: application/x-www-form-urlencoded" \
          -d "username=testuser&password=TestPass123!")

        TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
        success "Logged in and got access token"
    else
        error "Failed to create test user"
        echo "   Response: $REGISTER_RESPONSE"
        exit 1
    fi
fi

if [ -z "$TOKEN" ]; then
    error "Failed to get access token"
    exit 1
fi

# Step 6: Create test parcel
echo ""
echo "Step 6: Creating test parcel..."
PARCEL_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/parcels/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cadastral_id": "TEST_'$(date +%s)'",
    "parcel_name": "Quick Test Parcel",
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
    "has_irrigation": true
  }')

if echo "$PARCEL_RESPONSE" | grep -q "id"; then
    PARCEL_ID=$(echo "$PARCEL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    success "Test parcel created"
    echo "   Parcel ID: $PARCEL_ID"
else
    error "Failed to create test parcel"
    echo "   Response: $PARCEL_RESPONSE"
    exit 1
fi

# Step 7: Calculate credit score
echo ""
echo "Step 7: Calculating credit score..."
info "This may take a few seconds..."
SCORE_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/credit-scores/$PARCEL_ID" \
  -H "Authorization: Bearer $TOKEN")

if echo "$SCORE_RESPONSE" | grep -q "score"; then
    SCORE=$(echo "$SCORE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['score'])" 2>/dev/null || echo "N/A")
    RISK=$(echo "$SCORE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['risk_category'])" 2>/dev/null || echo "N/A")
    success "Credit score calculated successfully"
    echo "   Score: $SCORE"
    echo "   Risk Category: $RISK"
else
    error "Failed to calculate credit score"
    echo "   Response: $SCORE_RESPONSE"
    exit 1
fi

# Step 8: Test parcel list
echo ""
echo "Step 8: Testing parcel list endpoint..."
LIST_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/parcels/" \
  -H "Authorization: Bearer $TOKEN")

if echo "$LIST_RESPONSE" | grep -q "items"; then
    TOTAL=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "0")
    success "Parcel list retrieved"
    echo "   Total parcels: $TOTAL"
else
    error "Failed to get parcel list"
    exit 1
fi

# Step 9: Check frontend (if running)
echo ""
echo "Step 9: Checking frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    success "Frontend is accessible at http://localhost:3000"
else
    info "Frontend is not running. Start it with:"
    echo "  cd frontend && npm run dev"
fi

# Summary
echo ""
echo "================================"
echo "✨ All tests passed! ✨"
echo "================================"
echo ""
echo "📊 Test Summary:"
echo "   ✅ Docker services running"
echo "   ✅ Database accessible"
echo "   ✅ Backend API healthy"
echo "   ✅ User authentication working"
echo "   ✅ Parcel creation working"
echo "   ✅ Credit score calculation working"
echo ""
echo "🌐 Access Points:"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Frontend:  http://localhost:3000"
echo "   Grafana:   http://localhost:3001 (admin/admin)"
echo ""
echo "🔑 Test Credentials:"
echo "   Username:  testuser"
echo "   Password:  TestPass123!"
echo ""
echo "📝 Your Test Parcel:"
echo "   ID:        $PARCEL_ID"
echo "   Score:     $SCORE"
echo "   Risk:      $RISK"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Login with test credentials"
echo "   3. View your test parcel in the dashboard"
echo ""
echo "Happy testing! 🚀"
