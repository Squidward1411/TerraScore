#!/bin/bash

# TerraScore Development Environment Setup
# Sets up everything needed to run TerraScore locally

set -e  # Exit on error

echo "🔧 TerraScore Development Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

# Check prerequisites
echo "Step 1: Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
    exit 1
fi
success "Docker found: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
success "Docker Compose found: $(docker-compose --version)"

if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi
success "Python found: $(python3 --version)"

if ! command -v node &> /dev/null; then
    error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi
success "Node.js found: $(node --version)"

# Start Docker services
echo ""
echo "Step 2: Starting Docker services..."
docker-compose up -d
info "Waiting for services to initialize (30 seconds)..."
sleep 30
success "Docker services started"

# Setup backend
echo ""
echo "Step 3: Setting up backend..."

cd backend

if [ ! -d "venv" ]; then
    info "Creating Python virtual environment..."
    python3 -m venv venv
fi

info "Activating virtual environment..."
source venv/bin/activate

info "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
success "Backend dependencies installed"

# Create .env file
if [ ! -f ".env" ]; then
    info "Creating .env file..."
    cat > .env << 'EOF'
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production-make-it-very-long-and-random-please
DATABASE_URL=postgresql://terrascore:terrascore_dev_password@localhost:5432/terrascore
TIMESCALE_URL=postgresql://terrascore:terrascore_dev_password@localhost:5433/timeseries
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
ML_MODEL_PATH=../ml/models
EOF
    success ".env file created"
else
    info ".env file already exists"
fi

# Run database migrations
echo ""
echo "Step 4: Running database migrations..."
info "Applying migrations..."
alembic upgrade head
success "Database migrations completed"

# Verify database
info "Verifying database..."
if docker exec terrascore-postgres psql -U terrascore -d terrascore -c "\dt" | grep -q "users"; then
    success "Database schema verified"
else
    error "Database schema not found"
    exit 1
fi

cd ..

# Setup frontend
echo ""
echo "Step 5: Setting up frontend..."

cd frontend

if [ ! -d "node_modules" ]; then
    info "Installing Node.js dependencies (this may take a few minutes)..."
    npm install
    success "Frontend dependencies installed"
else
    info "Node modules already installed"
fi

# Create .env.local
if [ ! -f ".env.local" ]; then
    info "Creating .env.local file..."
    cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_MAPBOX_TOKEN=your-token-here
EOF
    success ".env.local file created"
else
    info ".env.local file already exists"
fi

cd ..

# Setup ML directory
echo ""
echo "Step 6: Setting up ML directories..."
mkdir -p ml/models ml/data ml/training ml/notebooks
success "ML directories created"

# Summary
echo ""
echo "================================"
echo "✨ Setup Complete! ✨"
echo "================================"
echo ""
echo "🚀 To start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "🎨 To start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "🧪 To run tests:"
echo "   ./scripts/quick-test.sh"
echo ""
echo "📚 Resources:"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Frontend:     http://localhost:3000"
echo "   Grafana:      http://localhost:3001 (admin/admin)"
echo "   MinIO:        http://localhost:9001 (admin/minio_dev_password)"
echo "   Prometheus:   http://localhost:9090"
echo ""
echo "📖 Documentation:"
echo "   Testing Guide:    TESTING_GUIDE.md"
echo "   Quick Start:      QUICKSTART.md"
echo "   Phase 2 Summary:  PHASE2_SUMMARY.md"
echo ""
echo "⚙️  Optional Configuration:"
echo "   Get Sentinel Hub API key:    https://www.sentinel-hub.com/"
echo "   Get OpenWeather API key:     https://openweathermap.org/api"
echo "   Get Mapbox token (optional): https://www.mapbox.com/"
echo ""
echo "Happy coding! 🎉"
