# iOS App Deployment Guide
## Misty Manufacturing Application

**Date:** September 2025  
**Target Device:** iPad/iPhone  
**Deployment Location:** Netgear RN104 NAS (Local Network)

---

## Overview

This guide explains how to deploy the Misty Manufacturing web application as a standalone iOS app that can be installed on iPads and iPhones, with the backend running on your Netgear RN104 NAS device.

---

## Architecture Decision

### Option A: Progressive Web App (PWA) ⭐ RECOMMENDED
**Timeline:** 2-4 hours  
**Cost:** Low  
**Maintenance:** Easy

**Pros:**
- ✅ Works on any modern iOS device
- ✅ Installable to home screen
- ✅ Offline capabilities with service workers
- ✅ No App Store approval needed
- ✅ Instant updates (no app store review wait)
- ✅ Works with existing codebase (no rewrite)

**Cons:**
- ❌ Not in App Store (must install via Safari)
- ❌ Limited access to native features
- ❌ Requires internet connection to NAS

---

### Option B: Capacitor Hybrid App ⭐⭐ BEST BALANCE
**Timeline:** 1-2 weeks  
**Cost:** Medium  
**Maintenance:** Moderate

**Pros:**
- ✅ Wraps existing React app
- ✅ Can be published to App Store
- ✅ Access to native iOS features (camera, push notifications, etc.)
- ✅ Better offline support
- ✅ Professional app experience
- ✅ No full rewrite needed

**Cons:**
- ❌ Requires Apple Developer account ($99/year)
- ❌ Requires macOS for building
- ❌ App Store review process (1-2 weeks)

**Implementation Steps:**
1. Install Capacitor in React app
2. Configure iOS project
3. Build with Xcode
4. Submit to App Store

---

### Option C: Native Swift App
**Timeline:** 3-6 months  
**Cost:** Very High  
**Maintenance:** Ongoing development team

**Pros:**
- ✅ Best performance
- ✅ Full access to all iOS features
- ✅ Best user experience

**Cons:**
- ❌ Complete rewrite of frontend
- ❌ Requires Swift/SwiftUI developers
- ❌ Must maintain two codebases (web + iOS)
- ❌ Very expensive

**Recommendation:** Not necessary for this application

---

## NAS Deployment Guide

### Current Setup
- **Application:** Misty Manufacturing (React + FastAPI + MongoDB)
- **NAS Device:** Netgear RN104
- **Network:** Local network only
- **Users:** 5-15 concurrent users expected

### Requirements Checklist

#### NAS Hardware Requirements
- ✅ Netgear RN104 with sufficient storage
- ✅ Network connection (Ethernet recommended)
- ✅ SSH access enabled
- ⚠️ No Docker support (will run without containers)

#### Software Requirements on NAS
- Python 3.9+ (for FastAPI backend)
- MongoDB 5.0+ (database)
- Node.js 18+ (for React build)
- nginx or similar (web server)

---

## Step-by-Step Deployment to NAS

### Phase 1: Prepare NAS Environment

#### 1.1 Install Required Software

```bash
# SSH into your NAS
ssh admin@nas-ip-address

# Install Python 3.11
# (Method depends on NAS Linux distribution)
# For Debian-based:
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install MongoDB
# Follow MongoDB installation for your NAS OS
# https://docs.mongodb.com/manual/installation/

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install nginx
sudo apt install nginx
```

#### 1.2 Create Application Directory

```bash
# Create app directory
sudo mkdir -p /opt/misty-manufacturing
sudo chown $USER:$USER /opt/misty-manufacturing
cd /opt/misty-manufacturing
```

---

### Phase 2: Deploy Backend

#### 2.1 Transfer Backend Files

```bash
# From your local machine, copy backend files to NAS
scp -r /app/backend admin@nas-ip:/opt/misty-manufacturing/

# SSH into NAS
ssh admin@nas-ip-address
cd /opt/misty-manufacturing/backend
```

#### 2.2 Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

```bash
# Create .env file
cat > .env << 'EOF'
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=misty_manufacturing

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Backend Configuration
PORT=8001
HOST=0.0.0.0

# Frontend URL (will be your NAS IP)
FRONTEND_URL=http://YOUR_NAS_IP:3000

# File Upload
UPLOAD_DIR=/opt/misty-manufacturing/uploads
EOF

# Replace YOUR_NAS_IP with actual NAS IP address
sed -i 's/YOUR_NAS_IP/192.168.1.100/g' .env  # Example IP
```

