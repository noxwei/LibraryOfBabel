# Domain Configuration Guide

## Setting Up Custom Domain for LibraryOfBabel API

This guide covers configuring DNS records and network settings for your LibraryOfBabel API with a custom domain and Let's Encrypt SSL.

## Prerequisites

- ✅ Domain name purchased (hover.com, GoDaddy, Namecheap, etc.)
- ✅ DNS management access
- ✅ Router/network admin access
- ✅ External IP address known

## Step 1: Determine Your External IP

### Find Your Public IP
```bash
curl ifconfig.me
```

Or visit: https://whatismyipaddress.com/

**Example:** `[YOUR-EXTERNAL-IP]`

## Step 2: DNS Configuration

### Required DNS Records

Add these records to your domain's DNS settings:

#### Essential Records
```
Type: A     Host: api               Value: YOUR_EXTERNAL_IP    TTL: 15 min
Type: A     Host: @                 Value: YOUR_DOMAIN_IP      TTL: 15 min  
Type: A     Host: *                 Value: YOUR_DOMAIN_IP      TTL: 15 min
Type: MX    Host: @                 Value: 10 mx.yourdomain.com TTL: 15 min
```

#### LibraryOfBabel Specific
```
Type: A     Host: api               Value: YOUR_EXTERNAL_IP    TTL: 15 min
```

#### For Let's Encrypt Verification (temporary)
```
Type: TXT   Host: _acme-challenge.api  Value: [provided by certbot]  TTL: 15 min
```

### Example DNS Configuration

For domain `yourdomain.com`:

| Type | Host | Value | TTL | Purpose |
|------|------|-------|-----|---------|
| A | api | [YOUR-EXTERNAL-IP] | 15 min | LibraryOfBabel API |
| A | @ | 216.40.34.41 | 15 min | Main domain |
| A | * | 216.40.34.41 | 15 min | Wildcard subdomains |
| MX | @ | 10 mx.yourdomain.com | 15 min | Email |
| TXT | _acme-challenge.api | [certbot value] | 15 min | SSL verification |

## Step 3: Network Configuration

### Router Port Forwarding

Configure your router to forward these ports:

#### Required Port Forwards
```
External Port: 80    → Internal IP: YOUR_LOCAL_IP  Port: 80   (HTTP/Let's Encrypt)
External Port: 5562  → Internal IP: YOUR_LOCAL_IP  Port: 5562 (LibraryOfBabel API)
```

#### Find Your Local IP
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Example:** `10.0.0.13`

### Port Forward Configuration Example

**Router Settings:**
- **Service Name:** LibraryOfBabel HTTP
- **External Port:** 80
- **Internal Port:** 80
- **Internal IP:** 10.0.0.13
- **Protocol:** TCP

**And:**
- **Service Name:** LibraryOfBabel API
- **External Port:** 5562
- **Internal Port:** 5562
- **Internal IP:** 10.0.0.13
- **Protocol:** TCP

## Step 4: DNS Propagation Testing

### Check DNS Resolution
```bash
# Test API subdomain
nslookup api.yourdomain.com

# Test TXT record (for Let's Encrypt)
nslookup -type=TXT _acme-challenge.api.yourdomain.com
```

### Expected Results
```
# For A record
Name: api.yourdomain.com
Address: [YOUR-EXTERNAL-IP]

# For TXT record
_acme-challenge.api.yourdomain.com text = "verification-string-from-certbot"
```

### DNS Propagation Time
- **Typical:** 5-15 minutes
- **Maximum:** Up to 48 hours
- **TTL setting:** Lower TTL = faster propagation

## Step 5: Firewall Configuration

### macOS Firewall
If using macOS firewall, allow these applications:
```bash
# Allow Python (for LibraryOfBabel API)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/bin/python3
```

