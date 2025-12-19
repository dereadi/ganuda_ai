# Jr Build Instructions: HTTPS for ganuda.us

## Priority: HIGH - Production Security

---

## Objective

Enable HTTPS for the public-facing ganuda.us site. This protects users and establishes trust.

**Key Principle**: No production site should run on plain HTTP.

---

## Architecture Overview

```
Internet
    │
    ▼
┌─────────────────────────────────────────┐
│           Cloudflare (Optional)         │
│     - Free SSL termination              │
│     - DDoS protection                   │
│     - CDN caching                       │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Nginx Reverse Proxy             │
│     - SSL termination (Let's Encrypt)   │
│     - Rate limiting                     │
│     - Static file serving               │
│     - Port 443 → Port 4080 (public)     │
│     - Port 443 → Port 4000 (SAG, auth)  │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
┌──────────┐           ┌──────────┐
│ Public   │           │   SAG    │
│ Site     │           │ (Auth)   │
│ :4080    │           │ :4000    │
└──────────┘           └──────────┘
```

---

## Option 1: Let's Encrypt with Certbot (Recommended for Self-Host)

### Prerequisites

- Domain `ganuda.us` pointing to your server IP
- Ports 80 and 443 open
- Nginx installed

### Step 1: Install Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# RHEL/CentOS
sudo dnf install certbot python3-certbot-nginx
```

### Step 2: Nginx Configuration

Create `/etc/nginx/sites-available/ganuda.us`:

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ganuda.us www.ganuda.us;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Public Site
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ganuda.us www.ganuda.us;

    # SSL certificates (Let's Encrypt will fill these in)
    ssl_certificate /etc/letsencrypt/live/ganuda.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ganuda.us/privkey.pem;

    # SSL settings (modern configuration)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS (strict transport security)
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req zone=general burst=20 nodelay;

    # Static files (if serving directly)
    root /var/www/ganuda.us/public;
    index index.html;

    # Public API proxy
    location /api/public/ {
        proxy_pass http://127.0.0.1:4080/api/public/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS for public API
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
    }

    # Try static files first, then 404
    location / {
        try_files $uri $uri/ =404;
    }
}

# HTTPS - SAG Control Room (Authenticated)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name sag.ganuda.us;

    # Same SSL certs (or separate if you prefer)
    ssl_certificate /etc/letsencrypt/live/ganuda.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ganuda.us/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Stricter rate limiting for authenticated area
    limit_req zone=sag burst=10 nodelay;

    # Proxy all requests to SAG
    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Step 3: Rate Limiting Configuration

Add to `/etc/nginx/nginx.conf` (in http block):

```nginx
http {
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=sag:10m rate=5r/s;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

    # Connection limiting
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    limit_conn addr 10;

    # ... rest of config
}
```

### Step 4: Enable Site and Get Certificate

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/ganuda.us /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Get certificate (this will modify nginx config automatically)
sudo certbot --nginx -d ganuda.us -d www.ganuda.us -d sag.ganuda.us

# Certbot will ask:
# - Email for renewal notices
# - Agree to terms
# - Share email with EFF (optional)
```

### Step 5: Auto-Renewal

Certbot sets up automatic renewal. Verify:

```bash
# Test renewal
sudo certbot renew --dry-run

# Check timer
sudo systemctl status certbot.timer
```

---

## Option 2: Cloudflare (Easiest)

If you don't want to manage certificates yourself:

### Step 1: Add Domain to Cloudflare

1. Sign up at cloudflare.com
2. Add site: ganuda.us
3. Update nameservers at your registrar

### Step 2: SSL/TLS Settings

In Cloudflare dashboard:
- SSL/TLS → Overview → Full (strict)
- SSL/TLS → Edge Certificates → Always Use HTTPS: ON
- SSL/TLS → Edge Certificates → Minimum TLS: 1.2
- SSL/TLS → Edge Certificates → HSTS: Enable

### Step 3: Origin Server

On your server, you can use Cloudflare Origin Certificates (valid for 15 years, only trusted by Cloudflare):

```bash
# Download origin cert from Cloudflare dashboard
# Save as:
/etc/ssl/cloudflare/ganuda.us.pem
/etc/ssl/cloudflare/ganuda.us.key
```

