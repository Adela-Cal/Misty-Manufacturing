# Misty Manufacturing - Complete Deployment Guide
## Multi-User NAS Deployment with Desktop Applications

**Date:** October 2025  
**Version:** 1.0  
**Author:** Emergent AI Development Team

---

## 📋 Overview

This guide provides complete instructions for deploying Misty Manufacturing to your office NAS with desktop applications for multiple users.

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OFFICE NETWORK                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Computer 1  │  │  Computer 2  │  │  Computer 3  │    │
│  │              │  │              │  │              │    │
│  │  [Electron]  │  │  [Electron]  │  │  [Electron]  │    │
│  │  Desktop App │  │  Desktop App │  │  Desktop App │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            │                               │
│                   ┌────────▼────────┐                      │
│                   │   NAS  DRIVE    │                      │
│                   │                 │                      │
│                   │  MongoDB        │                      │
│                   │  FastAPI        │                      │
│                   │  (Port 8001)    │                      │
│                   └─────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Deployment Steps

### Phase 1: NAS Server Setup (2-3 hours)

#### Prerequisites
- ✅ Netgear RN104 NAS (or compatible NAS with Docker support)
- ✅ Static IP address configured on NAS (e.g., 192.168.1.100)
- ✅ SSH access enabled on NAS
- ✅ Docker/Container Station installed on NAS
- ✅ Admin credentials for NAS

#### Step 1.1: Prepare NAS Environment

1. **SSH into your NAS:**
```bash
ssh admin@192.168.1.100
```

2. **Install Docker (if not already installed):**
```bash
# For Netgear NAS with Container Station
# Access via web interface: http://192.168.1.100:8080
# Install "Container Station" from App Center
```

3. **Create application directory:**
```bash
mkdir -p /share/misty-manufacturing
cd /share/misty-manufacturing
```

#### Step 1.2: Deploy MongoDB

1. **Create MongoDB Docker container:**
```bash
docker run -d \
  --name misty-mongodb \
  --restart always \
  -p 27017:27017 \
  -v /share/misty-manufacturing/mongodb-data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=misty_admin \
  -e MONGO_INITDB_ROOT_PASSWORD=your_secure_password_here \
  mongo:7.0
```

2. **Verify MongoDB is running:**
```bash
docker ps | grep misty-mongodb
```

#### Step 1.3: Deploy FastAPI Backend

1. **Copy backend files to NAS:**
```bash
# On your computer, from the project directory:
scp -r backend/ admin@192.168.1.100:/share/misty-manufacturing/
```

