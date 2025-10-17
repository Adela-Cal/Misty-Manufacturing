# 🗄️ Running on Netgear NAS Drive
## Manufacturing Management App on NAS Setup Guide

---

## ✅ Can You Run on NAS? (Quick Answer)

**YES, if your NAS supports Docker containers**

### Compatible Netgear NAS Models:
- ✅ **ReadyNAS 300 series** and above (with Docker support)
- ✅ **ReadyNAS with ARM or x86 processor**
- ✅ Any NAS running **Container Station** or **Docker**
- ❌ Lower-end models without Docker support

**Check your model:** Look for "Docker" or "Container" in the NAS app store.

---

## 🎯 Three Setup Options

### **Option 1: Full Docker Setup on NAS (Best)**
Run the entire application (database + backend + frontend) on NAS using Docker

**Requirements:**
- Netgear NAS with Docker support
- 4GB+ RAM minimum
- Good processor (avoid old ARM chips)

**Pros:**
- ✅ Everything runs on NAS
- ✅ 24/7 availability
- ✅ Low power consumption
- ✅ Automatic backups

**Cons:**
- ⚠️ Performance depends on NAS specs
- ⚠️ Setup is more technical

---

### **Option 2: NAS as Database/File Storage Only (Recommended)**
Run backend on a Mac, store database and files on NAS

**Requirements:**
- Any Netgear NAS with SMB/NFS support
- No Docker needed

**Pros:**
- ✅ Works with any NAS
- ✅ Easier setup
- ✅ Better performance
- ✅ Centralized file storage

**Cons:**
- ⚠️ Need one Mac to run backend
- ⚠️ Mac must stay on during work hours

---

### **Option 3: Hybrid Setup**
Database on NAS (Docker), backend on Mac, files on NAS

**Best of both worlds but most complex**

---

## 🔧 Option 1: Full Docker Setup on NAS

### Step 1: Check NAS Compatibility

**SSH into your NAS and check:**
```bash
# SSH to NAS (username is usually "admin")
ssh admin@nas-ip-address

# Check if Docker is installed
docker --version

# Check system resources
cat /proc/cpuinfo
free -h
```

**Minimum Requirements:**
- Docker installed
- 4GB RAM
- Dual-core processor
- 20GB free space

### Step 2: Create Docker Compose File

**On your NAS, create a directory:**
```bash
# SSH to NAS
ssh admin@192.168.1.50  # Replace with your NAS IP

# Create app directory
mkdir -p /volume1/docker/manufacturing-app
cd /volume1/docker/manufacturing-app
```

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: manufacturing-db
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - /volume1/docker/manufacturing-app/mongodb:/data/db
    environment:
      - MONGO_INITDB_DATABASE=manufacturing_db

  backend:
    image: python:3.11-slim
    container_name: manufacturing-backend
    restart: always
    ports:
      - "8001:8001"
    volumes:
      - /volume1/docker/manufacturing-app/backend:/app
      - /volume1/docker/manufacturing-app/uploads:/app/uploads
    working_dir: /app
    command: >
      bash -c "pip install -r requirements.txt && 
               uvicorn server:app --host 0.0.0.0 --port 8001"
    environment:
      - MONGO_URL=mongodb://mongodb:27017/manufacturing_db
      - UPLOAD_DIR=/app/uploads
    depends_on:
      - mongodb

  frontend:
    image: node:18-alpine
    container_name: manufacturing-frontend
    restart: always
    ports:
      - "3000:3000"
    volumes:
      - /volume1/docker/manufacturing-app/frontend:/app
    working_dir: /app
    command: >
      sh -c "yarn install && yarn start"
    environment:
      - REACT_APP_BACKEND_URL=http://nas-ip:8001
    depends_on:
      - backend

volumes:
  mongodb_data:
```

### Step 3: Upload Your Code to NAS

**Option A: Use NAS Web Interface**
1. Open NAS admin panel in browser
2. Go to File Manager
3. Navigate to `/volume1/docker/manufacturing-app/`
4. Upload `backend/` and `frontend/` folders

**Option B: Use rsync from Mac**
```bash
# From your Mac, after downloading the code
cd ~/Documents/manufacturing-management-app

# Copy backend to NAS
rsync -av backend/ admin@nas-ip:/volume1/docker/manufacturing-app/backend/

# Copy frontend to NAS
rsync -av frontend/ admin@nas-ip:/volume1/docker/manufacturing-app/frontend/