#### 2.4 Create Systemd Service for Backend

```bash
sudo cat > /etc/systemd/system/misty-backend.service << 'EOF'
[Unit]
Description=Misty Manufacturing Backend
After=network.target mongodb.service

[Service]
Type=simple
User=misty
WorkingDirectory=/opt/misty-manufacturing/backend
Environment="PATH=/opt/misty-manufacturing/backend/venv/bin"
ExecStart=/opt/misty-manufacturing/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable misty-backend
sudo systemctl start misty-backend
sudo systemctl status misty-backend
```

---

### Phase 3: Deploy Frontend

#### 3.1 Build React App

```bash
# On your local machine (or on NAS if it has enough resources)
cd /app/frontend

# Update .env with NAS IP
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=http://192.168.1.100:8001
EOF

# Build production bundle
npm install
npm run build
# This creates /app/frontend/build directory
```

#### 3.2 Transfer Frontend Build to NAS

```bash
# From local machine
scp -r /app/frontend/build admin@nas-ip:/opt/misty-manufacturing/frontend-build/
```

#### 3.3 Configure Nginx

```bash
# SSH into NAS
ssh admin@nas-ip-address

# Create nginx configuration
sudo cat > /etc/nginx/sites-available/misty-manufacturing << 'EOF'
server {
    listen 80;
    server_name YOUR_NAS_IP;  # or domain name if you have one
    
    # Frontend - React build
    location / {
        root /opt/misty-manufacturing/frontend-build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Increase upload size for file uploads
    client_max_body_size 50M;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/misty-manufacturing /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

### Phase 4: Configure MongoDB

#### 4.1 Create Database and User

```bash
# Connect to MongoDB
mongosh

# Switch to admin database
use admin

# Create database user
db.createUser({
  user: "misty_user",
  pwd: "secure_password_here",
  roles: [
    { role: "readWrite", db: "misty_manufacturing" }
  ]
})

# Switch to application database
use misty_manufacturing

# Import initial data (if you have a dump)
# On local machine:
mongodump --db=misty_manufacturing --out=/tmp/misty-dump

# Transfer to NAS and import:
scp -r /tmp/misty-dump admin@nas-ip:/tmp/
ssh admin@nas-ip-address
mongorestore --db=misty_manufacturing /tmp/misty-dump/misty_manufacturing
```

#### 4.2 Update Backend .env with MongoDB Credentials

```bash
# Update backend .env
nano /opt/misty-manufacturing/backend/.env

# Change MONGO_URL to:
MONGO_URL=mongodb://misty_user:secure_password_here@localhost:27017

