#!/bin/bash

# Manufacturing Management App - macOS Stop Script
# This script stops both backend and frontend services

echo "🛑 Stopping Manufacturing Management Application..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Stop Backend
if [ -f "$SCRIPT_DIR/.backend.pid" ]; then
    BACKEND_PID=$(cat "$SCRIPT_DIR/.backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        rm "$SCRIPT_DIR/.backend.pid"
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${RED}Backend process not found${NC}"
        rm "$SCRIPT_DIR/.backend.pid"
    fi
else
    echo -e "${YELLOW}No backend PID file found${NC}"
fi

# Stop Frontend
if [ -f "$SCRIPT_DIR/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$SCRIPT_DIR/.frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        rm "$SCRIPT_DIR/.frontend.pid"
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    else
        echo -e "${RED}Frontend process not found${NC}"
        rm "$SCRIPT_DIR/.frontend.pid"
    fi
else
    echo -e "${YELLOW}No frontend PID file found${NC}"
fi

# Also kill any remaining processes on the ports
echo -e "${YELLOW}Cleaning up any remaining processes...${NC}"
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

echo ""
echo -e "${GREEN}✓ Application stopped successfully${NC}"
echo -e "${YELLOW}MongoDB is still running. To stop it:${NC}"
echo -e "  ${GREEN}brew services stop mongodb-community${NC}"
