# Enhanced Reading Practice Platform - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Enhanced Reading Practice Platform to production. The platform consists of a Django REST API backend and React TypeScript frontend.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│  Frontend (React) │────│  Backend (Django) │
│   (Nginx/Apache)│    │   Static Files   │    │    REST API     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │   Database      │
                                               │  (PostgreSQL)   │
                                               └─────────────────┘
```

## Prerequisites

### Server Requirements
- **OS**: Ubuntu 20.04 LTS or newer (recommended)
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 20GB SSD
- **CPU**: 2 cores minimum, 4+ recommended

### Software Requirements
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Nginx
- Redis (for caching and sessions)
- Supervisor (for process management)

## Pre-Deployment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib redis-server nginx supervisor git

# Create deployment user
sudo adduser deploy
sudo usermod -aG sudo deploy
su - deploy
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE reading_platform;
CREATE USER reading_platform_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE reading_platform TO reading_platform_user;
ALTER USER reading_platform_user CREATEDB;
\q

# Configure PostgreSQL for production
sudo nano /etc/postgresql/12/main/postgresql.conf
# Uncomment and modify these settings:
# listen_addresses = 'localhost'
# max_connections = 100
# shared_buffers = 256MB
# effective_cache_size = 1GB

sudo systemctl restart postgresql
```

### 3. Redis Configuration

```bash
sudo nano /etc/redis/redis.conf
# Set these configurations:
# maxmemory 256mb
# maxmemory-policy allkeys-lru
# bind 127.0.0.1

sudo systemctl restart redis
```

## Backend Deployment

### 1. Code Deployment

```bash
# Create application directory
sudo mkdir -p /var/www/reading-platform
sudo chown deploy:deploy /var/www/reading-platform

# Clone repository
cd /var/www/reading-platform
git clone https://github.com/your-repo/reading-platform.git .

# Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Create production environment file
nano backend/.env
```

```env
# Production Environment Variables
DEBUG=False
SECRET_KEY=your_super_secret_key_here_50_chars_minimum
DATABASE_URL=postgres://reading_platform_user:your_secure_password@localhost/reading_platform
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your.server.ip

# Security
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Redis Cache
REDIS_URL=redis://127.0.0.1:6379/0

# Media/Static files
STATIC_ROOT=/var/www/reading-platform/static
MEDIA_ROOT=/var/www/reading-platform/media

# Email (configure according to your provider)
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password

# API Keys
API_KEYS=your_external_api_keys_comma_separated
```

### 3. Django Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run security audit
python manage.py security_audit

# Test the application
python manage.py check --deploy
```

### 4. Gunicorn Configuration

```bash
# Install gunicorn
pip install gunicorn

# Create gunicorn configuration
nano /var/www/reading-platform/backend/gunicorn.conf.py
```

```python
# Gunicorn configuration
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 60
preload_app = True
chdir = "/var/www/reading-platform/backend"
user = "deploy"
group = "deploy"
tmp_upload_dir = None
errorlog = "/var/log/reading-platform/gunicorn-error.log"
accesslog = "/var/log/reading-platform/gunicorn-access.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
```

### 5. Supervisor Configuration

```bash
# Create log directory
sudo mkdir -p /var/log/reading-platform
sudo chown deploy:deploy /var/log/reading-platform

# Create supervisor configuration
sudo nano /etc/supervisor/conf.d/reading-platform.conf
```

```ini
[program:reading-platform]
command=/var/www/reading-platform/backend/venv/bin/gunicorn reading_platform.wsgi:application -c /var/www/reading-platform/backend/gunicorn.conf.py
directory=/var/www/reading-platform/backend
user=deploy
autostart=true
autorestart=true
stdout_logfile=/var/log/reading-platform/django.log
stderr_logfile=/var/log/reading-platform/django-error.log
environment=PATH="/var/www/reading-platform/backend/venv/bin"
```

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start reading-platform
```

## Frontend Deployment

### 1. Build Frontend

```bash
cd /var/www/reading-platform/frontend

# Install dependencies
npm ci --production

# Create production environment file
nano .env.production
```

```env
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

```bash
# Build for production
npm run build

