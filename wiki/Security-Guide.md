# Security Guide

The Library of Babel implements comprehensive security measures to protect both the educational procedural generation system and the research-oriented ebook analysis platform.

## 🛡️ Security Overview

The system employs **defense in depth** with multiple security layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Security Architecture                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🌐 Network Security Layer                                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ • Cloudflare Tunnel (Zero Trust)  • DDoS Protection            │ │
│  │ • TLS 1.3 Encryption             • Geographic Filtering        │ │
│  │ • WAF (Web Application Firewall) • Rate Limiting               │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  🔐 Application Security Layer                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ • API Key Authentication         • Input Validation             │ │
│  │ • JWT Token Management           • SQL Injection Prevention     │ │
│  │ • CORS Policy Enforcement        • XSS Protection               │ │
│  │ • Rate Limiting per Endpoint     • Session Management           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  🎭 Domain Security (Seeker Mode)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ • Domain-Based Access Control    • Feature Gating               │ │
│  │ • Educational vs Research Modes  • User Type Classification     │ │
│  │ • Dynamic Security Policies      • Content Filtering            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  🗄️ Data Security Layer                                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ • Encrypted Database Connections • User Permission Isolation    │ │
│  │ • Secure File Storage            • Data Classification          │ │
│  │ • Regular Security Audits        • Backup Encryption            │ │
│  │ • PII Protection                 • GDPR Compliance              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎭 Seeker Mode (Domain-Based Security)

**Seeker Mode** is our innovative security feature that dynamically adjusts system behavior based on the accessing domain, user type, and context.

### Domain Classification System

```javascript
const SeekerMode = {
  // Classify users based on domain and context
  classifySeeker(req) {
    const domain = req.get('host');
    const userAgent = req.get('user-agent');
    const apiKey = req.headers.authorization;
    
    // Domain-based classification
    if (domain.includes('edu.')) return 'student';
    if (domain.includes('research.')) return 'researcher';
    if (domain.includes('internal.')) return 'developer';
    if (apiKey && this.validateResearchKey(apiKey)) return 'researcher';
    
    return 'public';
  },
  
  // Apply appropriate security policy
  applySecurityPolicy(seekerType, endpoint, req) {
    const policies = {
      student: {
        features: ['search', 'read', 'explore'],
        rateLimit: 100,
        dataAccess: 'educational_only',
        aiAgents: false
      },
      researcher: {
        features: ['all'],
        rateLimit: 500,
        dataAccess: 'full',
        aiAgents: true
      },
      developer: {
        features: ['all', 'admin', 'debug'],
        rateLimit: 1000,
        dataAccess: 'full',
        aiAgents: true
      },
      public: {
        features: ['search', 'read'],
        rateLimit: 50,
        dataAccess: 'public_only',
        aiAgents: false
      }
    };
    
    return policies[seekerType];
  }
};
```

### Security Policy Examples

#### Educational Seekers (Students)
```json
{
  "allowedEndpoints": [
    "/api/search",
    "/api/book/*",
    "/api/random-book",
    "/api/concepts",
    "/api/explore/*"
  ],
  "deniedEndpoints": [
    "/api/research/*",
    "/api/agents/*",
    "/api/admin/*"
  ],
  "rateLimits": {
    "perMinute": 100,
    "perHour": 1000,
    "perDay": 5000
  },
  "contentFiltering": {
    "mode": "educational",
    "hideRealBookData": true,
    "showOnlyProcedural": true
  }
}
```

#### Research Seekers (Authenticated)
```json
{
  "allowedEndpoints": ["*"],
  "rateLimits": {
    "perMinute": 500,
    "perHour": 10000,
    "perDay": 50000
  },
  "contentFiltering": {
    "mode": "full_access",
    "realBookAccess": true,
    "aiAgentAccess": true,
    "analyticsAccess": true
  },
  "additionalSecurity": {
    "requireApiKey": true,
    "sessionTimeout": 7200,
    "ipRestrictions": true
  }
}
```

---

## 🔐 Authentication & Authorization

### API Key Management

