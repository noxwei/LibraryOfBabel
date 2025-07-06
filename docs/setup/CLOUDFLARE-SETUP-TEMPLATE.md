# 🌐 Cloudflare Tunnel Setup Template (SANITIZED)

## ⚠️ **SECURITY NOTICE**
This is a sanitized template. Replace `YOUR_DOMAIN.COM` with your actual domains.
**DO NOT COMMIT** files containing real domain names or credentials.

## 🎯 **General Setup Process**

### **Step 1: Install Cloudflared**
```bash
brew install cloudflared
cloudflared version
```

### **Step 2: Cloudflare Account Setup**
1. Create account at https://cloudflare.com
2. Add your domains to Cloudflare
3. Note the nameservers provided

### **Step 3: Update DNS at Domain Registrar**
1. Login to your domain registrar
2. Update nameservers to Cloudflare's
3. Remove existing A records

### **Step 4: Authenticate Cloudflared**
```bash
cloudflared tunnel login
# Follow browser authentication
```

### **Step 5: Create Tunnel**
```bash
cloudflared tunnel create your-tunnel-name
# Note the tunnel ID generated
```

### **Step 6: Configure DNS Routes**
```bash
cloudflared tunnel route dns your-tunnel-name YOUR_DOMAIN.COM
cloudflared tunnel route dns your-tunnel-name YOUR_OTHER_DOMAIN.COM
```

### **Step 7: Create Configuration File**
Create `~/.cloudflared/config.yml`:
```yaml
tunnel: your-tunnel-name
credentials-file: ~/.cloudflared/[TUNNEL-ID].json

ingress:
  - hostname: YOUR_DOMAIN.COM
    service: http://localhost:5571
    
  - hostname: YOUR_OTHER_DOMAIN.COM
    service: http://localhost:5572
    
  - service: http_status:404
```

### **Step 8: Start Services**
```bash
# Terminal 1: Start production servers
cd "/path/to/LibraryOfBabel/babel-backend"
node src/production-server.js

# Terminal 2: Start tunnel
cloudflared tunnel run your-tunnel-name
```

### **Step 9: Set Up Auto-Start**
Follow system-specific instructions for auto-starting:
- macOS: LaunchAgent
- Linux: systemd
- Windows: Service

## 🔐 **Security Reminders**
- Keep tunnel credentials secure
- Use environment variables for configuration
- Monitor access logs
- Regular security updates
- Proper firewall configuration

## 🎯 **Verification**
After setup, test:
```bash
curl -I https://YOUR_DOMAIN.COM/api/health
curl -I https://YOUR_OTHER_DOMAIN.COM/api/health
```

**Remember**: Replace all placeholder values with your actual configuration!