# Copy uploads directory
rsync -av uploads/ admin@nas-ip:/volume1/docker/manufacturing-app/uploads/
```

### Step 4: Start the Application on NAS

```bash
# SSH to NAS
ssh admin@nas-ip

# Go to app directory
cd /volume1/docker/manufacturing-app

# Start all services
docker-compose up -d

# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Access from Any Computer

From any Mac/PC/iPhone on your network:
```
http://nas-ip:3000
```

---

## 🗂️ Option 2: NAS as Storage Only (Easiest)

This is the **recommended approach for most users**.

### Architecture:
```
┌────────────────────┐
│   Mac (Server)     │
│  • Backend         │
│  • Frontend        │
└────────┬───────────┘
         │
         ↓ (stores data)
┌────────────────────┐
│  Netgear NAS       │
│  • MongoDB Data    │
│  • Uploaded Files  │
└────────────────────┘
```

### Setup Steps:

#### Step 1: Mount NAS on Mac

**On your Mac:**
1. Open **Finder**
2. Go → **Connect to Server** (Cmd+K)
3. Enter: `smb://nas-ip/volume1`
4. Login with NAS credentials
5. The NAS will appear in Finder

**Or via Terminal:**
```bash
# Create mount point
mkdir -p ~/nas-storage

# Mount NAS
mount -t smbfs //admin@nas-ip/volume1 ~/nas-storage
```

#### Step 2: Configure MongoDB to Use NAS

**Edit MongoDB config to store data on NAS:**

```bash
# Stop MongoDB
brew services stop mongodb-community

# Edit config file
nano /usr/local/etc/mongod.conf
```

**Change storage path:**
```yaml
storage:
  dbPath: /Users/yourusername/nas-storage/mongodb-data
```

**Create directory on NAS and restart:**
```bash
# Create directory
mkdir -p ~/nas-storage/mongodb-data

# Restart MongoDB
brew services start mongodb-community
```

#### Step 3: Configure App to Use NAS for Uploads

**Edit `backend/.env`:**
```bash
# Point uploads to NAS
UPLOAD_DIR=/Users/yourusername/nas-storage/manufacturing-uploads

# MongoDB (now on NAS)
MONGO_URL=mongodb://localhost:27017/manufacturing_db
```

**Create uploads directory:**
```bash
mkdir -p ~/nas-storage/manufacturing-uploads/logos
mkdir -p ~/nas-storage/manufacturing-uploads/documents
```

#### Step 4: Start Application

```bash
cd ~/Documents/manufacturing-management-app
./start.sh
```

### Benefits of This Approach:

✅ **Works with ANY NAS** (no Docker needed)
✅ **Centralized Storage:** All data on NAS
✅ **Automatic Backups:** Use NAS backup features
✅ **Easy Setup:** Just mount and configure paths
✅ **Better Performance:** Mac runs the app, NAS just stores
✅ **Shared Access:** Multiple Macs can connect to same NAS

---

## 🌐 Network Access Configuration

Regardless of which option you choose:

### NAS Network Settings:

1. **Set Static IP for NAS:**
   - NAS Admin → Network → TCP/IP
   - Set static IP (e.g., 192.168.1.50)
   - Or configure DHCP reservation in router

2. **Enable Required Services:**
   - SMB/CIFS (for file sharing)
   - SSH (for management)
   - Docker (if using Option 1)

3. **Firewall Rules:**
   - Allow port 3000 (frontend)
   - Allow port 8001 (backend)
   - Allow port 27017 (MongoDB)

### Access URLs:

**If running on NAS (Option 1):**
```
Application: http://nas-ip:3000
Backend API: http://nas-ip:8001
```

**If using Mac + NAS (Option 2):**
```
Application: http://mac-ip:3000
Backend API: http://mac-ip:8001
Storage: On NAS (transparent to users)
```

---

## 📊 Performance Comparison

| Setup | Performance | Ease | 24/7 | Cost |
|-------|-------------|------|------|------|
| **Full NAS (Docker)** | ⭐⭐⭐ | ⭐⭐ | ✅ | $ |
| **Mac + NAS Storage** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ | $ |
| **Mac Only** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | Free |
| **Cloud Hosting** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | $$$ |

---

## 🔍 Which NAS Models Work Best?

### ✅ Recommended (Docker Support):
- **ReadyNAS 420/520/620** series
- **ReadyNAS 300 series** (312/314/316)
- **ReadyNAS with Intel x86 CPU**

