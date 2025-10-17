#!/bin/bash

# Network Setup Test Script
# Run this on the SERVER Mac to verify network accessibility

echo "🌐 Testing Network Setup for Manufacturing Management App"
echo "=========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get all IP addresses
echo -e "${YELLOW}Step 1: Finding your Mac's IP addresses...${NC}"
echo ""

# WiFi IP
WIFI_IP=$(ipconfig getifaddr en0 2>/dev/null)
if [ -n "$WIFI_IP" ]; then
    echo -e "${GREEN}✓ WiFi IP Address: $WIFI_IP${NC}"
    PRIMARY_IP=$WIFI_IP
else
    echo -e "${YELLOW}  WiFi not connected${NC}"
fi

# Ethernet IP  
ETH_IP=$(ipconfig getifaddr en1 2>/dev/null)
if [ -n "$ETH_IP" ]; then
    echo -e "${GREEN}✓ Ethernet IP Address: $ETH_IP${NC}"
    PRIMARY_IP=$ETH_IP
else
    echo -e "${YELLOW}  Ethernet not connected${NC}"
fi

if [ -z "$PRIMARY_IP" ]; then
    echo -e "${RED}✗ No network connection found!${NC}"
    echo "  Please connect to WiFi or Ethernet first."
    exit 1
fi

echo ""
echo -e "${GREEN}Primary IP to use: $PRIMARY_IP${NC}"
echo ""

# Check if MongoDB is running
echo -e "${YELLOW}Step 2: Checking MongoDB...${NC}"
if pgrep -x "mongod" > /dev/null; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}✗ MongoDB is not running${NC}"
    echo "  Start it with: brew services start mongodb-community"
fi
echo ""

# Check if backend is running
echo -e "${YELLOW}Step 3: Checking Backend Server...${NC}"
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Backend is running on port 8001${NC}"
    
    # Check if it's listening on all interfaces
    if lsof -Pi :8001 -sTCP:LISTEN | grep -q "\*:8001"; then
        echo -e "${GREEN}✓ Backend is accessible from network (listening on 0.0.0.0)${NC}"
    else
        echo -e "${RED}✗ Backend is only accessible locally (127.0.0.1)${NC}"
        echo "  Fix: Start backend with: uvicorn server:app --host 0.0.0.0 --port 8001"
    fi
else
    echo -e "${RED}✗ Backend is not running${NC}"
    echo "  Start it with: ./start.sh"
fi
echo ""

# Test backend locally
echo -e "${YELLOW}Step 4: Testing Backend Connection...${NC}"
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend responding on localhost${NC}"
else
    echo -e "${RED}✗ Backend not responding on localhost${NC}"
fi

# Test backend from network IP
if curl -s http://$PRIMARY_IP:8001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend responding on network IP ($PRIMARY_IP)${NC}"
else
    echo -e "${RED}✗ Backend not responding on network IP${NC}"
    echo "  This may be a firewall issue"
fi
echo ""

# Check firewall
echo -e "${YELLOW}Step 5: Checking Firewall...${NC}"
if /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate | grep -q "enabled"; then
    echo -e "${YELLOW}⚠ Firewall is enabled${NC}"
    echo "  You may need to allow Python in:"
    echo "  System Preferences → Security & Privacy → Firewall → Firewall Options"
else
    echo -e "${GREEN}✓ Firewall is disabled (easier for testing)${NC}"
fi
echo ""

# Summary
echo "=========================================================="
echo -e "${GREEN}SETUP SUMMARY${NC}"
echo "=========================================================="
echo ""
echo "Share this information with your team:"
echo ""
echo -e "${YELLOW}Server IP Address:${NC} $PRIMARY_IP"
echo -e "${YELLOW}Application URL:${NC} http://$PRIMARY_IP:3000"
echo -e "${YELLOW}Backend API URL:${NC} http://$PRIMARY_IP:8001"
echo ""
echo "Test from other computers:"
echo "  1. Open browser"
echo "  2. Go to: http://$PRIMARY_IP:3000"
echo "  3. Login with: Callum / Peach7510"
echo ""
echo "=========================================================="
echo ""

# Create a quick reference file
cat > network-info.txt << EOF
Manufacturing Management App - Network Information
===================================================

Server IP Address: $PRIMARY_IP
Application URL: http://$PRIMARY_IP:3000
Backend API URL: http://$PRIMARY_IP:8001

Login Credentials:
  Username: Callum
  Password: Peach7510

For client computers:
  1. Open any web browser
  2. Go to: http://$PRIMARY_IP:3000
  3. Bookmark this page for easy access

Server Location: $(hostname)
Last Updated: $(date)
EOF

echo -e "${GREEN}✓ Network information saved to: network-info.txt${NC}"
echo ""
