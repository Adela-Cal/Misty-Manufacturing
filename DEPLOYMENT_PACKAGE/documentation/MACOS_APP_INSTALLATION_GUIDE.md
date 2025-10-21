# Misty Manufacturing - macOS Desktop App Installation Guide

**Version:** 1.0.0  
**Last Updated:** September 2025

---

## 📦 Package Contents

You should have received:

1. **Misty Manufacturing.app** - The macOS desktop application
2. **setup-nas-server.sh** - Automated NAS setup script  
3. **README.md** - This file
4. **backend/** - Server application files (optional, for manual setup)

---

## 🚀 Quick Start Guide

### Step 1: Set Up Your NAS Server (One-Time Setup)

**Option A: Automated Setup (Recommended)**

1. Open Terminal on your Mac
2. Navigate to the installation directory:
   ```bash
   cd ~/Downloads/Misty-Manufacturing
   ```

3. Run the automated setup script:
   ```bash
   ./setup-nas-server.sh
   ```

4. Follow the prompts:
   - Enter your NAS IP address (e.g., `192.168.1.100`)
   - Enter your NAS username (usually `admin`)
   - Enter your NAS password
   
5. Wait for the script to complete (approximately 10-15 minutes)

**Option B: Manual Setup**

See the detailed manual setup guide in `NAS_MANUAL_SETUP.md`

---

### Step 2: Install the Mac App

1. **Extract the ZIP file** (if you haven't already)
2. **Drag "Misty Manufacturing.app"** to your Applications folder
3. **Double-click** to launch the app

**First Launch - Security Notice:**
Since the app is not signed with an Apple Developer certificate, macOS will show a security warning.

**To open the app:**
1. Control-click (right-click) the app icon
2. Select "Open" from the menu
3. Click "Open" in the dialog that appears

This only needs to be done once. After that, you can open the app normally.

---

### Step 3: Configure Server Connection

When you first launch the app:

1. You'll see a "Server Configuration" dialog
2. Enter your NAS IP address (e.g., `192.168.1.100`)
3. Click "Save"
4. The app will connect to your NAS server

---

### Step 4: Login

Use your existing credentials to login:
- Username: Your employee username
- Password: Your password

**Default admin account (if this is a fresh installation):**
- Username: `admin`
- Password: `admin123` (change this immediately!)

---

## 📱 App Features

### Desktop Experience
- ✅ Native macOS application
- ✅ Full-screen support
- ✅ Dock integration
- ✅ Native notifications (coming soon)
- ✅ Keyboard shortcuts
- ✅ Touch Bar support (if available)

### Multi-User Support
- ✅ Multiple users can work simultaneously
- ✅ Real-time data synchronization
- ✅ No conflicts or data loss
- ✅ Automatic session management

### Offline Capabilities
- ⚠️ Limited offline support
- ✅ Cached data viewable offline
- ❌ Cannot create/edit data offline
- ✅ Automatic sync when reconnected

---

## 🔧 Troubleshooting

### App Won't Open

**Problem:** "Misty Manufacturing.app is damaged and can't be opened"

**Solution:**
```bash
# In Terminal, remove the quarantine flag:
xattr -cr /Applications/Misty\ Manufacturing.app
```

---

### Cannot Connect to Server

**Problem:** App shows "Cannot connect to server"

**Check:**
1. Is your Mac on the same network as the NAS?
2. Can you ping the NAS?
   ```bash
   ping 192.168.1.100
   ```
3. Is the NAS server running?
   ```bash
   ssh admin@192.168.1.100
   sudo systemctl status misty-backend
   ```

---

### App is Slow

**Check:**
1. Network connection quality
2. NAS server resources:
   ```bash
   ssh admin@192.168.1.100
   top
   ```
3. Number of concurrent users

---

### Login Failed

**Problem:** "Invalid username or password"

**Solutions:**
1. Check username (case-sensitive)
2. Check Caps Lock
3. Reset password via admin account
4. Check NAS server backend logs:
   ```bash
   ssh admin@192.168.1.100
   sudo journalctl -u misty-backend -n 50
   ```

---

## 🔄 Updates

### Updating the App

1. Download new version
2. Quit the current app
3. Replace the old app in Applications folder
4. Launch the new version

### Updating the Server

1. SSH into your NAS
2. Navigate to the application directory:
   ```bash
   cd /volume1/misty-manufacturing
   ```
3. Pull latest changes or upload new files
4. Restart the backend:
   ```bash
   sudo systemctl restart misty-backend
   ```

---

## 🛡️ Security Best Practices

### Change Default Passwords
```bash
# SSH into NAS
ssh admin@192.168.1.100

# Change admin password in the app
# Go to: Staff & Security → Users → Edit admin user
```

### Enable HTTPS (Recommended)

See `HTTPS_SETUP.md` for instructions on securing your connection with SSL/TLS.

### Backup Configuration

**Automated Backups** are configured to run daily at 2 AM.

**Manual Backup:**
```bash
ssh admin@192.168.1.100
cd /volume1/misty-manufacturing
./backup-now.sh
```

**Backup Location:** `/volume1/misty-manufacturing/backups/`

---

## 📊 System Requirements

### Mac Requirements
- **macOS:** 10.13 (High Sierra) or later
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 500MB for app
- **Network:** Wired or WiFi connection to NAS

### NAS Requirements
- **Model:** Netgear RN104 (or compatible)
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 10GB minimum for application + data
- **Network:** Gigabit Ethernet recommended

---

## 🆘 Getting Help

### Check Logs

**Mac App Logs:**
```bash
# View app console logs
open ~/Library/Logs/Misty\ Manufacturing/
```

**Server Logs:**
```bash
ssh admin@192.168.1.100
sudo journalctl -u misty-backend -f
```

### Common Commands

**Check Server Status:**
```bash
ssh admin@192.168.1.100
sudo systemctl status misty-backend
sudo systemctl status nginx
sudo systemctl status mongod
```

**Restart Services:**
```bash
ssh admin@192.168.1.100
sudo systemctl restart misty-backend
sudo systemctl restart nginx
```

**View Active Users:**
```bash
ssh admin@192.168.1.100
who
```

---

## 📞 Support Information

### Documentation
- Full documentation: `/volume1/misty-manufacturing/docs/`
- Technical guide: `TECHNICAL_DOCUMENTATION.md`
- API reference: `API_DOCUMENTATION.md`

### Contact
- **Email:** support@misty-manufacturing.com
- **Phone:** (123) 456-7890
- **Hours:** Monday-Friday, 9 AM - 5 PM

---

## 📝 Version History

### Version 1.0.0 (Current)
- ✅ Initial release
- ✅ Multi-user concurrent access support
- ✅ macOS native application
- ✅ Automated NAS setup
- ✅ Token refresh (30-day sessions)
- ✅ Atomic operations (no race conditions)

---

## ⚖️ License

© 2025 Misty Manufacturing. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

## 🎉 Thank You!

Thank you for choosing Misty Manufacturing Management System. We hope this application helps streamline your manufacturing operations!

For questions or feedback, please contact your system administrator.

---

**Document Version:** 1.0  
**Last Updated:** September 2025  
**Prepared by:** Misty Manufacturing IT Department
