# 🍎 macOS Setup Guide for Manufacturing Management App

## ✅ macOS Compatibility Status

**GOOD NEWS:** Your application is **100% compatible with macOS!**

All components are cross-platform:
- ✅ Python/FastAPI backend - Works perfectly on macOS
- ✅ React frontend - Fully compatible
- ✅ MongoDB database - Native macOS support
- ✅ All dependencies - macOS compatible

## 📋 Prerequisites for macOS

### 1. Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python 3.8+
```bash
brew install python@3.11
```

### 3. Install Node.js and Yarn
```bash
brew install node
npm install -g yarn
```

### 4. Install MongoDB
```bash
# Install MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB as a service
brew services start mongodb-community
```

## 🚀 Installation Steps

### Step 1: Clone Your Repository
```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### Step 2: Create Upload Directories
```bash
# Create uploads directory (macOS compatible path)
mkdir -p uploads/logos
mkdir -p uploads/documents
```

### Step 3: Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

**Backend** (`backend/.env`):
```bash
# MongoDB connection (localhost on macOS)
MONGO_URL=mongodb://localhost:27017/manufacturing_db

# CORS origins
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Upload directory (macOS compatible)
UPLOAD_DIR=./uploads
```

**Frontend** (`frontend/.env`):
```bash
# Backend URL
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Step 5: Setup Frontend

```bash
cd ../frontend

# Install dependencies
yarn install

# Build for production (optional)
yarn build
```

## 🏃 Running the Application

### Option 1: Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn server:app --reload --host 127.0.0.1 --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
```

Access at: `http://localhost:3000`

### Option 2: Production Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 127.0.0.1 --port 8001 --workers 4
```

**Terminal 2 - Frontend (Built):**
```bash
cd frontend
yarn build
npx serve -s build -p 3000
```

## 🔄 Auto-Start on macOS Boot

### Create LaunchAgents for Backend

1. Create backend service file:
```bash
nano ~/Library/LaunchAgents/com.manufacturing.backend.plist
```

2. Add this content (update paths):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.manufacturing.backend</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/your/backend/venv/bin/uvicorn</string>
        <string>server:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8001</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/your/backend</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/manufacturing-backend-error.log</string>
    <key>StandardOutPath</key>
    <string>/tmp/manufacturing-backend.log</string>
</dict>
</plist>
```

3. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.manufacturing.backend.plist
```

### Create LaunchAgent for Frontend

1. Create frontend service file:
```bash
nano ~/Library/LaunchAgents/com.manufacturing.frontend.plist
```

2. Add similar content for frontend

## 🌐 Network Access for Office

### Share with Other Macs on Network

1. **Find your Mac's IP address:**
```bash
ipconfig getifaddr en0  # WiFi
# or
ipconfig getifaddr en1  # Ethernet
```

2. **Update frontend .env:**
```bash
REACT_APP_BACKEND_URL=http://YOUR-MAC-IP:8001
```

3. **Allow firewall access:**
   - System Preferences → Security & Privacy → Firewall
   - Add Python and Node to allowed apps

4. **Team access URL:**
```
http://YOUR-MAC-IP:3000
```

## 🐳 Docker Alternative (Easier for macOS)

### Install Docker Desktop for Mac
```bash
brew install --cask docker
```

### Create docker-compose.yml
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongodb:27017/manufacturing_db
    depends_on:
      - mongodb
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001

volumes:
  mongodb_data:
```

### Run with Docker
```bash
docker-compose up -d
```

## 🔧 macOS-Specific Notes

### File Paths
- ✅ All file paths use forward slashes `/` (compatible with macOS)
- ✅ No hardcoded Linux paths like `/usr/` or `/etc/`
- ✅ Uses `pathlib` for cross-platform compatibility

### Permissions
- Upload directory: `chmod 755 uploads`
- Log files: `chmod 644 *.log`

### Performance
- macOS M1/M2 chips: Native performance, no Rosetta needed
- Intel Macs: Full compatibility

### Database Storage
- MongoDB data location: `/usr/local/var/mongodb`
- Config file: `/usr/local/etc/mongod.conf`

## 🛠️ Troubleshooting

### MongoDB not starting
```bash
# Check if MongoDB is running
brew services list

# Restart MongoDB
brew services restart mongodb-community
```

### Port already in use
```bash
# Find process using port 8001
lsof -i :8001

# Kill process
kill -9 <PID>
```

### Python module not found
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

## 📱 Bonus: iOS/iPad Access

Your team can access the app from iPhones/iPads on the same network:
1. Find your Mac's IP address
2. Open Safari on iPhone/iPad
3. Go to `http://YOUR-MAC-IP:3000`
4. Add to Home Screen for app-like experience

## ✅ Final Checklist

- [ ] Homebrew installed
- [ ] Python 3.8+ installed
- [ ] Node.js & Yarn installed
- [ ] MongoDB installed and running
- [ ] Code cloned from GitHub
- [ ] Virtual environment created
- [ ] Dependencies installed (backend & frontend)
- [ ] Environment variables configured
- [ ] Upload directories created
- [ ] Services running successfully
- [ ] Accessible from browser

## 🎉 You're All Set!

Your Manufacturing Management Application is now running on macOS!

**Quick Start:**
```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn server:app --reload

# Terminal 2  
cd frontend && yarn start
```

**Access:** http://localhost:3000

**Login:**
- Username: Callum
- Password: Peach7510
