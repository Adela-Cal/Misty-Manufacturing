#!/bin/bash

###############################################################################
# Misty Manufacturing - Automated NAS Setup Script
# 
# This script automatically configures your Netgear RN104 NAS as the server
# for the Misty Manufacturing application.
#
# Prerequisites:
# - SSH access to your NAS
# - Admin credentials for your NAS
# - NAS on local network
#
# Usage:
#   ./setup-nas-server.sh
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/nas-setup.log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
clear
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          MISTY MANUFACTURING - NAS SERVER SETUP              ║
║                                                               ║
║        Automated Installation for Netgear RN104 NAS          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF

echo ""
log "Starting NAS server setup..."
log "Log file: $LOG_FILE"
echo ""

# Step 1: Get NAS connection details
info "Step 1: NAS Connection Details"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

read -p "Enter NAS IP address (e.g., 192.168.1.100): " NAS_IP
read -p "Enter NAS SSH username (usually 'admin'): " NAS_USER
read -sp "Enter NAS password: " NAS_PASS
echo ""

# Test SSH connection
info "Testing SSH connection to NAS..."
if sshpass -p "$NAS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$NAS_USER@$NAS_IP" "echo 'SSH connection successful'" > /dev/null 2>&1; then
    log "✅ SSH connection successful"
else
    error "❌ Cannot connect to NAS via SSH. Please check IP, username, and password."
fi

echo ""

# Step 2: Check NAS system
info "Step 2: Checking NAS System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

NAS_OS=$(sshpass -p "$NAS_PASS" ssh "$NAS_USER@$NAS_IP" "cat /etc/os-release 2>/dev/null || echo 'Unknown'")
log "NAS Operating System: $NAS_OS"

# Check available space
AVAILABLE_SPACE=$(sshpass -p "$NAS_PASS" ssh "$NAS_USER@$NAS_IP" "df -h / | tail -1 | awk '{print \$4}'")
log "Available disk space: $AVAILABLE_SPACE"

echo ""

# Step 3: Upload application files
info "Step 3: Uploading Application Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create application directory on NAS
log "Creating application directory on NAS..."
sshpass -p "$NAS_PASS" ssh "$NAS_USER@$NAS_IP" "mkdir -p /volume1/misty-manufacturing/{backend,frontend,uploads,backups}"

# Upload backend files
log "Uploading backend files..."
sshpass -p "$NAS_PASS" scp -r "$SCRIPT_DIR/../backend" "$NAS_USER@$NAS_IP:/volume1/misty-manufacturing/" 2>&1 | tee -a "$LOG_FILE"

# Build and upload frontend
log "Building frontend..."
cd "$SCRIPT_DIR/../frontend"
npm run build 2>&1 | tee -a "$LOG_FILE"

log "Uploading frontend build..."
sshpass -p "$NAS_PASS" scp -r "$SCRIPT_DIR/../frontend/build" "$NAS_USER@$NAS_IP:/volume1/misty-manufacturing/frontend/" 2>&1 | tee -a "$LOG_FILE"

echo ""

# Step 4: Install dependencies on NAS
info "Step 4: Installing Dependencies on NAS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

INSTALL_SCRIPT=$(cat << 'SCRIPT_EOF'
#!/bin/bash
set -e

echo "Installing Python 3..."
if ! command -v python3 &> /dev/null; then
    # Try to install Python (method varies by NAS OS)
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    elif command -v apk &> /dev/null; then
        apk add python3 py3-pip
    else
        echo "Please install Python 3 manually"
        exit 1
    fi
fi

echo "Installing MongoDB..."
if ! command -v mongod &> /dev/null; then
    # MongoDB installation varies by system
    echo "Please install MongoDB manually following: https://docs.mongodb.com/manual/installation/"
fi

echo "Setting up Python virtual environment..."
cd /volume1/misty-manufacturing/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Creating systemd service..."
cat > /etc/systemd/system/misty-backend.service << 'SERVICE_EOF'
[Unit]
Description=Misty Manufacturing Backend
After=network.target mongodb.service

[Service]
Type=simple
User=admin
WorkingDirectory=/volume1/misty-manufacturing/backend
Environment="PATH=/volume1/misty-manufacturing/backend/venv/bin"
ExecStart=/volume1/misty-manufacturing/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable misty-backend
systemctl start misty-backend

echo "Installing nginx..."
if ! command -v nginx &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        apt-get install -y nginx
    elif command -v apk &> /dev/null; then
        apk add nginx
    fi
fi

echo "Configuring nginx..."
cat > /etc/nginx/sites-available/misty-manufacturing << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        root /volume1/misty-manufacturing/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    client_max_body_size 50M;
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/misty-manufacturing /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo "Setup complete!"
SCRIPT_EOF
)

# Upload and execute installation script
log "Running installation script on NAS..."
echo "$INSTALL_SCRIPT" | sshpass -p "$NAS_PASS" ssh "$NAS_USER@$NAS_IP" "cat > /tmp/install.sh && chmod +x /tmp/install.sh && bash /tmp/install.sh" 2>&1 | tee -a "$LOG_FILE"

echo ""

# Step 5: Configure environment
info "Step 5: Configuring Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create .env file
ENV_CONTENT="MONGO_URL=mongodb://localhost:27017
DB_NAME=misty_manufacturing
SECRET_KEY=$(openssl rand -hex 32)
PORT=8001
HOST=0.0.0.0
FRONTEND_URL=http://$NAS_IP
UPLOAD_DIR=/volume1/misty-manufacturing/uploads"

echo "$ENV_CONTENT" | sshpass -p "$NAS_PASS" ssh "$NAS_USER@$NAS_IP" "cat > /volume1/misty-manufacturing/backend/.env"

log "✅ Environment configured"

echo ""

# Step 6: Start services
info "Step 6: Starting Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sshpass -p "$NAS_PASS" ssh "$NAS_USER@$NAS_IP" "systemctl start misty-backend && systemctl start nginx"

log "✅ Services started"

echo ""

# Step 7: Verify installation
info "Step 7: Verifying Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test backend
if curl -s "http://$NAS_IP/api/health" > /dev/null 2>&1; then
    log "✅ Backend is responding"
else
    warn "⚠️  Backend health check failed"
fi

# Test frontend
if curl -s "http://$NAS_IP" > /dev/null 2>&1; then
    log "✅ Frontend is accessible"
else
    warn "⚠️  Frontend is not accessible"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✨ NAS SETUP COMPLETE! ✨"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
info "Your Misty Manufacturing server is now running on your NAS!"
echo ""
echo "Server Address: http://$NAS_IP"
echo "Backend API: http://$NAS_IP/api"
echo ""
info "Next Steps:"
echo "1. Open the Mac app (Misty Manufacturing.app)"
echo "2. When prompted, enter your NAS IP: $NAS_IP"
echo "3. Login with your credentials"
echo ""
info "To check server status:"
echo "  ssh $NAS_USER@$NAS_IP"
echo "  sudo systemctl status misty-backend"
echo "  sudo systemctl status nginx"
echo ""
log "Setup log saved to: $LOG_FILE"
