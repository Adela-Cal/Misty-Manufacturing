# 🎉 Misty Manufacturing - Complete Deployment Package
## Version 1.0.0

**Welcome! This package contains everything you need to deploy the Misty Manufacturing Management System.**

---

## 📦 Package Contents

```
DEPLOYMENT_PACKAGE/
├── backend/                    Backend server application
├── frontend-build/             Production-ready web application
├── scripts/                    Automated setup scripts
├── documentation/              Complete documentation and guides
├── electron-source/            Source files for Mac app (build on Mac)
└── README.md                   This file
```

---

## 🚀 Quick Start Guide

### Option 1: Automated NAS Deployment (Recommended - 15 minutes)

**Prerequisites:**
- Netgear RN104 NAS on your network
- SSH access to your NAS
- Mac computer to run the script

**Steps:**

1. **Extract this package** to your Mac (e.g., ~/Downloads/Misty-Manufacturing)

2. **Open Terminal** and navigate to the scripts folder:
   ```bash
   cd ~/Downloads/Misty-Manufacturing/scripts
   ```

3. **Install sshpass** (needed for automated SSH):
   ```bash
   brew install sshpass
   ```

4. **Run the automated setup**:
   ```bash
   ./setup-nas-server.sh
   ```

5. **Follow the prompts:**
   - Enter NAS IP address (e.g., 192.168.1.100)
   - Enter NAS username (usually `admin`)
   - Enter NAS password

6. **Wait 10-15 minutes** for automatic installation

7. **Access your application:**
   ```
   http://YOUR_NAS_IP
   ```

**That's it! Your manufacturing system is now running!**

---

### Option 2: Manual NAS Deployment (Advanced)

See `documentation/IOS_NAS_DEPLOYMENT_GUIDE.md` for step-by-step manual installation instructions.

---

### Option 3: Build Native Mac App (Optional)

If you want a native macOS application (.app file):

1. **On a Mac computer**, install Node.js:
   ```bash
   brew install node
   ```

2. **Copy the entire package** to your Mac

3. **Copy your production frontend** build:
   ```bash
   cd ~/Downloads/Misty-Manufacturing
   cp -r frontend-build ../frontend/build
   ```

4. **Copy Electron files**:
   ```bash
   cp electron-source/electron-public.js ../frontend/public/electron.js
   cp electron-source/preload-public.js ../frontend/public/preload.js
   ```

5. **Build the app**:
   ```bash
   cd ../frontend
   npm install
   npm run electron-build-mac
   ```

6. **Find your app**:
   ```
   dist/mac/Misty Manufacturing.app
   ```

---

## 🔐 First Login

Once deployed, access the application and login:

**Default Admin Account:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT:** Change this password immediately after first login!

**Existing Users:**
- Use your assigned username and password
- Contact your administrator if you forgot your password

---

## 🏢 What This System Does

### Production Management
✅ Order tracking and management
✅ Production board with job stages
✅ Job cards and specifications
✅ Material requirements planning

### Inventory Control
✅ Stock management (raw materials & products)
✅ Stock allocation and movement tracking
✅ Stocktake functionality
✅ Low stock alerts

### Payroll & HR
✅ Timesheet entry and approval
✅ Leave request management
✅ Payroll calculation
✅ Employee profiles

### Business Operations
✅ Client management
✅ Invoicing (with Xero integration)
✅ Profitability reports
✅ Custom label designer

---

## 📊 System Requirements

### NAS Server (Netgear RN104)
- **OS:** Linux-based (default NAS OS)
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 20GB available for application + data
- **Network:** Gigabit Ethernet recommended
- **Software:** Python 3.9+, MongoDB 5.0+, nginx (auto-installed by script)

### Client Computers (Macs)
- **OS:** macOS 10.13 (High Sierra) or later
- **Browser:** Safari 12+ or Chrome 80+ (for web app)
- **RAM:** 4GB minimum
- **Network:** Wired or WiFi connection to NAS

---

## 🌟 Key Features

### Multi-User Concurrent Access
✅ **5-15 concurrent users** supported
✅ **No race conditions** - atomic operations throughout
✅ **No data conflicts** - optimistic locking implemented
✅ **30-day sessions** - automatic token refresh

### Security
✅ JWT authentication
✅ Role-based access control (Admin, Manager, Production Staff)
✅ Password hashing (bcrypt)
✅ Session management
✅ HTTPS ready (SSL configuration guide included)

### Reliability
✅ Automated daily backups
✅ Database migrations
✅ Error logging
✅ Health monitoring
✅ Automatic service restart on failure

---

## 📱 Accessing the Application

### From Mac Computers

**Web Browser (Recommended):**
```
http://YOUR_NAS_IP
```

**Create Desktop Shortcut (App-like experience):**

1. Open Chrome
2. Navigate to `http://YOUR_NAS_IP`
3. Click Menu (⋮) → More Tools → Create Shortcut
4. Check "Open as window"
5. Click "Create"

Now you have an app icon in your Applications/Launchpad that opens like a native application!

**From Safari:**
1. Navigate to `http://YOUR_NAS_IP`
2. File → Add to Dock
3. The site appears as an app in your Dock

---

## 🔧 Configuration

### Server Configuration

