# HaliCred Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the HaliCred platform to production environments. The deployment process covers both backend and frontend components with best practices for security, scalability, and reliability.

## Prerequisites

### System Requirements

#### Backend
- **OS**: Ubuntu 20.04 LTS or newer
- **CPU**: 4+ cores (8+ recommended for production)
- **Memory**: 8GB RAM minimum (16GB+ recommended)
- **Storage**: 100GB SSD minimum (500GB+ recommended)
- **Network**: Stable internet connection with low latency to AI services

#### Frontend
- **CDN**: CloudFlare or AWS CloudFront
- **Storage**: S3-compatible object storage
- **SSL**: Valid SSL certificates

#### Database
- **PostgreSQL**: Version 15 or newer
- **Extensions**: PostGIS for geospatial data
- **Backup**: Automated backup solution
- **High Availability**: Master-slave replication recommended

### Required Services

#### External APIs
- **Google Gemini API**: AI orchestration
- **Google Vision API**: OCR and image analysis
- **Climatiq API**: Emission factor data
- **Africa's Talking**: SMS/USSD services (optional)

#### Infrastructure Services
- **Redis**: Caching and session management
- **MinIO/S3**: File storage
- **Docker**: Containerization
- **Nginx**: Reverse proxy and load balancer

## Environment Setup

### 1. Server Preparation

#### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git software-properties-common
```

#### Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

#### Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Database Setup

#### PostgreSQL Installation
```bash
sudo apt install -y postgresql postgresql-contrib postgis
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Database Configuration
```bash
sudo -u postgres psql

-- Create database and user
CREATE DATABASE halicred_prod;
CREATE USER halicred_user WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE halicred_prod TO halicred_user;

-- Enable PostGIS
\c halicred_prod
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

\q
```

#### Production Database Settings
Edit `/etc/postgresql/15/main/postgresql.conf`:
```ini
# Performance tuning
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 64MB

# Connection settings
max_connections = 200
listen_addresses = '*'

# Logging
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000

# WAL settings for backup
wal_level = replica
max_wal_senders = 3
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/15/main/archive/%f'
```

Edit `/etc/postgresql/15/main/pg_hba.conf`:
```
# Allow application connections
host    halicred_prod    halicred_user    10.0.0.0/8    md5
host    halicred_prod    halicred_user    172.16.0.0/12  md5
host    halicred_prod    halicred_user    192.168.0.0/16 md5
```

### 3. Redis Setup

#### Installation
```bash
sudo apt install -y redis-server
```

#### Configuration
Edit `/etc/redis/redis.conf`:
```ini
# Security
requirepass your_redis_password_here
bind 127.0.0.1 ::1

# Memory optimization
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
```

Restart Redis:
```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## Application Deployment

### 1. Code Deployment

#### Clone Repository
```bash
cd /opt
sudo git clone https://github.com/Annfelicty/hali-cred.git halicred
sudo chown -R $USER:$USER /opt/halicred
cd /opt/halicred
```

#### Checkout Production Branch
```bash
git checkout main
git pull origin main
```

### 2. Backend Deployment

#### Environment Configuration
Create `/opt/halicred/backend/.env.production`:
```bash
# Database
DATABASE_URL=postgresql://halicred_user:secure_password_here@localhost:5432/halicred_prod

# Redis
REDIS_URL=redis://:your_redis_password_here@localhost:6379/0

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=your_256_bit_secret_key_here
ALGORITHM=HS256

# AI Services
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/opt/halicred/backend/keys/google-vision-prod.json
CLIMATIQ_API_KEY=your_climatiq_api_key_here

# File Storage
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
BUCKET_NAME=halicred-prod-files

# External Services
CELERY_BROKER_URL=redis://:your_redis_password_here@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:your_redis_password_here@localhost:6379/2

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
```

#### API Keys Setup
```bash
# Create keys directory
mkdir -p /opt/halicred/backend/keys

# Add Google Vision service account (get from Google Cloud Console)
sudo nano /opt/halicred/backend/keys/google-vision-prod.json
```

#### Docker Deployment
Create `/opt/halicred/docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENV_FILE=/app/.env.production
    volumes:
      - ./backend/.env.production:/app/.env.production
      - ./backend/keys:/app/keys
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass your_redis_password_here
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    build:
      context: ./nginx
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    restart: unless-stopped

