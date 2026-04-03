# Syntra Production Deployment Guide

## Domain Routing Configuration

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Public Internet                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Nginx / Traefik / Caddy                        │
│              SSL Termination + Routing                      │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼────────┐              ┌────────▼────────┐
    │  syntra.goalixa│              │  api.goalixa.   │
    │  .com           │              │  com            │
    │  (Admin Panel)  │              │  (CLI API)      │
    │                 │              │                 │
    │  /admin → UI    │              │  /api/* → API   │
    │  /api/admin →   │              │  /docs → Docs   │
    │  Admin API      │              │                 │
    └────────┬────────┘              └────────┬────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
                  ┌───────▼────────┐
                  │  Syntra App    │
                  │  (FastAPI)     │
                  │  Port 8000     │
                  └────────────────┘
```

## Nginx Configuration

Create `/etc/nginx/sites-available/syntra`:

```nginx
# Syntra Admin Panel
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name syntra.goalixa.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/syntra.goalixa.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/syntra.goalixa.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/syntra-admin.access.log;
    error_log /var/log/nginx/syntra-admin.error.log;

    # Proxy to Syntra App
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Websocket support for real-time features
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Syntra API (CLI access)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.goalixa.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.goalixa.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.goalixa.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Rate Limiting (additional layer)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/syntra-api.access.log;
    error_log /var/log/nginx/syntra-api.error.log;

    # API Endpoints
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers for API
        add_header Access-Control-Allow-Origin "https://syntra.goalixa.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "X-API-Key, Content-Type, Authorization" always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # API Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name syntra.goalixa.com api.goalixa.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/syntra /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificates (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d syntra.goalixa.com -d api.goalixa.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

## CLI Configuration

### Using the Syntra CLI

```bash
# Install CLI
npm install -g @goalixa/syntra-cli

# Configure with API key
syntra configure \
  --api-key sk_abc123... \
  --api-endpoint https://api.goalixa.com

# Test connection
syntra status

# Make a request
syntra ask "Check pod status in production"
```

### Using cURL

```bash
# Set API key
export SYNTRA_API_KEY="sk_abc123..."

# Check rate limits
curl https://api.goalixa.com/api/rate-limit \
  -H "X-API-Key: $SYNTRA_API_KEY"

# Make a request
curl -X POST https://api.goalixa.com/api/ask \
  -H "X-API-Key: $SYNTRA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "List all pods in production namespace",
    "namespace": "production"
  }'
```

### Using Python

```python
import requests

API_KEY = "sk_abc123..."
API_ENDPOINT = "https://api.goalixa.com"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(
    f"{API_ENDPOINT}/api/ask",
    headers=headers,
    json={
        "prompt": "Check pod status",
        "namespace": "production"
    }
)

print(response.json())
```

## Security Checklist

### ✅ Implemented
- [x] API Key authentication for CLI
- [x] Rate limiting (60/min, 1000/hour)
- [x] Security headers (CSP, HSTS, X-Frame-Options)
- [x] HTTPS/SSL enforced
- [x] CORS properly configured
- [x] Admin panel authentication

### 🔄 To Implement (Production)
- [ ] Integrate with Goalixa Auth Service (SSO)
- [ ] Add MFA for admin panel
- [ ] Redis for distributed rate limiting
- [ ] Database persistence (PostgreSQL)
- [ ] Audit logging to external system
- [ ] API key rotation
- [ ] IP whitelisting option
- [ ] mTLS for enterprise clients
- [ ] Web Application Firewall (WAF)
- [ ] DDoS protection

## Environment Variables

```bash
# .env file for production
DOMAIN_ADMIN=syntra.goalixa.com
DOMAIN_API=api.goalixa.com
AUTH_SERVICE_URL=https://auth.goalixa.com
DATABASE_URL=postgresql://user:pass@localhost/syntra
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key
API_KEY_EXPIRY_DAYS=365
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
LOG_LEVEL=INFO
```

## Monitoring

### Health Checks

```bash
# Service health
curl https://api.goalixa.com/api/health

# Full status (requires auth)
curl https://api.goalixa.com/api/admin/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Metrics

Syntra exposes Prometheus-compatible metrics at `/metrics`:
- Request rate
- Error rate
- Response time
- Active users
- API usage per user

## Troubleshooting

### CLI Connection Issues

```bash
# Test API endpoint
curl -v https://api.goalixa.com/api/health

# Test with API key
curl https://api.goalixa.com/api/rate-limit \
  -H "X-API-Key: YOUR_KEY"

# Check rate limit status
curl https://api.goalixa.com/api/rate-limit \
  -H "X-API-Key: YOUR_KEY" | jq
```

### Admin Panel Issues

```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/syntra-admin.access.log
sudo tail -f /var/log/nginx/syntra-admin.error.log

# Check app logs
docker-compose logs -f syntra-ai

# Restart services
sudo systemctl reload nginx
docker-compose restart syntra-ai
```

## DNS Configuration

Add these records to your DNS:

```
# A Records
syntra.goalixa.com.    A    YOUR_SERVER_IP
api.goalixa.com.       A    YOUR_SERVER_IP

# Optional: CNAME for documentation
docs.goalixa.com.      CNAME syntra.goalixa.com.
```

## Production Deployment

```bash
# Clone and setup
git clone https://github.com/goalixa/syntra.git
cd syntra

# Configure environment
cp .env.example .env
nano .env  # Edit with your values

# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f

# Scale if needed
docker-compose up -d --scale syntra-ai=3
```

---

**Next Steps:**
1. Set up DNS records
2. Configure SSL certificates
3. Update Nginx configuration
4. Test CLI connectivity
5. Set up monitoring
6. Implement SSO/MFA integration
