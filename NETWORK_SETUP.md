# 🌐 Multi-Computer Network Setup Guide
## Running Your Manufacturing App Across Multiple Macs

This guide will help you set up your manufacturing management application so that **multiple computers in your office can use it simultaneously** and share the same data in real-time.

---

## 📋 Architecture Overview

**What You'll Set Up:**

```
┌─────────────────────────────────────────────────┐
│  SERVER MAC (Main Computer)                     │
│  - Backend (FastAPI) on port 8001               │
│  - MongoDB Database                              │
│  - Frontend Files (optional)                     │
│  IP: 192.168.1.100 (example)                    │
└─────────────────────────────────────────────────┘
                    ↕ Network
┌──────────────────┬──────────────────┬────────────┐
│  Client Mac #1   │  Client Mac #2   │ Client #3  │
│  - Browser Only  │  - Browser Only  │ - Browser  │
│  - No Database   │  - No Database   │ - No DB    │
└──────────────────┴──────────────────┴────────────┘
```

**Key Concept:** 
- ONE computer acts as the **SERVER** (runs backend + database)
- ALL other computers act as **CLIENTS** (just use web browser)
- ALL computers share the same data through the server

---

## 🖥️ Step 1: Choose Your Server Mac

**Recommended:** Pick the most powerful Mac or one that will stay on during work hours.

**Requirements for Server Mac:**
- Good RAM (8GB+ recommended)
- Stays powered on during work hours
- Connected to office network (WiFi or Ethernet)
- macOS 10.15+ (Catalina or newer)

---

## 🔧 Step 2: Setup Server Mac

### A. Download the Application

```bash
# Clone from GitHub
cd ~/Documents
git clone https://github.com/YOUR-USERNAME/manufacturing-management-app.git
cd manufacturing-management-app
```

### B. Install Prerequisites

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required software
brew install python@3.11 node mongodb-community

# Start MongoDB (database will run 24/7)
brew services start mongodb-community
```

### C. Configure for Network Access

Create/edit `backend/.env`:

```bash
# MongoDB (localhost since database is on this Mac)
MONGO_URL=mongodb://localhost:27017/manufacturing_db
DB_NAME=manufacturing_db

# CORS - Allow all computers on your network
CORS_ORIGINS=http://localhost:3000,http://192.168.1.*:3000,http://10.0.*:3000

# Upload directory
UPLOAD_DIR=./uploads

# Xero (if using)
XERO_CLIENT_ID=your_client_id_here
XERO_CLIENT_SECRET=your_secret_here
XERO_REDIRECT_URI=http://YOUR-SERVER-IP:8001/xero-oauth-callback
```

Create/edit `frontend/.env`:

```bash
# THIS WILL BE DIFFERENT FOR SERVER vs CLIENTS
# For server (if running frontend locally):
REACT_APP_BACKEND_URL=http://localhost:8001

# For clients, you'll use the server's IP address
```

### D. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create uploads directory
mkdir -p ../uploads/logos
mkdir -p ../uploads/documents
```

### E. Setup Frontend

```bash
cd ../frontend

# Install dependencies
yarn install
```

### F. Find Your Server Mac's IP Address

```bash
# For WiFi
ipconfig getifaddr en0

# For Ethernet
ipconfig getifaddr en1

# Example output: 192.168.1.100
# WRITE THIS DOWN - you'll need it for all client computers!
```

Let's say your IP is: **192.168.1.100** (use your actual IP)

### G. Configure Firewall to Allow Connections

1. Open **System Preferences** → **Security & Privacy** → **Firewall**
2. Click **Firewall Options**
3. Add these applications:
   - Python (for backend)
   - Node (for frontend development server)
4. OR disable firewall temporarily for testing

### H. Start the Server

**Option 1: Using the startup script**

First, update `start.sh` to bind to all network interfaces:

Edit line in start.sh that starts backend:
```bash
# Change from 127.0.0.1 to 0.0.0.0 to accept network connections
uvicorn server:app --host 0.0.0.0 --port 8001 > "$SCRIPT_DIR/backend.log" 2>&1 &
```