volumes:
  redis_data:
```

#### Backend Dockerfile
Create `/opt/halicred/backend/Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-prod.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Database Migration
```bash
cd /opt/halicred/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt

# Run migrations
export DATABASE_URL="postgresql://halicred_user:secure_password_here@localhost:5432/halicred_prod"
alembic upgrade head
```

#### Start Backend
```bash
cd /opt/halicred
docker-compose -f docker-compose.prod.yml up -d backend
```

### 3. Frontend Deployment

#### Build Configuration
Create `/opt/halicred/frontend-web/.env.production`:
```bash
VITE_API_BASE_URL=https://api.halicred.com
VITE_APP_ENV=production
VITE_SENTRY_DSN=your_frontend_sentry_dsn_here
```

#### Build Application
```bash
cd /opt/halicred/frontend-web
npm ci --production
npm run build
```

#### Nginx Configuration
Create `/opt/halicred/nginx/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/xml+rss
        application/javascript
        application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;

    # Backend upstream
    upstream backend {
        server backend:8000;
    }

    # HTTPS redirect
    server {
        listen 80;
        server_name api.halicred.com app.halicred.com;
        return 301 https://$server_name$request_uri;
    }

    # API server
    server {
        listen 443 ssl http2;
        server_name api.halicred.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API endpoints
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Auth endpoints (stricter rate limiting)
        location /auth/ {
            limit_req zone=auth burst=5 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # Frontend server
    server {
        listen 443 ssl http2;
        server_name app.halicred.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # React router support
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Static assets caching
        location /assets/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### 4. SSL Certificate Setup

#### Using Let's Encrypt
```bash
sudo apt install -y certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d api.halicred.com -d app.halicred.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Copy certificates to nginx volume
```bash
sudo mkdir -p /opt/halicred/ssl
sudo cp /etc/letsencrypt/live/api.halicred.com/fullchain.pem /opt/halicred/ssl/
sudo cp /etc/letsencrypt/live/api.halicred.com/privkey.pem /opt/halicred/ssl/
sudo chown -R $USER:$USER /opt/halicred/ssl
```

### 5. Complete Deployment

#### Start all services
```bash
cd /opt/halicred
docker-compose -f docker-compose.prod.yml up -d
```

#### Verify deployment
```bash
# Check containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Test API
curl -k https://api.halicred.com/health

# Test frontend
curl -k https://app.halicred.com
```

## Post-Deployment Configuration

### 1. Database Optimization

#### Create additional indexes
```sql
-- Performance indexes for production
CREATE INDEX CONCURRENTLY idx_evidence_user_created ON evidence(user_id, created_at);
CREATE INDEX CONCURRENTLY idx_greenscores_user_computed ON greenscores(user_id, computed_at);
CREATE INDEX CONCURRENTLY idx_loan_apps_status_created ON loan_applications(status, created_at);
```

#### Setup database monitoring
```bash
# Install pg_stat_statements
sudo -u postgres psql -d halicred_prod -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
```

### 2. Application Monitoring

#### Health check endpoints
```bash
# API health
curl https://api.halicred.com/health

# Database connectivity
curl https://api.halicred.com/health/db

# External services
curl https://api.halicred.com/health/ai
```

#### Log aggregation
```bash
# Setup log rotation
sudo nano /etc/logrotate.d/halicred

/opt/halicred/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 root root
    postrotate
        docker-compose -f /opt/halicred/docker-compose.prod.yml restart nginx
    endscript
}
```

### 3. Backup Configuration

#### Database backup script
Create `/opt/halicred/scripts/backup_db.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/halicred/backups"
DB_NAME="halicred_prod"
DB_USER="halicred_user"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/halicred_$DATE.sql.gz

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/halicred_$DATE.sql.gz s3://halicred-backups/database/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "halicred_*.sql.gz" -mtime +30 -delete

echo "Backup completed: halicred_$DATE.sql.gz"
```

Make executable and schedule:
```bash
chmod +x /opt/halicred/scripts/backup_db.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/halicred/scripts/backup_db.sh
```

### 4. Security Hardening

#### Firewall configuration
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

#### Fail2ban for SSH protection
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Scaling Considerations

### 1. Horizontal Scaling