# Copy build files to static directory
sudo cp -r build/* /var/www/reading-platform/static/
sudo chown -R deploy:deploy /var/www/reading-platform/static/
```

## Nginx Configuration

### 1. SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 2. Nginx Site Configuration

```bash
sudo nano /etc/nginx/sites-available/reading-platform
```

```nginx
# Reading Platform Nginx Configuration
upstream reading_platform_backend {
    server 127.0.0.1:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # File upload size
    client_max_body_size 50M;
    
    # Static files
    location /static/ {
        alias /var/www/reading-platform/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff always;
    }
    
    # Media files
    location /media/ {
        alias /var/www/reading-platform/media/;
        expires 1y;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options nosniff always;
    }
    
    # API requests
    location /api/ {
        proxy_pass http://reading_platform_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_redirect off;
        
        # Security
        proxy_set_header X-Content-Type-Options nosniff;
        proxy_hide_header X-Powered-By;
    }
    
    # Admin interface
    location /admin/ {
        proxy_pass http://reading_platform_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Additional security for admin
        allow your.admin.ip.address;
        deny all;
    }
    
    # Frontend application
    location / {
        try_files $uri $uri/ /index.html;
        root /var/www/reading-platform/static;
        index index.html;
        
        # Security headers for frontend
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Logging
    access_log /var/log/nginx/reading-platform-access.log;
    error_log /var/log/nginx/reading-platform-error.log warn;
}
```

```bash
# Enable site and test configuration
sudo ln -s /etc/nginx/sites-available/reading-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Monitoring and Logging

### 1. Log Rotation

```bash
sudo nano /etc/logrotate.d/reading-platform
```

```
/var/log/reading-platform/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        sudo supervisorctl restart reading-platform
    endscript
}

/var/log/nginx/reading-platform-*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        sudo systemctl reload nginx
    endscript
}
```

### 2. System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Create monitoring script
nano /home/deploy/monitor.sh
```

```bash
#!/bin/bash
# System monitoring script

LOG_FILE="/var/log/reading-platform/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# System stats
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.2f"), ($3/$2) * 100.0}')
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

# Application health
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/auth/health/ || echo "DOWN")
DB_CONNECTION=$(sudo -u deploy /var/www/reading-platform/backend/venv/bin/python /var/www/reading-platform/backend/manage.py dbshell --command="SELECT 1;" 2>&1 | grep -q "1" && echo "OK" || echo "ERROR")

echo "$DATE | CPU: $CPU_USAGE% | Memory: $MEMORY_USAGE% | Disk: $DISK_USAGE% | Backend: $BACKEND_STATUS | DB: $DB_CONNECTION" >> $LOG_FILE

# Alert if any service is down
if [ "$BACKEND_STATUS" = "DOWN" ] || [ "$DB_CONNECTION" = "ERROR" ]; then
    echo "$DATE | ALERT: Service issues detected" >> $LOG_FILE
    # Add notification logic here (email, webhook, etc.)
fi
```

```bash
# Make script executable
chmod +x /home/deploy/monitor.sh

# Add to crontab
crontab -e
# Add this line:
# */5 * * * * /home/deploy/monitor.sh
```

### 3. Database Backup

```bash
# Create backup script
nano /home/deploy/backup.sh
```

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/var/backups/reading-platform"
DATE=$(date '+%Y%m%d_%H%M%S')
DB_NAME="reading_platform"
DB_USER="reading_platform_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
PGPASSWORD="your_secure_password" pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C /var/www/reading-platform media/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "$(date): Backup completed successfully" >> /var/log/reading-platform/backup.log
```

```bash
# Make script executable
chmod +x /home/deploy/backup.sh

# Add to crontab for daily backups at 2 AM
crontab -e
# Add this line:
# 0 2 * * * /home/deploy/backup.sh
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Install and configure UFW
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port if changed)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable
sudo ufw status verbose
```

### 2. Fail2Ban Setup

```bash
# Install fail2ban
sudo apt install fail2ban

# Create custom jail
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/reading-platform-error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/reading-platform-error.log
maxretry = 10

[django-auth]
enabled = true
filter = django-auth
port = http,https
logpath = /var/log/reading-platform/security.log
maxretry = 5
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Automated Security Updates

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades

# Configure automatic security updates
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Enable automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Health Checks and Alerts

### 1. Application Health Endpoint

Add to Django backend (`backend/health/views.py`):

```python
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import time

def health_check(request):
    """System health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', 60)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'healthy'
        else:
            health_status['checks']['cache'] = 'unhealthy'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
```

## Deployment Checklist

### Pre-Deployment
- [ ] Server meets minimum requirements
- [ ] SSL certificate obtained and configured
- [ ] Environment variables configured
- [ ] Database created and configured
- [ ] Static files directory created
- [ ] Log directories created with proper permissions

### Backend Deployment
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Superuser created
- [ ] Security audit passed
- [ ] Gunicorn configuration tested
- [ ] Supervisor configuration working

### Frontend Deployment  
- [ ] Dependencies installed
- [ ] Production build completed
- [ ] Static files copied to correct location
- [ ] Build tested locally

### Web Server
- [ ] Nginx configuration tested
- [ ] SSL certificate working
- [ ] Security headers configured
- [ ] Rate limiting configured
- [ ] Static file serving working

### Security
- [ ] Firewall configured
- [ ] Fail2ban installed and configured
- [ ] Automated security updates enabled
- [ ] File permissions set correctly
- [ ] Sensitive files protected

### Monitoring
- [ ] Log rotation configured
- [ ] Backup scripts configured
- [ ] Monitoring script configured
- [ ] Health check endpoint working
- [ ] Alert system configured

### Post-Deployment Testing
- [ ] Application loads correctly
- [ ] User registration/login working
- [ ] File uploads working
- [ ] API endpoints responding
- [ ] Admin interface accessible
- [ ] Performance acceptable
- [ ] Security headers present

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if Django application is running: `sudo supervisorctl status`
   - Check Gunicorn logs: `tail -f /var/log/reading-platform/gunicorn-error.log`
   - Restart application: `sudo supervisorctl restart reading-platform`

2. **Static Files Not Loading**
   - Verify static files collected: `python manage.py collectstatic`
   - Check Nginx static file configuration
   - Verify file permissions

3. **Database Connection Errors**
   - Check PostgreSQL status: `sudo systemctl status postgresql`
   - Verify database credentials in environment file
   - Check database connection limits

4. **SSL Certificate Issues**
   - Renew certificate: `sudo certbot renew`
   - Check certificate status: `sudo certbot certificates`
   - Verify Nginx SSL configuration

### Log Locations
- Django Application: `/var/log/reading-platform/django.log`
- Gunicorn: `/var/log/reading-platform/gunicorn-*.log`
- Nginx: `/var/log/nginx/reading-platform-*.log`
- Security: `/var/log/reading-platform/security.log`
- System: `/var/log/syslog`

## Maintenance

### Regular Tasks
- Monitor application logs daily
- Review security logs weekly
- Update dependencies monthly
- Run security audits quarterly
- Test backups monthly
- Review and rotate SSL certificates

### Updates and Upgrades
1. Test updates in staging environment
2. Create full backup before updates
3. Update during low-traffic periods
4. Monitor application closely after updates
5. Be prepared to rollback if issues occur

---

For additional support or questions, refer to the application documentation or contact the development team.