Then run:
```bash
chmod +x start.sh
./start.sh
```

**Option 2: Manual start (more control)**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Terminal 2 - Frontend (optional, can just use clients):
```bash
cd frontend
REACT_APP_BACKEND_URL=http://192.168.1.100:8001 yarn start
```

**Verify Server is Running:**
```bash
# Check if backend is accessible
curl http://localhost:8001/api/health

# Check from your IP
curl http://192.168.1.100:8001/api/health
```

---

## 💻 Step 3: Setup Client Macs

**On EACH other Mac in your office:**

### Option A: Browser Only (Simplest - Recommended)

No installation needed! Just open a web browser and go to:

```
http://192.168.1.100:3000
```

(Replace 192.168.1.100 with your server's actual IP)

**That's it!** The client Mac just needs:
- A web browser (Safari, Chrome, Firefox)
- Network connection to the server
- No database, no installation, nothing else!

### Option B: Run Frontend Locally on Each Client (Optional)

If you want better performance or offline frontend:

```bash
# 1. Clone the repository
cd ~/Documents
git clone https://github.com/YOUR-USERNAME/manufacturing-management-app.git
cd manufacturing-management-app/frontend

# 2. Install Node.js
brew install node

# 3. Install dependencies
yarn install

# 4. Create .env file pointing to SERVER
echo "REACT_APP_BACKEND_URL=http://192.168.1.100:8001" > .env

# 5. Start frontend
yarn start
```

Client will open at `http://localhost:3000` but connects to central server's database.

---

## ✅ Step 4: Test Multi-Computer Setup

### Test 1: Basic Connectivity

**On Server Mac:**
```bash
# Check backend is running and accessible
curl http://192.168.1.100:8001/api/health
```

**On Client Mac:**
```bash
# Try to reach server
ping 192.168.1.100

# Try to reach backend
curl http://192.168.1.100:8001/api/health
```

### Test 2: Real-Time Data Sharing

1. **On Server Mac:** Login and create a new client
2. **On Client Mac:** Refresh browser - you should see the new client
3. **On Client Mac:** Create an order
4. **On Server Mac:** The order should appear immediately

### Test 3: Simultaneous Editing

1. Open the app on 3 different computers
2. Have each person create a different order
3. All orders should appear on all computers

---

## 🔄 Ensuring Real-Time Updates

Your application should automatically update when data changes. However, to ensure optimal performance:

### Option 1: Browser Auto-Refresh (Built-in)

Most modern browsers auto-refresh data. If you notice delays:

1. Add a refresh button to key pages
2. Or implement polling (check for updates every few seconds)

### Option 2: Add WebSocket Support (Advanced)

For instant real-time updates, you can add WebSockets later. For now, the app will update within a few seconds.

---

## 🌐 Network Configuration Checklist

### Server Mac Settings:

- [ ] Backend running on `0.0.0.0:8001` (not 127.0.0.1)
- [ ] MongoDB running and accessible
- [ ] Firewall allows Python and Node
- [ ] IP address is static (or set DHCP reservation in router)
- [ ] Computer set to not sleep (System Preferences → Energy Saver)

### Client Mac Settings:

- [ ] Can ping server IP
- [ ] Can access `http://SERVER-IP:8001/api/health`
- [ ] Browser configured to use server IP
- [ ] No local database running

### Router/Network Settings:

- [ ] All computers on same subnet (e.g., 192.168.1.x)
- [ ] No firewall blocking ports 8001 or 3000
- [ ] Consider setting static IP for server in router

---

## 📱 Bonus: Access from iPhones/iPads

Your team can also use the app from mobile devices!

1. Make sure mobile device is on same WiFi
2. Open Safari (or any browser)
3. Go to: `http://192.168.1.100:3000`
4. Tap "Share" → "Add to Home Screen" for app-like experience

---

## 🔒 Security Considerations

### For Office Network:

1. **Use Router Firewall:** Only allow connections from office network
2. **WiFi Password:** Strong WiFi password prevents unauthorized access
3. **Backup Database:** Regular backups of MongoDB data
   ```bash
   mongodump --out ~/backups/manufacturing-$(date +%Y%m%d)
   ```

### For Internet Access (Optional - Advanced):

If you want to access from outside office:
1. Set up VPN to office network, OR
2. Deploy to cloud (Emergent hosting), OR
3. Use dynamic DNS + port forwarding (requires network expertise)

---

## 🛠️ Troubleshooting

### "Cannot connect to server"

**On Client Mac:**
```bash
# 1. Can you ping the server?
ping 192.168.1.100

# 2. Is the backend port open?
nc -zv 192.168.1.100 8001

# 3. Check from server itself
curl http://192.168.1.100:8001/api/health
```

**On Server Mac:**
```bash
# 1. Is backend running?
ps aux | grep uvicorn

# 2. Is it listening on all interfaces?
lsof -i :8001

# Should show: *:8001 (not just 127.0.0.1:8001)
```

### "Connection refused"

- Check server firewall settings
- Make sure backend started with `--host 0.0.0.0`
- Verify server Mac isn't in sleep mode

### "Data not updating"

- Check browser console for errors (F12)
- Verify CORS settings include client IPs
- Try hard refresh (Cmd+Shift+R)

### "Slow performance"

- Too many users? Consider upgrading server Mac
- Network congestion? Check WiFi signal strength
- Database size? MongoDB may need optimization

---

## 🚀 Production Deployment Options

### Option 1: Keep Using Mac Server
- Works great for 5-10 users
- No monthly cost
- You control everything

### Option 2: Upgrade to Dedicated Server
- Mac Mini as dedicated server
- Linux server (more powerful)
- Always-on setup

### Option 3: Cloud Deployment
- Emergent hosting ($50/month)
- AWS, Google Cloud, Azure
- Access from anywhere, not just office

---

## 📊 Recommended Setup by Office Size

### Small Office (1-5 people)
- **Server:** Any modern Mac (even MacBook Air)
- **Clients:** Browsers only
- **Network:** Standard WiFi router
- **Cost:** $0 (use existing equipment)

### Medium Office (5-15 people)
- **Server:** Mac Mini or iMac
- **Clients:** Browsers only
- **Network:** Business-grade WiFi
- **Cost:** ~$800 (Mac Mini as server)

### Large Office (15+ people)
- **Server:** Mac Studio or cloud hosting
- **Clients:** Mix of browsers and local frontends
- **Network:** Enterprise WiFi with VLANs
- **Cost:** $2000+ or cloud hosting

---

## 📞 Quick Reference Card

**Print this and put next to each computer:**

```
═══════════════════════════════════════════════
  MANUFACTURING MANAGEMENT APP ACCESS
═══════════════════════════════════════════════

Server Computer: Mac in [LOCATION]
Server IP Address: 192.168.1.100

TO ACCESS:
Open browser and go to:
http://192.168.1.100:3000

LOGIN:
Username: Callum
Password: Peach7510

SUPPORT:
Server not responding? Check:
1. Is server Mac powered on?
2. Run on server: ./start.sh
3. Call IT: [YOUR NUMBER]

═══════════════════════════════════════════════
```

---

## ✅ Setup Complete Checklist

- [ ] Server Mac chosen and set up
- [ ] MongoDB running on server
- [ ] Backend running on 0.0.0.0:8001
- [ ] Server IP address documented
- [ ] Firewall configured
- [ ] Tested from at least 2 client computers
- [ ] All team members can access the app
- [ ] Data syncs across all computers
- [ ] Quick reference cards printed
- [ ] Backup system in place

---

## 🎉 You're All Set!

Your manufacturing management application is now running as a **true multi-user system** where all computers share the same data in real-time!

**Need help?** Let me know if you encounter any issues during setup!