Nginx config for Cloudflare:

```nginx
server {
    listen 443 ssl http2;
    server_name ganuda.us;

    ssl_certificate /etc/ssl/cloudflare/ganuda.us.pem;
    ssl_certificate_key /etc/ssl/cloudflare/ganuda.us.key;

    # Only allow Cloudflare IPs (optional, extra security)
    # See: https://www.cloudflare.com/ips/
    allow 173.245.48.0/20;
    allow 103.21.244.0/22;
    allow 103.22.200.0/22;
    allow 103.31.4.0/22;
    allow 141.101.64.0/18;
    allow 108.162.192.0/18;
    allow 190.93.240.0/20;
    allow 188.114.96.0/20;
    allow 197.234.240.0/22;
    allow 198.41.128.0/17;
    allow 162.158.0.0/15;
    allow 104.16.0.0/13;
    allow 104.24.0.0/14;
    allow 172.64.0.0/13;
    allow 131.0.72.0/22;
    deny all;

    # ... rest of config
}
```

---

## Option 3: Docker with Traefik (For Docker Deployments)

If running everything in Docker:

### docker-compose.yml Addition

```yaml
services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@ganuda.us"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      # Redirect HTTP to HTTPS
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-certificates:/letsencrypt
    networks:
      - ganuda-network

  public-site:
    image: ganuda-public:latest
    container_name: ganuda-public
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.public.rule=Host(`ganuda.us`) || Host(`www.ganuda.us`)"
      - "traefik.http.routers.public.entrypoints=websecure"
      - "traefik.http.routers.public.tls.certresolver=letsencrypt"
      - "traefik.http.services.public.loadbalancer.server.port=4080"
    networks:
      - ganuda-network

  sag:
    image: ganuda-sag:latest
    container_name: ganuda-sag
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.sag.rule=Host(`sag.ganuda.us`)"
      - "traefik.http.routers.sag.entrypoints=websecure"
      - "traefik.http.routers.sag.tls.certresolver=letsencrypt"
      - "traefik.http.services.sag.loadbalancer.server.port=4000"
    networks:
      - ganuda-network

volumes:
  traefik-certificates:

networks:
  ganuda-network:
    driver: bridge
```

---

## Verification Script

Create `/ganuda/scripts/verify_https.sh`:

```bash
#!/bin/bash
# Verify HTTPS is working correctly

DOMAIN="${1:-ganuda.us}"

echo "=== HTTPS Verification for $DOMAIN ==="
echo ""

# Check certificate
echo "1. Checking SSL Certificate..."
echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN":443 2>/dev/null | \
    openssl x509 -noout -dates -subject -issuer
echo ""

# Check certificate chain
echo "2. Checking Certificate Chain..."
echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN":443 2>/dev/null | \
    grep -E "(depth|verify)"
echo ""

# Check TLS version
echo "3. Checking TLS Version..."
echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN":443 2>/dev/null | \
    grep "Protocol"
echo ""

# Check HTTP redirect
echo "4. Checking HTTP → HTTPS Redirect..."
REDIRECT=$(curl -sI "http://$DOMAIN" | grep -i "location")
if [[ "$REDIRECT" == *"https"* ]]; then
    echo "   ✓ HTTP redirects to HTTPS"
else
    echo "   ✗ HTTP does NOT redirect to HTTPS"
fi
echo ""

# Check HSTS header
echo "5. Checking HSTS Header..."
HSTS=$(curl -sI "https://$DOMAIN" | grep -i "strict-transport")
if [[ -n "$HSTS" ]]; then
    echo "   ✓ HSTS enabled: $HSTS"
else
    echo "   ✗ HSTS not enabled"
fi
echo ""

# Check response
echo "6. Checking HTTPS Response..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN")
if [[ "$HTTP_CODE" == "200" ]]; then
    echo "   ✓ HTTPS returns 200 OK"
else
    echo "   ✗ HTTPS returns $HTTP_CODE"
fi
echo ""

# SSL Labs (manual)
echo "7. For detailed SSL analysis:"
echo "   https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo ""

echo "=== Verification Complete ==="
```

---

