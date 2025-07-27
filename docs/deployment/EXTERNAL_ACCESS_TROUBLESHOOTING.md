# 🔥 External API Access Troubleshooting Guide
## "Why is my API not accessible externally?" - The Complete Fix

**Created after resolving the July 27, 2025 external access crisis**

---

## 🚨 **SYMPTOMS: API works locally but not externally**

- ✅ `curl localhost:5562` works
- ❌ `curl https://api.ashortstayinhell.com:5562` fails
- ❌ External IP unreachable

---

## 🔧 **ROOT CAUSE: Mac Mini IP Address Changed**

**THE PROBLEM:** Router port forwarding was configured for **10.0.0.13** but Mac Mini had changed to **10.0.0.68**

### **Step 1: Check Current Mac Mini IP**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Should show: inet 10.0.0.13 (for port forwarding to work)
```

### **Step 2: Fix IP Address (if changed)**
**Option A: Set Static IP to 10.0.0.13**
- System Preferences → Network → Advanced → TCP/IP
- Configure IPv4: Manually
- IP Address: 10.0.0.13
- Subnet Mask: 255.255.255.128 
- Router: 10.0.0.1

**Option B: Update Router Port Forwarding**
- Router Admin → Port Forwarding
- Change Internal IP from 10.0.0.13 → 10.0.0.68

---

## 🔥 **EMERGENCY CHECKLIST**

### **1. Verify Local API Works**
```bash
curl -k https://localhost:5562/api/v4/health
# Expected: {"status":"healthy"}
```

### **2. Check Mac Mini IP**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Must match router port forwarding config
```

### **3. Verify External IP**
```bash
curl ifconfig.me
# Should be: 73.161.54.75
```

### **4. Test Port Forwarding**
```bash
curl http://73.161.54.75:5562
# Should connect (may show error content but connection works)
```

### **5. Check Firewall**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getappblocked "/opt/homebrew/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python"
# Expected: "Incoming connection...is permitted"
```

---

## 🛠 **COMPLETE RESOLUTION STEPS**

### **Phase 1: Infrastructure**
1. **Fix Mac Mini IP** (set to 10.0.0.13)
2. **Verify Router Port Forwarding:**
   - External Port: 5562 → Internal IP: 10.0.0.13 → Internal Port: 5562
3. **Update DNS A Record:**
   - api.ashortstayinhell.com → 73.161.54.75

### **Phase 2: Firewall Configuration**
```bash
# Add Python to firewall allowlist
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add "/opt/homebrew/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python"

# Unblock Python
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock "/opt/homebrew/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python"
```

### **Phase 3: API Configuration**
```bash
# Ensure API binds to all interfaces
# In production_api.py:
app.run(
    host='0.0.0.0',  # NOT '127.0.0.1'
    port=5562,
    ssl_context=(ssl_cert_path, ssl_key_path)
)
```

### **Phase 4: Testing**
```bash
# Test external access
curl -k https://73.161.54.75:5562/api/v4/health

# Test domain access  
curl https://api.ashortstayinhell.com:5562/api/v4/health
```

---

## 🚫 **WHAT NOT TO DO**

❌ **Don't run simple HTTP servers on port 5562** - Risk of exposing file system  
❌ **Don't assume firewall is the only issue** - Check IP first  
❌ **Don't restart services without checking network config**  
❌ **Don't use `localhost` or `127.0.0.1` for external APIs**  

---

## 📊 **CURRENT WORKING CONFIGURATION**

- **External IP:** 73.161.54.75
- **Mac Mini IP:** 10.0.0.13 (static)
- **API Port:** 5562 (HTTPS with SSL)
- **Domain:** api.ashortstayinhell.com
- **SSL Certificate:** `/ssl/letsencrypt-config/live/api.ashortstayinhell.com/`
- **API Key:** [REDACTED - babel_prod_*****]

---

## 🎯 **PREVENTION**

1. **Document network configuration** in this file
2. **Set static IP** for Mac Mini
3. **Monitor IP changes** with alerts
4. **Test external access** after any network changes
5. **Keep this guide updated** with current config

---

## 🏆 **SUCCESS INDICATORS**

✅ `curl https://api.ashortstayinhell.com:5562/api/v4/health` returns JSON  
✅ SSL certificate valid (no security warnings)  
✅ All API endpoints accessible externally  
✅ 5000+ books, 515M+ words available  

**Last Updated:** July 27, 2025  
**Status:** ✅ RESOLVED - External access working