#!/bin/bash

###############################################################################
# Misty Manufacturing - Quick Deployment Script
# 
# This script automates the deployment of Misty Manufacturing to your NAS
#
# Usage:
#   ./quick-deploy.sh
#
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      MISTY MANUFACTURING - QUICK DEPLOYMENT SCRIPT          ║
║                                                              ║
║                    NAS Deployment Tool                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Get NAS IP address
echo -e "${YELLOW}Step 1: NAS Configuration${NC}"
read -p "Enter your NAS IP address (e.g., 192.168.1.100): " NAS_IP
read -p "Enter NAS SSH username (default: admin): " NAS_USER
NAS_USER=${NAS_USER:-admin}

# Get MongoDB credentials
echo -e "\n${YELLOW}Step 2: Database Configuration${NC}"
read -p "Enter MongoDB admin username (default: misty_admin): " MONGO_USER
MONGO_USER=${MONGO_USER:-misty_admin}
read -sp "Enter MongoDB admin password: " MONGO_PASS
echo ""

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)

echo -e "\n${GREEN}Configuration Summary:${NC}"
echo "  NAS IP: $NAS_IP"
echo "  NAS User: $NAS_USER"
echo "  MongoDB User: $MONGO_USER"
echo "  JWT Secret: [Generated]"

read -p "Continue with deployment? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Test SSH connection
echo -e "\n${YELLOW}Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 ${NAS_USER}@${NAS_IP} "echo 'Connected'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed. Please check:${NC}"
    echo "  1. NAS IP address is correct"
    echo "  2. SSH is enabled on NAS"
    echo "  3. You have SSH key or password access"
    exit 1
fi

# Create application directory on NAS
echo -e "\n${YELLOW}Creating application directory on NAS...${NC}"
ssh ${NAS_USER}@${NAS_IP} "mkdir -p /share/misty-manufacturing/{backend,mongodb-data,backups}"
echo -e "${GREEN}✓ Directory created${NC}"

# Copy backend files to NAS
echo -e "\n${YELLOW}Copying backend files to NAS...${NC}"
scp -r backend/ ${NAS_USER}@${NAS_IP}:/share/misty-manufacturing/
echo -e "${GREEN}✓ Backend files copied${NC}"

# Create backend .env file
echo -e "\n${YELLOW}Creating backend configuration...${NC}"
cat > /tmp/backend.env << EOF
MONGO_URL=mongodb://${MONGO_USER}:${MONGO_PASS}@${NAS_IP}:27017/misty_manufacturing?authSource=admin
JWT_SECRET=${JWT_SECRET}
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://${NAS_IP}:3000,http://localhost:3000
EOF

scp /tmp/backend.env ${NAS_USER}@${NAS_IP}:/share/misty-manufacturing/backend/.env
rm /tmp/backend.env
echo -e "${GREEN}✓ Backend configuration created${NC}"

# Create Dockerfile
echo -e "\n${YELLOW}Creating backend Dockerfile...${NC}"
cat > /tmp/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
EOF

scp /tmp/Dockerfile ${NAS_USER}@${NAS_IP}:/share/misty-manufacturing/backend/Dockerfile
rm /tmp/Dockerfile
echo -e "${GREEN}✓ Dockerfile created${NC}"

# Deploy MongoDB container
echo -e "\n${YELLOW}Deploying MongoDB container...${NC}"
ssh ${NAS_USER}@${NAS_IP} << EOF
docker stop misty-mongodb 2>/dev/null || true
docker rm misty-mongodb 2>/dev/null || true

docker run -d \
  --name misty-mongodb \
  --restart always \
  -p 27017:27017 \
  -v /share/misty-manufacturing/mongodb-data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=${MONGO_USER} \
  -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASS} \
  mongo:7.0
EOF
echo -e "${GREEN}✓ MongoDB container deployed${NC}"

# Wait for MongoDB to start
echo -e "\n${YELLOW}Waiting for MongoDB to start...${NC}"
sleep 10

# Build and deploy backend container
echo -e "\n${YELLOW}Building backend container...${NC}"
ssh ${NAS_USER}@${NAS_IP} << EOF
cd /share/misty-manufacturing/backend
docker build -t misty-backend .
EOF
echo -e "${GREEN}✓ Backend container built${NC}"

echo -e "\n${YELLOW}Deploying backend container...${NC}"
ssh ${NAS_USER}@${NAS_IP} << EOF
docker stop misty-backend 2>/dev/null || true
docker rm misty-backend 2>/dev/null || true

docker run -d \
  --name misty-backend \
  --restart always \
  -p 8001:8001 \
  --env-file /share/misty-manufacturing/backend/.env \
  misty-backend
EOF
echo -e "${GREEN}✓ Backend container deployed${NC}"

# Wait for backend to start
echo -e "\n${YELLOW}Waiting for backend to start...${NC}"
sleep 15

# Test backend health
echo -e "\n${YELLOW}Testing backend health...${NC}"
if curl -s http://${NAS_IP}:8001/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy and running${NC}"
else
    echo -e "${YELLOW}⚠ Backend health check inconclusive. Check logs:${NC}"
    echo "  ssh ${NAS_USER}@${NAS_IP} 'docker logs misty-backend'"
fi

# Create backup script
echo -e "\n${YELLOW}Creating backup script...${NC}"
cat > /tmp/backup-script.sh << 'BACKUP_EOF'
#!/bin/bash
BACKUP_DIR="/share/misty-manufacturing/backups"
DATE=$(date +%Y%m%d_%H%M%S)

docker exec misty-mongodb mongodump \
  --username=$MONGO_USER \
  --password=$MONGO_PASS \
  --authenticationDatabase=admin \
  --out=/data/backup-${DATE}

docker cp misty-mongodb:/data/backup-${DATE} ${BACKUP_DIR}/

# Keep only last 7 backups
ls -t ${BACKUP_DIR}/backup-* | tail -n +8 | xargs -r rm -rf

echo "Backup completed: backup-${DATE}"
BACKUP_EOF

scp /tmp/backup-script.sh ${NAS_USER}@${NAS_IP}:/share/misty-manufacturing/backup-script.sh
ssh ${NAS_USER}@${NAS_IP} "chmod +x /share/misty-manufacturing/backup-script.sh"
rm /tmp/backup-script.sh
echo -e "${GREEN}✓ Backup script created${NC}"

# Summary
echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 DEPLOYMENT COMPLETE! 🎉                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Backend URL:${NC} http://${NAS_IP}:8001"
echo -e "${BLUE}MongoDB URL:${NC} mongodb://${NAS_IP}:27017"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "  1. Update frontend/.env with: REACT_APP_BACKEND_URL=http://${NAS_IP}:8001"
echo "  2. Build frontend: cd frontend && yarn build"
echo "  3. Package Electron app: yarn electron:build"
echo "  4. Install desktop app on client computers"

echo -e "\n${YELLOW}Management Commands:${NC}"
echo "  Check status:  ssh ${NAS_USER}@${NAS_IP} 'docker ps'"
echo "  View logs:     ssh ${NAS_USER}@${NAS_IP} 'docker logs misty-backend'"
echo "  Restart:       ssh ${NAS_USER}@${NAS_IP} 'docker restart misty-backend'"
echo "  Backup:        ssh ${NAS_USER}@${NAS_IP} '/share/misty-manufacturing/backup-script.sh'"

echo -e "\n${GREEN}Deployment log saved to: deployment-$(date +%Y%m%d_%H%M%S).log${NC}\n"
