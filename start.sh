#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Clase Analytics Platform Startup      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 is not installed${NC}"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js is not installed${NC}"
    exit 1
fi

# Setup backend
echo -e "${YELLOW}Setting up backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f "installed_deps" ]; then
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
    touch installed_deps
fi

cd ..

# Setup frontend
echo -e "${YELLOW}Setting up frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install -q
fi

cd ..

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo -e "${BLUE}Starting services...${NC}"
echo ""

# Start backend
echo -e "${GREEN}Backend:${NC} Starting FastAPI on http://localhost:8000"
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

sleep 2

# Start frontend
echo -e "${GREEN}Frontend:${NC} Starting Next.js on http://localhost:3000"
cd ../frontend
npm run dev &
FRONTEND_PID=$!

sleep 2

echo ""
echo -e "${GREEN}✓ Services started!${NC}"
echo ""
echo -e "${BLUE}Access the application:${NC}"
echo -e "  🌐 http://localhost:3000"
echo ""
echo -e "${BLUE}API:${NC}"
echo -e "  📡 http://localhost:8000/api/clases"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