#### Load Balancer Setup
- Use AWS ALB, Google Cloud Load Balancer, or Nginx Plus
- Configure health checks for backend instances
- Enable session stickiness if needed

#### Multiple Backend Instances
```yaml
# In docker-compose.prod.yml
backend:
  deploy:
    replicas: 3
  ports:
    - "8000-8002:8000"
```

### 2. Database Scaling

#### Read Replicas
```bash
# Setup PostgreSQL streaming replication
# Master: Add to postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 8

# Slave: Configure recovery.conf
standby_mode = 'on'
primary_conninfo = 'host=master_ip port=5432 user=replication'
```

#### Connection Pooling
```bash
# Install PgBouncer
sudo apt install -y pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
halicred_prod = host=localhost port=5432 dbname=halicred_prod

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### 3. Caching Strategy

#### Redis Clustering
```yaml
# Redis cluster for high availability
redis-cluster:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
  ports:
    - "7000-7005:7000-7005"
```

#### CDN Configuration
- CloudFlare or AWS CloudFront for static assets
- Cache API responses where appropriate
- Set proper cache headers

## Monitoring and Alerting

### 1. Application Monitoring

#### Prometheus Configuration
```yaml
# docker-compose.monitoring.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=secure_password
```

#### Key Metrics to Monitor
- API response times
- Database query performance
- AI service response times
- Error rates
- Resource utilization (CPU, memory, disk)

### 2. Log Monitoring

#### ELK Stack (Optional)
```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
  environment:
    - discovery.type=single-node
    - "ES_JAVA_OPTS=-Xms2g -Xmx2g"

kibana:
  image: docker.elastic.co/kibana/kibana:8.5.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

### 3. Alerting Rules

#### Critical Alerts
- API downtime > 1 minute
- Database connection failures
- High error rates (>5%)
- Disk space > 85%
- Memory usage > 90%

#### Warning Alerts
- Response time > 2 seconds
- AI service degradation
- High CPU usage (>80%)
- Failed backups

## Rollback Procedures

### 1. Application Rollback

#### Quick Rollback
```bash
cd /opt/halicred

# Stop current services
docker-compose -f docker-compose.prod.yml down

# Rollback to previous version
git checkout <previous_commit_hash>

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Database Rollback
```bash
# Restore from backup
gunzip -c /opt/halicred/backups/halicred_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -U halicred_user -d halicred_prod
```

### 2. Migration Rollback

#### Alembic Downgrade
```bash
cd /opt/halicred/backend
source venv/bin/activate
alembic downgrade -1  # Go back one migration
```

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common causes:
# - Database connection issues
# - Missing environment variables
# - Port conflicts
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
psql -h localhost -U halicred_user -d halicred_prod

# Check PostgreSQL status
sudo systemctl status postgresql

# Review connection settings
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

#### 3. SSL Certificate Issues
```bash
# Renew certificates
sudo certbot renew --dry-run

# Check certificate expiry
openssl x509 -in /opt/halicred/ssl/fullchain.pem -noout -dates
```

#### 4. High Memory Usage
```bash
# Check container resource usage
docker stats

# Optimize PostgreSQL
# Reduce shared_buffers if memory constrained
# Tune work_mem and maintenance_work_mem
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Analyze query performance
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Update table statistics
ANALYZE;

-- Reindex if needed
REINDEX DATABASE halicred_prod;
```

#### 2. Application Optimization
- Enable API response caching
- Optimize AI service calls
- Use database connection pooling
- Implement background job processing

## Maintenance Procedures

### 1. Regular Maintenance

#### Weekly Tasks
- Review application logs
- Check disk space usage
- Monitor database performance
- Update security patches

#### Monthly Tasks
- Rotate log files
- Review backup integrity
- Update dependencies
- Performance optimization review

### 2. Updates and Patches

#### Security Updates
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Application updates
cd /opt/halicred
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Dependency Updates
```bash
# Backend dependencies
cd /opt/halicred/backend
pip list --outdated
pip install -r requirements-prod.txt --upgrade

# Frontend dependencies
cd /opt/halicred/frontend-web
npm audit
npm update
```

---

**Last Updated**: September 30, 2025
**Deployment Version**: 7.0.0
**Supported Environments**: Ubuntu 20.04+, Docker 20.10+, PostgreSQL 15+