2. **Create Dockerfile for backend** (save as `/share/misty-manufacturing/backend/Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

3. **Build and run backend container:**
```bash
cd /share/misty-manufacturing/backend

docker build -t misty-backend .

docker run -d \
  --name misty-backend \
  --restart always \
  -p 8001:8001 \
  -e MONGO_URL="mongodb://misty_admin:your_secure_password_here@192.168.1.100:27017/misty_manufacturing?authSource=admin" \
  misty-backend
```

4. **Test backend is running:**
```bash
curl http://192.168.1.100:8001/health
# Should return: {"status":"healthy"}
```

---

### Phase 2: Desktop Application Build (1-2 hours)

#### Prerequisites
- ✅ Node.js 18+ installed on your computer
- ✅ Yarn package manager
- ✅ Access to frontend code

#### Step 2.1: Configure Frontend for NAS

1. **Update frontend/.env file:**
```env
REACT_APP_BACKEND_URL=http://192.168.1.100:8001
```

2. **Build production frontend:**
```bash
cd frontend
yarn install
yarn build
```

#### Step 2.2: Package Electron App

1. **Install electron-builder:**
```bash
yarn add --dev electron-builder
```

2. **Update package.json with build configuration:**
```json
{
  "name": "misty-manufacturing",
  "version": "1.0.0",
  "description": "Misty Manufacturing Management System",
  "main": "public/electron.js",
  "homepage": "./",
  "build": {
    "appId": "com.misty.manufacturing",
    "productName": "Misty Manufacturing",
    "directories": {
      "buildResources": "build",
      "output": "dist"
    },
    "files": [
      "build/**/*",
      "public/electron.js",
      "public/preload.js",
      "node_modules/**/*"
    ],
    "win": {
      "target": ["nsis"],
      "icon": "public/icon.ico"
    },
    "mac": {
      "target": ["dmg"],
      "icon": "public/icon.icns",
      "category": "public.app-category.business"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    }
  },
  "scripts": {
    "electron:build": "electron-builder"
  }
}
```

3. **Build Windows installer:**
```bash
yarn electron:build --win
```

4. **Build Mac installer (requires macOS):**
```bash
yarn electron:build --mac
```

**Output:**
- Windows: `frontend/dist/Misty Manufacturing Setup 1.0.0.exe`
- Mac: `frontend/dist/Misty Manufacturing-1.0.0.dmg`

---

### Phase 3: Installation on Client Computers (15 mins per computer)

#### For Windows Computers:

1. **Copy installer:**
   - Copy `Misty Manufacturing Setup 1.0.0.exe` to target computer
   - Or place on shared network drive

2. **Run installer:**
   - Double-click the installer
   - Choose installation location (default: `C:\Program Files\Misty Manufacturing`)
   - Select "Create desktop shortcut"
   - Click "Install"

3. **Launch application:**
   - Double-click desktop shortcut
   - Application connects to NAS at `http://192.168.1.100:8001`
   - Login with your credentials

#### For Mac Computers:

1. **Copy installer:**
   - Copy `Misty Manufacturing-1.0.0.dmg` to target computer

2. **Install:**
   - Double-click the DMG file
   - Drag "Misty Manufacturing" to Applications folder
   - Eject the DMG

3. **Launch application:**
   - Open from Applications folder
   - If security warning appears, go to System Preferences → Security & Privacy → Allow
   - Login with your credentials

---

### Phase 4: Multi-User Configuration

#### Database Connection Pooling

MongoDB automatically handles multiple connections. Default settings:
- Max connections: 100
- Connection timeout: 30 seconds
- Automatic reconnection: Enabled

#### User Management

1. **Create user accounts via Admin panel:**
   - Login as admin (Callum/Peach7510)
   - Go to Settings → Staff Security
   - Add users with appropriate roles:
     - `admin` - Full access
     - `manager` - Production + Payroll access
     - `production_manager` - Production access only
     - `staff` - Limited access

2. **Concurrent Access:**
   - Multiple users can login simultaneously
   - Real-time updates via MongoDB change streams
   - Optimistic locking prevents conflicts

---

## 🔧 Configuration Files

### Backend Environment Variables

Create `/share/misty-manufacturing/backend/.env`:
```env
# MongoDB Connection
MONGO_URL=mongodb://misty_admin:your_secure_password_here@192.168.1.100:27017/misty_manufacturing?authSource=admin

# JWT Secret (generate a secure random string)
JWT_SECRET=your_super_secret_jwt_key_change_this

# Application Settings
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://192.168.1.100:3000,http://localhost:3000
```

### Frontend Environment Variables

Frontend `.env` (built into Electron app):
```env
REACT_APP_BACKEND_URL=http://192.168.1.100:8001
```

---

## 🚀 Startup & Shutdown

### Starting the System

1. **Start NAS containers:**
```bash
ssh admin@192.168.1.100
docker start misty-mongodb
docker start misty-backend
```

2. **Verify services:**
```bash
docker ps
# Both containers should show "Up"
```

3. **Launch desktop apps on client computers:**
   - Simply open the installed application
   - Auto-connects to NAS

### Stopping the System

```bash
ssh admin@192.168.1.100
docker stop misty-backend
docker stop misty-mongodb
```

### Auto-Start on NAS Boot

```bash
# Containers are already configured with --restart always
# They will start automatically when NAS reboots
```

---

## 🔍 Troubleshooting

### Issue: Can't connect to backend

**Solution:**
1. Check NAS IP address: `ping 192.168.1.100`
2. Check if backend is running: `docker ps | grep misty-backend`
3. Check backend logs: `docker logs misty-backend`
4. Verify firewall allows port 8001

### Issue: Database connection error

**Solution:**
1. Check MongoDB is running: `docker ps | grep misty-mongodb`
2. Check MongoDB logs: `docker logs misty-mongodb`
3. Verify credentials in backend .env file
4. Test connection: `docker exec -it misty-mongodb mongosh`

### Issue: Multiple users experiencing conflicts

**Solution:**
1. Check backend logs for errors: `docker logs misty-backend`
2. Verify each user has unique username
3. Ensure backend has enough resources (RAM/CPU)
4. Check MongoDB connection pool isn't exhausted

### Issue: Desktop app won't launch

**Windows:**
- Check Windows Defender / Antivirus (may block unsigned app)
- Right-click → Properties → Unblock

**Mac:**
- System Preferences → Security & Privacy → Allow
- If still blocked: `xattr -cr /Applications/Misty\ Manufacturing.app`

---

## 📊 Performance Optimization

### For NAS Server:

1. **Allocate sufficient resources:**
   - Minimum: 4GB RAM, 2 CPU cores
   - Recommended: 8GB RAM, 4 CPU cores

2. **Database indexing:**
```javascript
// MongoDB indexes are already configured in the application
// No manual setup needed
```

3. **Enable RAID** for data redundancy on NAS

### For Client Computers:

- Minimum: 4GB RAM, Intel i3 or equivalent
- Recommended: 8GB+ RAM, Intel i5 or equivalent
- Wired Ethernet connection preferred over WiFi

---

## 🔒 Security Considerations

1. **Change default passwords:**
   - MongoDB admin password
   - Application admin password (Callum/Peach7510)
   - NAS admin password

2. **Enable HTTPS (Optional but recommended):**
   - Install SSL certificate on NAS
   - Configure reverse proxy (nginx) on NAS
   - Update REACT_APP_BACKEND_URL to use https://

3. **Firewall rules:**
   - Only allow port 8001 from local network
   - Block external access to NAS

4. **Backup strategy:**
   - Schedule daily MongoDB backups
   - Use NAS snapshot feature
   - Off-site backup weekly

---

## 📦 Backup & Restore

### Backup MongoDB Data

```bash
# Create backup directory
mkdir -p /share/misty-manufacturing/backups

# Run backup
docker exec misty-mongodb mongodump \
  --username=misty_admin \
  --password=your_secure_password_here \
  --authenticationDatabase=admin \
  --out=/data/backup-$(date +%Y%m%d)

# Copy backup out of container
docker cp misty-mongodb:/data/backup-$(date +%Y%m%d) /share/misty-manufacturing/backups/
```

### Restore MongoDB Data

```bash
docker exec misty-mongodb mongorestore \
  --username=misty_admin \
  --password=your_secure_password_here \
  --authenticationDatabase=admin \
  /data/backup-YYYYMMDD
```

### Automated Backups

Create cron job on NAS:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /share/misty-manufacturing/backup-script.sh
```

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks:

**Daily:**
- ✅ Check application logs for errors
- ✅ Verify all users can login

**Weekly:**
- ✅ Review database backup
- ✅ Check NAS disk space
- ✅ Update user accounts if needed

**Monthly:**
- ✅ Update Docker containers (if security patches available)
- ✅ Review and archive old orders
- ✅ Check application performance

### Getting Help:

1. **Check logs first:**
```bash
# Backend logs
docker logs misty-backend --tail 100

# MongoDB logs
docker logs misty-mongodb --tail 100
```

2. **Application logs:**
   - Desktop app logs located in:
     - Windows: `%APPDATA%\Misty Manufacturing\logs`
     - Mac: `~/Library/Logs/Misty Manufacturing`

3. **Contact support:**
   - Save logs to file
   - Document the issue with screenshots
   - Note which users are affected

---

## ✅ Deployment Checklist

### Pre-Deployment:
- [ ] NAS has static IP configured
- [ ] SSH access to NAS enabled
- [ ] Docker/Container Station installed on NAS
- [ ] Node.js 18+ installed on build computer
- [ ] Backend and frontend code ready

### NAS Setup:
- [ ] MongoDB container running
- [ ] FastAPI backend container running
- [ ] Can access http://NAS_IP:8001/health
- [ ] Database credentials configured
- [ ] Auto-restart enabled on containers

### Desktop Apps:
- [ ] Frontend build completed
- [ ] Electron app packaged
- [ ] Installers created (Windows/Mac)
- [ ] Backend URL correctly configured

### Client Installation:
- [ ] Installers copied to client computers
- [ ] Applications installed
- [ ] Desktop shortcuts created
- [ ] Applications can connect to NAS
- [ ] Users can login successfully

### Testing:
- [ ] Single user can login and use all features
- [ ] Multiple users can login simultaneously
- [ ] Data synchronizes between users
- [ ] Orders can be created and viewed by all users
- [ ] Payroll data updates in real-time
- [ ] PDF generation works
- [ ] Backup process tested
- [ ] Restore process tested

---

## 🎓 Training Materials

### For Users:

1. **Login Process:**
   - Launch "Misty Manufacturing" app
   - Enter username and password
   - Click "Login"

2. **Common Tasks:**
   - Creating orders
   - Managing clients
   - Timesheet entry
   - Viewing reports

3. **Multi-User Etiquette:**
   - Don't delete records others are using
   - Save work frequently
   - Communicate when making major changes

### For Administrators:

1. **User Management:**
   - Settings → Staff Security
   - Add/edit/deactivate users
   - Assign appropriate roles

2. **Monitoring:**
   - Check logs regularly
   - Monitor disk space
   - Review backup success

3. **Updates:**
   - Keep Docker containers updated
   - Plan maintenance windows
   - Test updates on single machine first

---

## 🚀 Next Steps

After successful deployment:

1. **Train your team** on using the application
2. **Set up regular backups** (automated)
3. **Create user documentation** specific to your workflows
4. **Monitor performance** for first week
5. **Gather feedback** from users
6. **Plan for future enhancements**

---

## 📝 Change Log

**Version 1.0 (October 2025)**
- Initial deployment guide
- Multi-user NAS architecture
- Desktop app packaging
- Backup/restore procedures

---

**Need Help?** Refer to the troubleshooting section or check application logs for detailed error messages.

**Deployment Time Estimate:**
- NAS Setup: 2-3 hours
- Desktop App Build: 1-2 hours  
- Client Installation: 15 mins × number of computers
- Testing: 1-2 hours
- **Total: 4-8 hours** (depending on experience level)

Good luck with your deployment! 🎉