### Network Firewall
Ensure your network firewall allows:
- **Inbound TCP 80** (for Let's Encrypt verification)
- **Inbound TCP 5562** (for LibraryOfBabel API)

## Step 6: Test Domain Configuration

### Test External Access
```bash
# Test HTTP (should redirect or respond)
curl -I http://api.yourdomain.com

# Test API port (before SSL)
curl -k https://api.yourdomain.com:5562/api/secure/info
```

### Test from External Network
Use your phone's cellular data or ask a friend to test:
```bash
curl https://api.yourdomain.com:5562/api/secure/info
```

## Domain Provider Specific Instructions

### Hover.com
1. Login to Hover control panel
2. Select your domain
3. Go to **DNS** tab
4. Click **ADD A RECORD**
5. Fill in the record details
6. Save changes

### GoDaddy
1. Login to GoDaddy account
2. Go to **My Products** → **Domains**
3. Click **DNS** next to your domain
4. Add records in DNS Management
5. Save changes

### Namecheap
1. Login to Namecheap account
2. Go to **Domain List**
3. Click **Manage** next to your domain
4. Go to **Advanced DNS** tab
5. Add Host Records
6. Save changes

## Troubleshooting

### DNS Not Resolving
- **Check TTL:** Wait for TTL expiration
- **Verify records:** Ensure correct syntax
- **Test different DNS:** Use `8.8.8.8` for testing
- **Online tools:** Use DNS checker websites

### Port Forwarding Issues
- **Router restart:** Restart router after configuration
- **Local firewall:** Check macOS firewall settings
- **ISP blocking:** Some ISPs block residential port 80
- **Double NAT:** Check if behind multiple routers

### Common DNS Errors
```bash
# Wrong host format
❌ Host: api.yourdomain.com    # Don't include full domain
✅ Host: api                   # Just the subdomain

# Missing trailing dot in MX
❌ Value: 10 mx.yourdomain.com  # Missing dot
✅ Value: 10 mx.yourdomain.com. # With trailing dot
```

## Security Considerations

### DNS Security
- **Use strong passwords** for domain account
- **Enable 2FA** on domain registrar account
- **Monitor DNS changes** for unauthorized modifications
- **Use DNS monitoring** services for change alerts

### Network Security
- **Change default router passwords**
- **Keep router firmware updated**
- **Use WPA3 WiFi security**
- **Monitor network traffic** for unusual activity

## Next Steps

After domain configuration:
1. **SSL certificate setup** - Generate Let's Encrypt certificates
2. **API configuration** - Update LibraryOfBabel to use domain
3. **Production deployment** - Set up automated service
4. **Monitoring setup** - Health checks and alerts

## Domain Configuration Checklist

- [ ] Domain purchased and accessible
- [ ] DNS A record added for API subdomain
- [ ] DNS records propagated (verified with nslookup)
- [ ] Router port forwarding configured (80, 5562)
- [ ] External IP accessible on configured ports
- [ ] Firewall configured to allow traffic
- [ ] Domain resolves correctly from external networks
- [ ] Ready for SSL certificate generation

## Reference Information

### Useful DNS Tools
- **DNS Checker:** https://dnschecker.org/
- **DNS Propagation:** https://www.whatsmydns.net/
- **Google DNS Test:** https://toolbox.googleapps.com/apps/dig/

### Port Testing Tools
- **Port Checker:** https://www.yougetsignal.com/tools/open-ports/
- **Network Tools:** https://www.speedtest.net/

### External IP Services
- **WhatIsMyIP:** https://whatismyipaddress.com/
- **IPInfo:** https://ipinfo.io/
<!-- Agent Commentary -->
---

## 🤖 Agent Bulletin Board

*Agents observe and comment on project evolution*

### 👤 Dr. Elena Rodriguez (Project Philosophy & Ethics Advisor)
*2025-07-07 00:17*

> Agent personalities suggest interesting questions about anthropomorphization of AI systems. Why do we make them human-like?

### 👤 Alex Thompson (Security Analyst)
*2025-07-07 00:17*

> Git repository growing. Historical data creates permanent attack surface. Consider information lifecycle management.

### 👤 Dr. Sarah Kim (Technical Architecture Analyst)
*2025-07-07 00:17*

> Technical architecture demonstrates good separation of concerns. Agent modularity will enable future scaling.

### 👤 Jordan Park (Productivity & Efficiency Analyst)
*2025-07-07 00:17*

> Documentation standardization reducing context switching overhead. Good workflow optimization principle.

---
*Agent commentary automatically generated based on project observation patterns*