## Certificate Monitoring

### Simple Cron Check

Add to crontab:

```bash
# Check cert expiry weekly
0 0 * * 0 /ganuda/scripts/check_cert_expiry.sh
```

Create `/ganuda/scripts/check_cert_expiry.sh`:

```bash
#!/bin/bash
# Alert if certificate expires within 14 days

DOMAIN="ganuda.us"
DAYS_WARNING=14

EXPIRY_DATE=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN":443 2>/dev/null | \
    openssl x509 -noout -enddate | cut -d= -f2)

EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

if [[ $DAYS_LEFT -lt $DAYS_WARNING ]]; then
    echo "WARNING: SSL certificate for $DOMAIN expires in $DAYS_LEFT days!"
    # Add alerting here (email, webhook, etc.)
    exit 1
fi

echo "OK: Certificate valid for $DAYS_LEFT more days"
exit 0
```

---

## DNS Configuration

Ensure these DNS records exist:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | ganuda.us | YOUR_SERVER_IP | 300 |
| A | www | YOUR_SERVER_IP | 300 |
| A | sag | YOUR_SERVER_IP | 300 |
| CNAME | www | ganuda.us | 300 |
| CAA | ganuda.us | 0 issue "letsencrypt.org" | 3600 |

### Verify DNS

```bash
# Check A record
dig +short ganuda.us

# Check CAA record (allows Let's Encrypt to issue certs)
dig +short ganuda.us CAA
```

---

## Firewall Rules

```bash
# Allow HTTP (for Let's Encrypt challenge)
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Optionally block direct access to backend ports
sudo ufw deny 4000/tcp  # SAG only via nginx
sudo ufw deny 4080/tcp  # Public only via nginx
sudo ufw deny 8080/tcp  # Gateway only via nginx

# Check status
sudo ufw status
```

---

## Security Checklist

### Before Going Live

- [ ] Certificate obtained and valid
- [ ] HTTP redirects to HTTPS
- [ ] HSTS header enabled
- [ ] TLS 1.2+ only (no SSLv3, TLS 1.0, 1.1)
- [ ] Strong cipher suites configured
- [ ] Certificate auto-renewal working
- [ ] Monitoring in place for expiry
- [ ] Firewall blocks direct backend access
- [ ] Rate limiting configured

### SSL Labs Grade Target

Aim for A+ on SSL Labs test:
- https://www.ssllabs.com/ssltest/

Common issues that lower grade:
- Weak ciphers → Use modern cipher suite
- No HSTS → Add Strict-Transport-Security header
- Supports TLS 1.0 → Disable old protocols
- Missing CAA record → Add to DNS

---

## Troubleshooting

### Certificate Not Renewing

```bash
# Check certbot logs
sudo journalctl -u certbot

# Manual renewal
sudo certbot renew --force-renewal

# Check timer
sudo systemctl list-timers | grep certbot
```

### Mixed Content Warnings

If browser shows mixed content:
- Check all resources use HTTPS URLs
- Or use protocol-relative URLs: `//example.com/resource`
- Set CSP header: `upgrade-insecure-requests`

### Connection Refused

```bash
# Check nginx running
sudo systemctl status nginx

# Check ports open
sudo ss -tlnp | grep -E ":80|:443"

# Check firewall
sudo ufw status
```

---

## Rollback Plan

If HTTPS causes issues:

```bash
# Disable HTTPS site
sudo rm /etc/nginx/sites-enabled/ganuda.us

# Enable HTTP-only fallback
sudo ln -s /etc/nginx/sites-available/ganuda-http-only /etc/nginx/sites-enabled/

# Reload
sudo nginx -s reload
```

Create `/etc/nginx/sites-available/ganuda-http-only`:

```nginx
server {
    listen 80;
    server_name ganuda.us www.ganuda.us;

    location / {
        proxy_pass http://127.0.0.1:4080;
    }
}
```

---

## Success Criteria

1. `https://ganuda.us` loads without warnings
2. `http://ganuda.us` redirects to HTTPS
3. SSL Labs grade: A or A+
4. Certificate auto-renews
5. All subdomains covered (www, sag)
6. Security headers present

---

*For Seven Generations*