#### Key Generation
```bash
# Generate new API key for research access
curl -X POST http://localhost:5560/api/auth/generate-key \
  -H "Content-Type: application/json" \
  -d '{
    "userType": "researcher",
    "organization": "University Research Lab",
    "email": "researcher@university.edu",
    "permissions": ["read", "analyze", "agents"]
  }'
```

#### Key Usage
```bash
# Use API key for authenticated requests
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:5560/api/research/search
```

### JWT Token Implementation
```javascript
const jwt = require('jsonwebtoken');

class AuthenticationManager {
  generateToken(user, permissions) {
    const payload = {
      userId: user.id,
      userType: user.type,
      permissions: permissions,
      seekerMode: this.determineSeekerMode(user),
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + (60 * 60 * 24) // 24 hours
    };
    
    return jwt.sign(payload, process.env.JWT_SECRET, { algorithm: 'HS256' });
  }
  
  validateToken(token) {
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      
      // Check if token is expired
      if (decoded.exp < Date.now() / 1000) {
        throw new Error('Token expired');
      }
      
      return {
        valid: true,
        user: decoded,
        seekerMode: decoded.seekerMode
      };
    } catch (error) {
      return { valid: false, error: error.message };
    }
  }
}
```

---

## 🛡️ Input Validation & Sanitization

### SQL Injection Prevention
```python
class SecurityValidator:
    """Comprehensive input validation and sanitization"""
    
    def __init__(self):
        self.sql_injection_patterns = [
            r"(\b(ALTER|CREATE|DELETE|DROP|EXEC(UTE)?|INSERT|SELECT|UNION|UPDATE)\b)",
            r"(\b(OR|AND)\s+\w+\s*=\s*\w+)",
            r"(--|#|/\*|\*/)",
            r"(\')(.*?)(\-\-|\')|(\")(.*?)(\-\-|\")",
            r"(\b(EXEC|EXECUTE)\s+(SP_|XP_|USP_))",
        ]
        
    def validate_search_query(self, query: str) -> dict:
        """Validate search query for security issues"""
        
        # Check length
        if len(query) > 1000:
            return {'valid': False, 'reason': 'Query too long'}
        
        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return {'valid': False, 'reason': 'Potential SQL injection detected'}
        
        # Check for XSS patterns
        xss_patterns = [r'<script.*?>', r'javascript:', r'onload=', r'onerror=']
        for pattern in xss_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return {'valid': False, 'reason': 'Potential XSS detected'}
        
        return {'valid': True, 'sanitized_query': self.sanitize_query(query)}
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize query while preserving search functionality"""
        
        # Remove potentially dangerous characters
        query = re.sub(r'[<>"\']', '', query)
        
        # Escape special characters for SQL
        query = query.replace('%', '\\%').replace('_', '\\_')
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return query.strip()
```

### Coordinate Validation
```javascript
function validateCoordinates(hexagon, wall, shelf, volume) {
  const validation = {
    valid: true,
    errors: []
  };
  
  // Validate ranges
  if (!Number.isInteger(hexagon) || hexagon < 0 || hexagon > 999999999) {
    validation.valid = false;
    validation.errors.push('Hexagon must be between 0 and 999999999');
  }
  
  if (!Number.isInteger(wall) || wall < 0 || wall > 5) {
    validation.valid = false;
    validation.errors.push('Wall must be between 0 and 5');
  }
  
  if (!Number.isInteger(shelf) || shelf < 0 || shelf > 4) {
    validation.valid = false;
    validation.errors.push('Shelf must be between 0 and 4');
  }
  
  if (!Number.isInteger(volume) || volume < 0 || volume > 31) {
    validation.valid = false;
    validation.errors.push('Volume must be between 0 and 31');
  }
  
  return validation;
}
```

---

## 🚦 Rate Limiting & DDoS Protection