# Restart backend
sudo systemctl restart misty-backend
```

---

## Making it a Progressive Web App (PWA)

### PWA Implementation

#### 1. Create manifest.json

Create `/app/frontend/public/manifest.json`:
```json
{
  "name": "Misty Manufacturing",
  "short_name": "Misty Mfg",
  "description": "Manufacturing management system",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1e40af",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

#### 2. Create Service Worker

Create `/app/frontend/public/service-worker.js`:
```javascript
const CACHE_NAME = 'misty-manufacturing-v1';
const urlsToCache = [
  '/',
  '/static/js/main.js',
  '/static/css/main.css',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
```

#### 3. Register Service Worker

Update `/app/frontend/src/index.js`:
```javascript
// At the bottom of index.js
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => console.log('SW registered:', registration))
      .catch(error => console.log('SW registration failed:', error));
  });
}
```

#### 4. Add to Home Screen Instructions

Users can install the PWA by:
1. Opening Safari on iPad/iPhone
2. Navigate to http://YOUR_NAS_IP
3. Tap the Share button (square with arrow)
4. Tap "Add to Home Screen"
5. Name it "Misty Manufacturing"
6. Tap "Add"

The app icon will appear on the home screen like a native app!

---

## Capacitor Implementation (Optional - for App Store)

### If you choose Capacitor:

#### 1. Install Capacitor

```bash
cd /app/frontend
npm install @capacitor/core @capacitor/cli
npm install @capacitor/ios
npx cap init "Misty Manufacturing" "com.misty.manufacturing"
```

#### 2. Build and Add iOS Platform

```bash
npm run build
npx cap add ios
npx cap copy
npx cap open ios  # Opens Xcode
```

#### 3. Configure in Xcode
- Set app icon and splash screen
- Configure capabilities (networking, storage)
- Set bundle identifier
- Add Apple Developer account

#### 4. Build and Submit
- Build archive in Xcode
- Upload to App Store Connect
- Submit for review

---

## Network Configuration

### For Local Network Access

#### Option 1: Static IP on NAS
```bash
# Set static IP on your NAS
# Via NAS web interface or:
sudo nano /etc/network/interfaces

# Example:
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 8.8.4.4
```

#### Option 2: Reserve IP in Router
- Login to your router
- Find NAS MAC address
- Reserve/assign static IP for NAS MAC address

### For Remote Access (Optional)

#### VPN Setup (RECOMMENDED)
- Setup VPN server on router or NAS
- Users connect via VPN to access app remotely
- Most secure option

#### Port Forwarding (NOT RECOMMENDED for production)
- Forward port 80 from router to NAS
- Security risk - requires proper firewall rules

---

## Security Considerations

### Essential Security Measures

#### 1. HTTPS/SSL (IMPORTANT)
```bash
# Install certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate (requires public domain)
sudo certbot --nginx -d your-domain.com

# Or create self-signed certificate for local use
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt
```

#### 2. Firewall Configuration
```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

#### 3. MongoDB Security
```bash
# Enable MongoDB authentication
sudo nano /etc/mongod.conf

# Add:
security:
  authorization: enabled

# Restart MongoDB
sudo systemctl restart mongod
```

#### 4. Regular Backups
```bash
# Create backup script
cat > /opt/misty-manufacturing/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/misty-manufacturing/backups"
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db=misty_manufacturing --out=$BACKUP_DIR/mongo_$DATE

# Backup uploaded files
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/misty-manufacturing/uploads

# Keep only last 30 days of backups
find $BACKUP_DIR -type f -mtime +30 -delete
EOF

chmod +x /opt/misty-manufacturing/backup.sh

# Add to cron (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /opt/misty-manufacturing/backup.sh
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Check backend status
sudo systemctl status misty-backend

# Check backend logs
sudo journalctl -u misty-backend -f

# Check MongoDB status
sudo systemctl status mongod

# Check nginx status
sudo systemctl status nginx

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Tuning

#### MongoDB
```javascript
// Create indexes for better performance
use misty_manufacturing

db.orders.createIndex({ "order_number": 1 }, { unique: true })
db.orders.createIndex({ "client_id": 1 })
db.orders.createIndex({ "current_stage": 1 })
db.orders.createIndex({ "created_at": -1 })

db.raw_substrate_stock.createIndex({ "product_id": 1, "client_id": 1 })

db.timesheets.createIndex({ "employee_id": 1, "status": 1 })
db.leave_requests.createIndex({ "employee_id": 1, "status": 1 })
```

---

## Troubleshooting

### Common Issues

#### Backend won't start
```bash
# Check logs
sudo journalctl -u misty-backend -n 50

# Common fixes:
# 1. Check MongoDB is running
sudo systemctl status mongod

# 2. Check Python dependencies
cd /opt/misty-manufacturing/backend
source venv/bin/activate
pip install -r requirements.txt

# 3. Check .env file
cat .env
```

#### Frontend shows "Network Error"
```bash
# Check nginx configuration
sudo nginx -t

# Check backend is accessible
curl http://localhost:8001/api/health

# Check firewall
sudo ufw status
```

#### MongoDB connection errors
```bash
# Check MongoDB is running
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh --host localhost --port 27017
```

---

## Estimated Costs

### One-Time Costs
- NAS Storage (if not owned): $0 (already have Netgear RN104)
- SSL Certificate: $0 (Let's Encrypt free or self-signed)
- Development Time: Already complete

### If Going with Capacitor + App Store:
- Apple Developer Account: $99/year
- Development Time: 1-2 weeks
- Ongoing: App Store updates/maintenance

### If Going with PWA:
- Total Cost: $0
- Deployment Time: 4-6 hours
- Users can install immediately

---

## Recommendation

For your use case (local manufacturing facility with iPads):

**Phase 1: Deploy PWA (Immediate - 4-6 hours)**
1. Deploy backend to NAS ✅
2. Deploy frontend build to NAS ✅
3. Configure nginx ✅
4. Add PWA manifest and service worker
5. Users add to home screen on iPads

**Phase 2: Consider Capacitor (If needed - 2 weeks)**
- Only if you need App Store presence
- Only if you need specific native features
- Can be done after PWA is working

---

**Prepared by:** AI Development Agent  
**For:** Misty Manufacturing  
**Status:** Ready for Implementation  
**Next Step:** Choose PWA or Capacitor path and begin deployment to NAS