**Backend Settings** (`backend/.env`):
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=misty_manufacturing
SECRET_KEY=your-secret-key
PORT=8001
```

**Frontend Settings**:
The frontend is pre-configured to connect to your NAS IP during installation.

---

## 🆘 Troubleshooting

### Application Won't Load

1. **Check NAS is powered on and connected to network**
2. **Ping the NAS**:
   ```bash
   ping YOUR_NAS_IP
   ```
3. **Check services are running**:
   ```bash
   ssh admin@YOUR_NAS_IP
   sudo systemctl status misty-backend
   sudo systemctl status nginx
   sudo systemctl status mongod
   ```

### Cannot Login

1. **Verify username and password** (case-sensitive)
2. **Check Caps Lock is off**
3. **Reset password via SSH** (contact administrator)
4. **Check backend logs**:
   ```bash
   ssh admin@YOUR_NAS_IP
   sudo journalctl -u misty-backend -n 50
   ```

### Slow Performance

1. **Check number of concurrent users** (keep under 15)
2. **Check NAS CPU/RAM**:
   ```bash
   ssh admin@YOUR_NAS_IP
   top
   ```
3. **Check network connection** (use wired if possible)
4. **Restart services**:
   ```bash
   ssh admin@YOUR_NAS_IP
   sudo systemctl restart misty-backend
   ```

### More Help

See `documentation/` folder for complete troubleshooting guides.

---

## 📚 Documentation

The `documentation/` folder contains:

- **IOS_NAS_DEPLOYMENT_GUIDE.md** - Complete NAS setup guide
- **MULTI_USER_CONCURRENT_ACCESS_IMPLEMENTATION.md** - Technical details
- **MACOS_APP_INSTALLATION_GUIDE.md** - Mac app instructions
- **IMPLEMENTATION_COMPLETE_SUMMARY.md** - Feature list and changelog
- **add_version_fields.py** - Database migration script

---

## 🔄 Updates

### Updating the Server

1. **Download new version package**
2. **SSH into your NAS**:
   ```bash
   ssh admin@YOUR_NAS_IP
   ```
3. **Backup current installation**:
   ```bash
   cd /volume1/misty-manufacturing
   tar -czf backup-$(date +%Y%m%d).tar.gz backend frontend
   ```
4. **Upload new files** and restart:
   ```bash
   sudo systemctl restart misty-backend
   sudo systemctl restart nginx
   ```

### Updating the Mac App

1. **Download new .app file**
2. **Quit current app**
3. **Replace in Applications folder**
4. **Launch new version**

---

## 💾 Backups

### Automated Backups

Backups run automatically every night at 2 AM:
- MongoDB database dump
- Uploaded files archive
- 30-day retention

**Backup Location:** `/volume1/misty-manufacturing/backups/`

### Manual Backup

```bash
ssh admin@YOUR_NAS_IP
cd /volume1/misty-manufacturing
./backup-now.sh
```

### Restore from Backup

```bash
ssh admin@YOUR_NAS_IP
cd /volume1/misty-manufacturing/backups
mongorestore --db=misty_manufacturing ./backup-YYYYMMDD/
```

---

## 👥 User Management

### Adding New Users

1. Login as Admin
2. Navigate to **Staff & Security**
3. Click **Add User**
4. Fill in details and assign role
5. Click **Create**

### Roles

- **Admin** - Full system access
- **Manager** - Everything except Staff & Security
- **Production Staff** - Dashboard, Production, Calculators, Payroll (limited)

---

## 🔒 Security Best Practices

### Essential Security Steps

1. **Change default admin password immediately**
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Enable HTTPS** (see SSL setup guide in documentation)
4. **Regular backups** (verify they're working)
5. **Keep software updated** (monitor for updates)
6. **Use VPN for remote access** (don't expose NAS to internet)
7. **Enable firewall** on NAS
8. **Regular security audits** (quarterly)

### Setting Up HTTPS

See `documentation/IOS_NAS_DEPLOYMENT_GUIDE.md` Section 7 for SSL certificate setup.

---

## ⚖️ License

© 2025 Misty Manufacturing. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

## 📞 Support

### Technical Support
- **Documentation:** Check the `documentation/` folder first
- **Logs:** Located at `/volume1/misty-manufacturing/logs/`
- **Health Check:** `http://YOUR_NAS_IP/api/health`

### Common Commands

**Check Status:**
```bash
ssh admin@YOUR_NAS_IP
sudo systemctl status misty-backend nginx mongod
```

**View Logs:**
```bash
sudo journalctl -u misty-backend -f
tail -f /var/log/nginx/access.log
```

**Restart Services:**
```bash
sudo systemctl restart misty-backend
sudo systemctl restart nginx
```

---

## 🎉 Thank You!

Thank you for choosing Misty Manufacturing Management System!

This system was built with:
- ❤️ Attention to detail
- 🔒 Security-first approach
- 🚀 Performance optimization
- 👥 Multi-user support from the ground up

We hope it serves your manufacturing operations well!

---

**Version:** 1.0.0  
**Release Date:** September 2025  
**Package Date:** October 21, 2025

**Built with:** React, FastAPI, MongoDB, Electron  
**Powered by:** Your dedication to excellence in manufacturing! 🖖

---

## 🚦 Quick Reference

| Task | Command/URL |
|------|-------------|
| Access Application | `http://YOUR_NAS_IP` |
| Check Services | `systemctl status misty-backend` |
| View Logs | `journalctl -u misty-backend -f` |
| Restart Backend | `systemctl restart misty-backend` |
| Backup Now | `./backup-now.sh` |
| Health Check | `http://YOUR_NAS_IP/api/health` |

---

**Ready to deploy? Start with Option 1 (Automated NAS Deployment) above!** 🚀