### Multi-Tier Rate Limiting
```javascript
const rateLimitConfig = {
  // Global rate limits
  global: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000, // requests per window
    message: 'Too many requests from this IP'
  },
  
  // Endpoint-specific limits
  endpoints: {
    '/api/search': {
      windowMs: 1 * 60 * 1000, // 1 minute
      max: 30,
      skipSuccessfulRequests: false
    },
    '/api/book/*': {
      windowMs: 1 * 60 * 1000,
      max: 60,
      skipSuccessfulRequests: true
    },
    '/api/research/*': {
      windowMs: 1 * 60 * 1000,
      max: 10,
      keyGenerator: (req) => req.headers.authorization || req.ip
    }
  },
  
  // User type specific limits
  userTypes: {
    student: { max: 100, windowMs: 15 * 60 * 1000 },
    researcher: { max: 500, windowMs: 15 * 60 * 1000 },
    developer: { max: 1000, windowMs: 15 * 60 * 1000 },
    public: { max: 50, windowMs: 15 * 60 * 1000 }
  }
};

// Implement adaptive rate limiting
class AdaptiveRateLimiter {
  constructor(config) {
    this.config = config;
    this.suspiciousIPs = new Set();
  }
  
  getRateLimit(req) {
    const seekerType = req.seekerMode || 'public';
    const endpoint = this.matchEndpoint(req.path);
    const isAuthenticated = !!req.headers.authorization;
    
    // Apply stricter limits for suspicious IPs
    if (this.suspiciousIPs.has(req.ip)) {
      return { max: 10, windowMs: 15 * 60 * 1000 };
    }
    
    // Combine endpoint and user type limits
    const userLimit = this.config.userTypes[seekerType];
    const endpointLimit = this.config.endpoints[endpoint];
    
    return {
      max: Math.min(userLimit?.max || 100, endpointLimit?.max || 100),
      windowMs: endpointLimit?.windowMs || userLimit?.windowMs || 15 * 60 * 1000
    };
  }
}
```

### DDoS Detection & Mitigation
```python
class DDoSProtection:
    """Advanced DDoS detection and mitigation"""
    
    def __init__(self):
        self.request_patterns = {}
        self.blocked_ips = set()
        
    def analyze_request_pattern(self, ip: str, endpoint: str) -> dict:
        """Analyze request patterns for DDoS indicators"""
        
        current_time = time.time()
        
        if ip not in self.request_patterns:
            self.request_patterns[ip] = []
        
        # Add current request
        self.request_patterns[ip].append({
            'timestamp': current_time,
            'endpoint': endpoint
        })
        
        # Remove old requests (last 5 minutes)
        self.request_patterns[ip] = [
            req for req in self.request_patterns[ip]
            if current_time - req['timestamp'] < 300
        ]
        
        # Analyze patterns
        recent_requests = len(self.request_patterns[ip])
        
        # Check for rapid-fire requests
        if recent_requests > 100:
            return {'block': True, 'reason': 'Excessive request rate'}
        
        # Check for pattern repetition
        endpoints = [req['endpoint'] for req in self.request_patterns[ip]]
        if len(set(endpoints)) == 1 and recent_requests > 50:
            return {'block': True, 'reason': 'Repetitive endpoint targeting'}
        
        return {'block': False}
```

---

## 🔒 Data Protection & Privacy

### Database Security
```sql
-- Create security-focused database users
CREATE USER babel_reader WITH PASSWORD 'secure_read_password';
CREATE USER babel_writer WITH PASSWORD 'secure_write_password';
CREATE USER babel_admin WITH PASSWORD 'secure_admin_password';

-- Grant minimal required permissions
GRANT SELECT ON books, chunks, book_outlines TO babel_reader;
GRANT SELECT, INSERT, UPDATE ON books, chunks, book_outlines TO babel_writer;
GRANT ALL PRIVILEGES ON DATABASE librarybabel TO babel_admin;

-- Enable row level security
ALTER TABLE books ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

-- Create security policies
CREATE POLICY book_access_policy ON books
  FOR ALL TO babel_reader
  USING (NOT contains_sensitive_data);

CREATE POLICY chunk_access_policy ON chunks
  FOR ALL TO babel_reader
  USING (NOT contains_pii);
```

