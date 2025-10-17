#!/bin/bash

# Manufacturing Management App - macOS Startup Script
# This script starts both backend and frontend services

echo "🍎 Starting Manufacturing Management Application for macOS..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if MongoDB is running
echo -e "${YELLOW}Checking MongoDB...${NC}"
if ! brew services list | grep -q "mongodb-community.*started"; then
    echo -e "${YELLOW}Starting MongoDB...${NC}"
    brew services start mongodb-community
    sleep 3
else
    echo -e "${GREEN}✓ MongoDB is running${NC}"
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create uploads directory if it doesn't exist
echo -e "${YELLOW}Setting up upload directories...${NC}"
mkdir -p "$SCRIPT_DIR/uploads/logos"
mkdir -p "$SCRIPT_DIR/uploads/documents"
echo -e "${GREEN}✓ Upload directories ready${NC}"

# Start Backend
echo -e "${YELLOW}Starting Backend Server...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and start backend
source venv/bin/activate

# Install dependencies if needed
if [ ! -f ".dependencies_installed" ]; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r requirements.txt
    touch .dependencies_installed
fi

# Start backend in background
echo -e "${GREEN}✓ Starting Backend on port 8001 (accessible from network)${NC}"
uvicorn server:app --host 0.0.0.0 --port 8001 > "$SCRIPT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$SCRIPT_DIR/.backend.pid"

# Wait for backend to start
sleep 3

# Start Frontend
echo -e "${YELLOW}Starting Frontend Server...${NC}"
cd "$SCRIPT_DIR/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    yarn install
fi

# Start frontend in background
echo -e "${GREEN}✓ Starting Frontend on port 3000${NC}"
yarn start > "$SCRIPT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend.pid"

# Wait for services to fully start
sleep 5

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ Manufacturing Management App is Running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Access the application at:${NC}"
echo -e "  ${GREEN}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Login Credentials:${NC}"
echo -e "  Username: ${GREEN}Callum${NC}"
echo -e "  Password: ${GREEN}Peach7510${NC}"
echo ""
echo -e "${YELLOW}Share with your team:${NC}"
echo -e "  1. Find your Mac's IP: ${GREEN}ipconfig getifaddr en0${NC}"
echo -e "  2. Share URL: ${GREEN}http://YOUR-IP:3000${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  ${GREEN}tail -f $SCRIPT_DIR/backend.log${NC}"
echo -e "  Frontend: ${GREEN}tail -f $SCRIPT_DIR/frontend.log${NC}"
echo ""
echo -e "${YELLOW}To stop the application:${NC}"
echo -e "  ${GREEN}./stop.sh${NC}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
