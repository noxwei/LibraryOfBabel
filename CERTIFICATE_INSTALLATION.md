# 🔐 Certificate Installation Guide
## LibraryOfBabel SSL Certificate Setup for Zero Browser Warnings

### 🎯 **Quick Summary**
Your LibraryOfBabel APIs now use proper SSL certificates! For the best experience with zero browser warnings, install the CA certificate in your browser.

### 📱 **For iOS Safari/Shortcuts App**

#### **Step 1: Download CA Certificate**
Open Safari and visit:
```
https://73.161.54.75:5562/api/secure/ca-cert
```

#### **Step 2: Install Profile**
1. Safari will download the certificate file
2. Go to Settings → General → VPN & Device Management
3. Find "LibraryOfBabel Root CA" under Downloaded Profile
4. Tap Install and enter your passcode
5. Tap Install again to confirm

#### **Step 3: Trust Certificate**
1. Go to Settings → General → About → Certificate Trust Settings
2. Find "LibraryOfBabel Root CA" 
3. Enable full trust for this root certificate
4. Tap Continue to confirm

### 🖥️ **For Desktop Browsers**

#### **Chrome/Edge:**
1. Download certificate: `https://73.161.54.75:5562/api/secure/ca-cert`
2. Chrome Settings → Privacy and Security → Security → Manage Certificates
3. Authorities tab → Import → Select downloaded file
4. Check "Trust this certificate for identifying websites"
5. Restart browser

#### **Firefox:**
1. Download certificate: `https://73.161.54.75:5562/api/secure/ca-cert`
2. Firefox Settings → Privacy & Security → Certificates → View Certificates
3. Authorities tab → Import → Select downloaded file
4. Check "Trust this CA to identify websites"
5. Restart browser

#### **Safari (macOS):**
1. Download certificate: `https://73.161.54.75:5562/api/secure/ca-cert`
2. Double-click downloaded .crt file
3. Keychain Access opens → Add to System keychain
4. Find certificate → Double-click → Trust → "Always Trust"
5. Enter admin password

### 🌐 **External Access URLs (After Certificate Installation)**

Once installed, these URLs will work without SSL warnings:

#### **Secure Book Search API:**
- **API Info**: `https://73.161.54.75:5562/api/secure/info`
- **Books List**: `https://73.161.54.75:5562/api/secure/books/list?api_key=YOUR_KEY`
- **Search Book**: `https://73.161.54.75:5562/api/secure/books/search/260?api_key=YOUR_KEY&q=consciousness`

#### **For iOS Shortcuts:**
```
https://73.161.54.75:5562/api/secure/books/search/260?api_key=M39Gqz5e8D-_qkyuy37ar87_jNU0EPs_nO6_izPnGaU&q=consciousness
```

### 🔑 **API Authentication**
```
API Key: M39Gqz5e8D-_qkyuy37ar87_jNU0EPs_nO6_izPnGaU
```

**Authentication Methods:**
1. **URL Parameter** (easiest for Shortcuts): `?api_key=YOUR_KEY`
2. **Header**: `X-API-Key: YOUR_KEY`
3. **Bearer Token**: `Authorization: Bearer YOUR_KEY`

### ✅ **Certificate Features**
- **4096-bit RSA encryption**
- **SHA-256 signature algorithm**
- **Subject Alternative Names** for localhost, IP addresses, and domains
- **Extended Key Usage** for server authentication
- **1-year validity** (expires July 2026)

### 🔧 **Router Port Forwarding Required**
Make sure your Xfinity router forwards:
- **External Port**: `5562` → **Internal Port**: `5562` → **IP**: `10.0.0.13`

### 🧪 **Test Certificate Installation**
After installation, visit:
```
https://73.161.54.75:5562/api/secure/info
```

You should see:
- ✅ **Green lock** in browser address bar
- ✅ **No security warnings**
- ✅ **Valid certificate** in browser security info

### 🆘 **Troubleshooting**

#### **Still seeing warnings?**
1. Ensure you downloaded from the correct URL
2. Restart your browser after installation
3. Clear browser cache and cookies
4. Check that certificate is trusted in system settings

#### **Connection refused?**
1. Verify router port forwarding is configured
2. Check that API server is running
3. Confirm your external IP hasn't changed

#### **API key errors?**
1. Ensure you're using the correct key
2. Check that key is properly URL-encoded in requests
3. Verify you're using HTTPS (not HTTP)

### 🔄 **Certificate Renewal**
Certificates expire July 2026. To renew:
1. Regenerate certificates using the SSL scripts
2. Restart API servers
3. Re-download and install new CA certificate

---

**🎉 Once installed, your LibraryOfBabel APIs will work seamlessly in browsers and iOS Shortcuts with full SSL security and zero warnings!**