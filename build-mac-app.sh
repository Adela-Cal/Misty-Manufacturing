#!/bin/bash

###############################################################################
# Misty Manufacturing - Desktop App Builder for Mac
# This script builds the Mac installer
###############################################################################

echo "========================================"
echo "  Misty Manufacturing Desktop Builder"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

# Check if Yarn is installed
if ! command -v yarn &> /dev/null; then
    echo "Installing Yarn..."
    npm install -g yarn
fi

echo ""
echo "Step 1: Get NAS IP Address"
read -p "Enter your NAS IP address (e.g., 192.168.1.100): " NAS_IP

echo ""
echo "Step 2: Updating configuration..."
cd frontend
echo "REACT_APP_BACKEND_URL=http://${NAS_IP}:8001" > .env
echo "Configuration updated!"

echo ""
echo "Step 3: Installing dependencies..."
yarn install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Step 4: Building React app..."
yarn build
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build React app"
    exit 1
fi

echo ""
echo "Step 5: Building Mac installer..."
yarn electron:build --mac
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build Mac installer"
    exit 1
fi

echo ""
echo "========================================"
echo "  BUILD COMPLETE!"
echo "========================================"
echo ""
echo "Installer location: frontend/dist/Misty Manufacturing-1.0.0.dmg"
echo ""
echo "Next steps:"
echo "  1. Copy the DMG to your client Macs"
echo "  2. Double-click the DMG and drag app to Applications"
echo "  3. Launch the app and login"
echo ""