### File System Security
```python
class SecureFileManager:
    """Secure file handling for ebook storage"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()
        self.allowed_extensions = {'.epub', '.pdf', '.mobi', '.txt'}
        
    def validate_file_path(self, file_path: str) -> dict:
        """Validate file path for security issues"""
        
        path = Path(file_path).resolve()
        
        # Check if path is within allowed base directory
        if not str(path).startswith(str(self.base_path)):
            return {'valid': False, 'reason': 'Path traversal attempt detected'}
        
        # Check file extension
        if path.suffix.lower() not in self.allowed_extensions:
            return {'valid': False, 'reason': 'File type not allowed'}
        
        # Check file size (max 100MB)
        if path.exists() and path.stat().st_size > 100 * 1024 * 1024:
            return {'valid': False, 'reason': 'File too large'}
        
        return {'valid': True, 'sanitized_path': str(path)}
    
    def secure_file_write(self, content: bytes, filename: str) -> str:
        """Securely write file with proper permissions"""
        
        validation = self.validate_file_path(filename)
        if not validation['valid']:
            raise SecurityError(validation['reason'])
        
        file_path = Path(validation['sanitized_path'])
        
        # Create directory if needed (with secure permissions)
        file_path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        
        # Write file with secure permissions
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Set secure file permissions
        os.chmod(file_path, 0o640)
        
        return str(file_path)
```

### PII Protection
```python
class PIIProtector:
    """Protect personally identifiable information"""
    
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        
    def scan_for_pii(self, text: str) -> dict:
        """Scan text for potential PII"""
        
        findings = {
            'emails': self.email_pattern.findall(text),
            'phones': self.phone_pattern.findall(text),
            'ssns': self.ssn_pattern.findall(text)
        }
        
        total_pii = sum(len(v) for v in findings.values())
        
        return {
            'has_pii': total_pii > 0,
            'findings': findings,
            'risk_level': 'high' if total_pii > 5 else 'medium' if total_pii > 0 else 'low'
        }
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text while preserving readability"""
        
        # Replace emails
        text = self.email_pattern.sub('[EMAIL REDACTED]', text)
        
        # Replace phone numbers
        text = self.phone_pattern.sub('[PHONE REDACTED]', text)
        
        # Replace SSNs
        text = self.ssn_pattern.sub('[SSN REDACTED]', text)
        
        return text
```

---

## 🔍 Security Monitoring & Auditing

### Real-Time Security Monitoring
```python
class SecurityMonitor:
    """Real-time security event monitoring"""
    
    def __init__(self):
        self.security_events = []
        self.alert_thresholds = {
            'failed_logins': 5,
            'sql_injection_attempts': 1,
            'rate_limit_violations': 10,
            'suspicious_file_access': 3
        }
        
    def log_security_event(self, event_type: str, details: dict):
        """Log security event and check for alert conditions"""
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details,
            'ip': details.get('ip'),
            'user': details.get('user'),
            'severity': self.classify_severity(event_type)
        }
        
        self.security_events.append(event)
        
        # Check for alert conditions
        self.check_alert_conditions(event)
    
    def check_alert_conditions(self, event):
        """Check if event triggers security alerts"""
        
        recent_events = [
            e for e in self.security_events 
            if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=1)
        ]
        
        # Count events by type and IP
        event_counts = {}
        for e in recent_events:
            key = f"{e['type']}_{e.get('ip')}"
            event_counts[key] = event_counts.get(key, 0) + 1
        
        # Check thresholds
        for key, count in event_counts.items():
            event_type = key.split('_')[0]
            if event_type in self.alert_thresholds:
                if count >= self.alert_thresholds[event_type]:
                    self.trigger_security_alert(event_type, key, count)
    
    def trigger_security_alert(self, event_type: str, key: str, count: int):
        """Trigger security alert for suspicious activity"""
        
        alert = {
            'alert_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'count': count,
            'severity': 'high' if count > self.alert_thresholds[event_type] * 2 else 'medium',
            'recommended_action': self.get_recommended_action(event_type)
        }
        
        # Send alert to administrators
        self.send_security_alert(alert)
        
        # Take automatic defensive action
        self.take_defensive_action(event_type, key)
```