### ⚠️ Limited Support:
- **ReadyNAS 100 series** (may be slow)
- **Older ARM-based models**

### ❌ Not Recommended:
- **ReadyNAS Duo/Ultra** (too old)
- **Models with <2GB RAM**
- **Consumer-grade NAS without Docker**

### How to Check Your Model:

**Web Interface:**
1. Login to NAS admin panel
2. Look for **System → Info**
3. Check for "App Center" or "Container Station"

**SSH Method:**
```bash
ssh admin@nas-ip
cat /etc/version
cat /proc/cpuinfo | grep model
free -h
```

---

## 🛠️ Troubleshooting NAS Setup

### Issue: "Docker not available on NAS"
**Solution:** Use Option 2 (NAS as storage only)

### Issue: "NAS is too slow"
**Solutions:**
- Use SSD cache if NAS supports it
- Upgrade NAS RAM
- Use Option 2 (Mac runs app, NAS just stores)
- Consider dedicated Mac Mini server instead

### Issue: "Can't connect to MongoDB on NAS"
**Check:**
```bash
# Is MongoDB container running?
docker ps | grep mongo

# Check MongoDB logs
docker logs manufacturing-db

# Test connection from Mac
mongo --host nas-ip --port 27017
```

### Issue: "Permission denied on NAS"
**Fix permissions:**
```bash
# SSH to NAS
ssh admin@nas-ip

# Fix permissions
chmod -R 755 /volume1/docker/manufacturing-app
chown -R admin:admin /volume1/docker/manufacturing-app
```

---

## 💡 Recommendations by Scenario

### Scenario 1: "I have a modern Netgear NAS with Docker"
**→ Use Option 1 (Full Docker on NAS)**
- Best for 24/7 operation
- NAS runs everything
- Mac computers just use browsers

### Scenario 2: "I have a basic NAS for file storage"
**→ Use Option 2 (Mac + NAS Storage)**
- Easiest setup
- Better performance
- Works with any NAS

### Scenario 3: "My NAS is old/slow"
**→ Use Mac server, upgrade NAS later**
- Run entirely on Mac for now
- Move to NAS when you upgrade
- Or just use NAS for backups

### Scenario 4: "I want the most reliable setup"
**→ Dedicated Mac Mini + NAS Storage**
- Mac Mini as 24/7 server ($500-800)
- NAS for file storage and backups
- Best performance and reliability

---

## 📋 Quick Decision Guide

**Answer these questions:**

1. **Does your NAS support Docker?**
   - YES → Option 1 (Full NAS setup)
   - NO → Option 2 (Mac + NAS storage)

2. **Do you have a Mac that can stay on 24/7?**
   - YES → Option 2 is perfect
   - NO → Option 1 or consider Mac Mini

3. **How many users?**
   - 1-5 users → Any option works
   - 6-15 users → Option 2 or dedicated Mac Mini
   - 15+ users → Dedicated server or cloud hosting

4. **Budget?**
   - $0 → Use existing Mac + NAS
   - $500-800 → Add Mac Mini as server
   - $50/month → Cloud hosting (Emergent)

---

## ✅ Setup Checklist

**For Option 1 (Full NAS):**
- [ ] Verify NAS has Docker support
- [ ] Check NAS has 4GB+ RAM
- [ ] Install Docker on NAS
- [ ] Upload code to NAS
- [ ] Create docker-compose.yml
- [ ] Start containers
- [ ] Test from multiple computers
- [ ] Configure automatic backups

**For Option 2 (Mac + NAS):**
- [ ] Mount NAS on Mac
- [ ] Configure MongoDB to use NAS
- [ ] Set upload directory to NAS
- [ ] Create NAS directories
- [ ] Start application
- [ ] Test file uploads go to NAS
- [ ] Verify multiple Macs can access
- [ ] Configure NAS backup schedule

---

## 📞 Need Help?

**Questions to help me assist you better:**

1. What's your Netgear NAS model? (e.g., ReadyNAS 312)
2. How much RAM does it have?
3. Can you access "App Center" in the NAS admin panel?
4. Do you see "Docker" or "Container Station" available?

**Let me know your NAS model and I can provide specific instructions!**

---

## 🎉 Summary

**YES, you can run on Netgear NAS!**

- **Best Option:** Mac runs app + NAS stores data (Option 2)
- **Also Works:** Full Docker on NAS if supported (Option 1)
- **Easiest:** Start with Mac, add NAS storage later

**Next Step:** Tell me your NAS model and I'll give you specific setup instructions!
