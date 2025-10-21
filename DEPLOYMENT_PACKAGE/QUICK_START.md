# 🚀 5-Minute Quick Start Guide
## Misty Manufacturing on Your NAS

This is the fastest way to get Misty Manufacturing running on your Netgear RN104 NAS.

---

## ⚡ Prerequisites (2 minutes)

Before you start, make sure you have:

✅ Netgear RN104 NAS powered on and connected to your network  
✅ NAS IP address (e.g., 192.168.1.100)  
✅ NAS admin username and password  
✅ Mac computer on the same network  
✅ Terminal access on your Mac

---

## 🎯 Installation (15 minutes)

### Step 1: Install sshpass on Your Mac

Open Terminal and run:
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install sshpass
brew install sshpass
```

### Step 2: Extract the Package

1. Unzip `Misty-Manufacturing.zip` to your Downloads folder
2. You should see a folder called `DEPLOYMENT_PACKAGE`

### Step 3: Run the Automated Setup Script

```bash
# Navigate to the scripts folder
cd ~/Downloads/DEPLOYMENT_PACKAGE/scripts

# Run the setup script
./setup-nas-server.sh
```

### Step 4: Answer the Prompts

The script will ask you:

```
Enter NAS IP address: 192.168.1.100  (your actual NAS IP)
Enter NAS SSH username: admin
Enter NAS password: ********
```

### Step 5: Wait for Installation

The script will:
- ✅ Connect to your NAS
- ✅ Install Python, MongoDB, nginx
- ✅ Upload all application files
- ✅ Configure services
- ✅ Start everything

**Time:** About 10-15 minutes

### Step 6: Access Your Application!

Once complete, open any web browser:

```
http://YOUR_NAS_IP
```

**Login:**
- Username: `admin`
- Password: `admin123`

⚠️ **Change this password immediately!**

---

## ✅ Success Checklist

After installation, verify everything is working:

- [ ] Can access the login page at `http://YOUR_NAS_IP`
- [ ] Can login with admin/admin123
- [ ] Dashboard loads without errors
- [ ] Navigation menu is visible
- [ ] Can create a test order
- [ ] Logo says "Misty Manufacturing"

---

## 🆘 If Something Goes Wrong

### Can't Access the Application

**Problem:** Browser shows "Can't reach this page"

**Solutions:**
1. Check NAS is powered on:
   ```bash
   ping YOUR_NAS_IP
   ```
2. Check services are running:
   ```bash
   ssh admin@YOUR_NAS_IP
   sudo systemctl status misty-backend
   sudo systemctl status nginx
   ```
3. Restart services:
   ```bash
   sudo systemctl restart misty-backend nginx
   ```

### Login Doesn't Work

**Problem:** "Invalid username or password"

**Solutions:**
1. Check username is exactly: `admin` (lowercase)
2. Check password is exactly: `admin123`
3. Check Caps Lock is OFF
4. Check backend logs:
   ```bash
   ssh admin@YOUR_NAS_IP
   sudo journalctl -u misty-backend -n 50
   ```

### Installation Script Failed

**Problem:** Script exits with an error

**Solutions:**
1. Check you have SSH access to NAS:
   ```bash
   ssh admin@YOUR_NAS_IP
   ```
2. Check sshpass is installed:
   ```bash
   brew list sshpass
   ```
3. Check the installation log:
   ```bash
   cat ~/Downloads/DEPLOYMENT_PACKAGE/scripts/nas-setup.log
   ```
4. Try manual installation (see full guide in documentation/)

---

## 📱 Creating Desktop Shortcuts

To make the app feel like a native Mac application:

### Chrome Method:
1. Open Chrome
2. Go to `http://YOUR_NAS_IP`
3. Click Menu (⋮) → More Tools → Create Shortcut
4. Check "Open as window"
5. Click "Create"

Result: App icon in Launchpad that opens full-screen!

### Safari Method:
1. Open Safari
2. Go to `http://YOUR_NAS_IP`
3. File → Add to Dock

Result: Icon in Dock that opens in Safari!

---

## 🔄 Next Steps

### 1. Change Admin Password
- Login → Staff & Security → Users → Edit admin
- Change password to something secure

### 2. Create User Accounts
- Staff & Security → Users → Add User
- Create accounts for each employee

### 3. Configure Company Settings
- Upload company logo
- Set default tax rates
- Configure email settings (if using)

### 4. Import Existing Data (if applicable)
- Clients
- Products
- Employees

### 5. Train Staff
- Show them how to login
- Walk through their daily tasks
- Share the URL: `http://YOUR_NAS_IP`

---

## 📚 Need More Help?

See the complete documentation:
- **Full Installation Guide:** `documentation/IOS_NAS_DEPLOYMENT_GUIDE.md`
- **Feature Documentation:** `documentation/IMPLEMENTATION_COMPLETE_SUMMARY.md`
- **Troubleshooting:** `documentation/MACOS_APP_INSTALLATION_GUIDE.md`

---

## 🎉 You're Done!

Your Misty Manufacturing system is now running!

**Access URL:** `http://YOUR_NAS_IP`  
**Initial Login:** admin / admin123  
**Users Supported:** 5-15 concurrent users  
**Backup:** Automatic daily at 2 AM

---

**Enjoy your new manufacturing management system! 🖖**

*Need help? Check the logs: `/var/log/misty-manufacturing/`*