### Security Audit Logging
```python
class SecurityAuditor:
    """Comprehensive security audit logging"""
    
    def __init__(self, log_file: str = 'security_audit.log'):
        self.logger = self.setup_audit_logger(log_file)
        
    def setup_audit_logger(self, log_file: str):
        """Setup secure audit logging"""
        
        logger = logging.getLogger('security_audit')
        logger.setLevel(logging.INFO)
        
        # Create handler with log rotation
        handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        
        # Secure log format
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def audit_authentication(self, user_id: str, success: bool, ip: str):
        """Audit authentication attempts"""
        
        self.logger.info(f"AUTH_ATTEMPT: user={user_id}, success={success}, ip={ip}")
    
    def audit_api_access(self, endpoint: str, user_id: str, success: bool):
        """Audit API access attempts"""
        
        self.logger.info(f"API_ACCESS: endpoint={endpoint}, user={user_id}, success={success}")
    
    def audit_data_access(self, resource: str, user_id: str, action: str):
        """Audit data access operations"""
        
        self.logger.info(f"DATA_ACCESS: resource={resource}, user={user_id}, action={action}")
```

---

## 🛠️ Security Configuration

### Production Security Checklist

#### Environment Variables
```bash
# Required security environment variables
export JWT_SECRET="your-super-secure-jwt-secret-key"
export DATABASE_ENCRYPTION_KEY="your-database-encryption-key"
export API_SECRET_KEY="your-api-secret-key"
export ALLOWED_ORIGINS="https://yourdomain.com,https://research.yourdomain.com"

# Security settings
export SECURITY_LEVEL="high"
export RATE_LIMITING_ENABLED="true"
export SQL_INJECTION_PROTECTION="true"
export XSS_PROTECTION="true"
export CSRF_PROTECTION="true"

# Monitoring
export SECURITY_MONITORING="true"
export AUDIT_LOGGING="true"
export ALERT_EMAIL="security@yourdomain.com"
```

#### Security Headers Configuration
```javascript
// security-headers.js
const securityHeaders = {
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Content-Security-Policy': `
    default-src 'self';
    script-src 'self' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    connect-src 'self';
    font-src 'self';
    object-src 'none';
    media-src 'self';
    frame-src 'none';
  `.replace(/\s+/g, ' ').trim()
};

module.exports = securityHeaders;
```

### Development Security Setup
```bash
# Install security scanning tools
npm install --save-dev eslint-plugin-security
npm install --save-dev audit-ci
pip install bandit safety

# Run security scans
npm audit
npm run lint:security
bandit -r src/
safety check
```

---

## 🚨 Incident Response

### Security Incident Response Plan

#### Immediate Response (0-15 minutes)
1. **Assess the threat** - Determine severity and scope
2. **Isolate affected systems** - Temporarily block suspicious IPs
3. **Alert security team** - Notify administrators immediately
4. **Document incident** - Record all details and timestamps

#### Short-term Response (15 minutes - 2 hours)
1. **Investigate the incident** - Analyze logs and security events
2. **Implement containment** - Prevent further damage
3. **Assess data exposure** - Determine if data was compromised
4. **Notify stakeholders** - Inform relevant parties as needed

#### Recovery Phase (2-24 hours)
1. **Eliminate the threat** - Remove malicious content/access
2. **Restore normal operations** - Gradually restore services
3. **Strengthen security** - Implement additional protections
4. **Monitor for recurrence** - Enhanced monitoring for 72 hours

#### Post-Incident Review (1-7 days)
1. **Conduct thorough analysis** - Full incident timeline
2. **Update security measures** - Improve based on lessons learned
3. **Update documentation** - Revise procedures as needed
4. **Training updates** - Educate team on new threats

---

The Library of Babel's security framework ensures that both the educational exploration of infinite knowledge and the research analysis of real book collections remain protected while maintaining accessibility for legitimate users.