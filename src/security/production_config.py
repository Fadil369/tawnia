"""
Production Security Configuration
Security settings and hardening for production deployment
"""

import os
from pathlib import Path

# Production Environment Configuration
PRODUCTION_CONFIG = {
    # Server Security
    "HOST": "127.0.0.1",  # Never bind to 0.0.0.0 in production without proper security
    "PORT": 8000,
    "DEBUG": False,
    "TESTING": False,
    
    # JWT Configuration
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": 15,  # Shorter token expiry
    "JWT_REFRESH_TOKEN_EXPIRE_DAYS": 1,    # Shorter refresh token expiry
    "JWT_ALGORITHM": "HS256",
    
    # Rate Limiting (Stricter)
    "RATE_LIMIT_REQUESTS_PER_MINUTE": 30,
    "RATE_LIMIT_REQUESTS_PER_HOUR": 500,
    "RATE_LIMIT_BURST_LIMIT": 5,
    
    # File Upload Security
    "MAX_FILE_SIZE_MB": 25,  # Smaller limit for production
    "SCAN_FOR_VIRUSES": True,
    "QUARANTINE_SUSPICIOUS_FILES": True,
    
    # Security Headers
    "ENABLE_SECURITY_HEADERS": True,
    "ENABLE_HTTPS_REDIRECT": True,
    "HSTS_MAX_AGE": 31536000,  # 1 year
    
    # CORS (Restrictive)
    "CORS_ORIGINS": [],  # Must be configured with specific domains
    "CORS_ALLOW_CREDENTIALS": True,
    "CORS_METHODS": ["GET", "POST", "PUT", "DELETE"],
    "CORS_HEADERS": ["Content-Type", "Authorization"],
    
    # Database Security
    "DATABASE_SSL_REQUIRED": True,
    "DATABASE_SSL_VERIFY": True,
    "DATABASE_CONNECTION_TIMEOUT": 30,
    "DATABASE_MAX_CONNECTIONS": 20,
    
    # Logging Configuration
    "LOG_LEVEL": "INFO",
    "ENABLE_AUDIT_LOGGING": True,
    "LOG_RETENTION_DAYS": 90,
    "SENSITIVE_DATA_LOGGING": False,
    
    # Authentication
    "ENABLE_2FA": True,
    "PASSWORD_MIN_LENGTH": 14,
    "MAX_LOGIN_ATTEMPTS": 3,
    "ACCOUNT_LOCKOUT_DURATION_MINUTES": 30,
    
    # Session Security
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Strict",
    
    # Content Security
    "CSP_DEFAULT_SRC": "'self'",
    "CSP_SCRIPT_SRC": "'self'",
    "CSP_STYLE_SRC": "'self'",
    "CSP_IMG_SRC": "'self' data:",
    "CSP_FONT_SRC": "'self'",
    "CSP_CONNECT_SRC": "'self'",
    "CSP_FRAME_ANCESTORS": "'none'",
    
    # API Security
    "API_RATE_LIMIT_PER_IP": 1000,  # Per day
    "API_REQUIRE_AUTHENTICATION": True,
    "API_VALIDATE_CONTENT_TYPE": True,
    
    # Monitoring
    "ENABLE_SECURITY_MONITORING": True,
    "ALERT_ON_SUSPICIOUS_ACTIVITY": True,
    "SECURITY_LOG_RETENTION_DAYS": 365,
}

# Security Checklist for Production Deployment
PRODUCTION_SECURITY_CHECKLIST = [
    "✓ Change default JWT secret key",
    "✓ Configure CORS origins for your domains",
    "✓ Enable HTTPS and obtain SSL certificate",
    "✓ Configure trusted proxy addresses",
    "✓ Set up database SSL connection",
    "✓ Configure email for security alerts",
    "✓ Set up log aggregation and monitoring",
    "✓ Configure backup encryption",
    "✓ Enable virus scanning for file uploads",
    "✓ Set up intrusion detection system",
    "✓ Configure firewall rules",
    "✓ Set up regular security audits",
    "✓ Configure automated security updates",
    "✓ Set up incident response procedures",
    "✓ Train staff on security best practices",
    "✓ Implement data retention policies",
    "✓ Configure GDPR/HIPAA compliance features",
    "✓ Set up disaster recovery procedures",
    "✓ Configure security headers",
    "✓ Enable audit logging",
]

def generate_production_env():
    """Generate production .env file template"""
    env_content = f"""# Production Environment Configuration - Tawnia Healthcare Analytics
# CRITICAL: Review and customize all values before deployment

# Server Configuration
HOST={PRODUCTION_CONFIG['HOST']}
PORT={PRODUCTION_CONFIG['PORT']}
ENVIRONMENT=production
DEBUG={PRODUCTION_CONFIG['DEBUG']}

# Security - MUST CHANGE THESE VALUES
SECRET_KEY=CHANGE_ME_TO_CRYPTOGRAPHICALLY_SECURE_VALUE_AT_LEAST_32_CHARS
JWT_SECRET_KEY=CHANGE_ME_TO_CRYPTOGRAPHICALLY_SECURE_JWT_KEY_AT_LEAST_32_CHARS
JWT_ACCESS_TOKEN_EXPIRE_MINUTES={PRODUCTION_CONFIG['JWT_ACCESS_TOKEN_EXPIRE_MINUTES']}
JWT_REFRESH_TOKEN_EXPIRE_DAYS={PRODUCTION_CONFIG['JWT_REFRESH_TOKEN_EXPIRE_DAYS']}

# Database - Configure for your production database
DATABASE_URL=postgresql://username:password@localhost:5432/tawnia_prod
DATABASE_SSL_REQUIRED={PRODUCTION_CONFIG['DATABASE_SSL_REQUIRED']}
DATABASE_SSL_VERIFY={PRODUCTION_CONFIG['DATABASE_SSL_VERIFY']}

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE={PRODUCTION_CONFIG['RATE_LIMIT_REQUESTS_PER_MINUTE']}
RATE_LIMIT_REQUESTS_PER_HOUR={PRODUCTION_CONFIG['RATE_LIMIT_REQUESTS_PER_HOUR']}
RATE_LIMIT_BURST_LIMIT={PRODUCTION_CONFIG['RATE_LIMIT_BURST_LIMIT']}

# File Upload Security
MAX_FILE_SIZE_MB={PRODUCTION_CONFIG['MAX_FILE_SIZE_MB']}
SCAN_FOR_VIRUSES={PRODUCTION_CONFIG['SCAN_FOR_VIRUSES']}
ALLOWED_FILE_EXTENSIONS=.xlsx,.xls,.csv

# CORS - CONFIGURE FOR YOUR DOMAINS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_CREDENTIALS={PRODUCTION_CONFIG['CORS_ALLOW_CREDENTIALS']}

# Security Headers
ENABLE_SECURITY_HEADERS={PRODUCTION_CONFIG['ENABLE_SECURITY_HEADERS']}
ENABLE_HTTPS_REDIRECT={PRODUCTION_CONFIG['ENABLE_HTTPS_REDIRECT']}
HSTS_MAX_AGE={PRODUCTION_CONFIG['HSTS_MAX_AGE']}

# Authentication
ENABLE_2FA={PRODUCTION_CONFIG['ENABLE_2FA']}
PASSWORD_MIN_LENGTH={PRODUCTION_CONFIG['PASSWORD_MIN_LENGTH']}
MAX_LOGIN_ATTEMPTS={PRODUCTION_CONFIG['MAX_LOGIN_ATTEMPTS']}

# Logging
LOG_LEVEL={PRODUCTION_CONFIG['LOG_LEVEL']}
ENABLE_AUDIT_LOGGING={PRODUCTION_CONFIG['ENABLE_AUDIT_LOGGING']}
LOG_RETENTION_DAYS={PRODUCTION_CONFIG['LOG_RETENTION_DAYS']}

# Monitoring and Alerts - Configure for your infrastructure
SENTRY_DSN=your_sentry_dsn_here
SLACK_WEBHOOK_URL=your_slack_webhook_for_alerts
EMAIL_SMTP_SERVER=your_smtp_server
EMAIL_SECURITY_ALERTS=security@yourdomain.com

# External Services
OPENAI_API_KEY=your_openai_api_key_if_needed
VIRUS_SCAN_API_KEY=your_virus_scanning_service_key

# Backup Configuration
BACKUP_ENCRYPTION_KEY=your_backup_encryption_key
BACKUP_RETENTION_DAYS=90
"""
    
    return env_content

def generate_nginx_config():
    """Generate secure Nginx configuration"""
    nginx_config = """# Secure Nginx Configuration for Tawnia Healthcare Analytics

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    # File Upload Limits
    client_max_body_size 50M;
    
    # Hide Server Information
    server_tokens off;
    
    # Proxy to FastAPI
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Special rate limiting for login endpoints
    location ~ ^/(auth|login) {
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(env|git|svn)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Logging
    access_log /var/log/nginx/tawnia_access.log;
    error_log /var/log/nginx/tawnia_error.log;
}
"""
    return nginx_config

def generate_docker_security_config():
    """Generate secure Docker configuration"""
    dockerfile_security = """# Security-hardened Dockerfile for Production

FROM python:3.11-slim-bullseye

# Create non-root user
RUN groupadd -r tawnia && useradd -r -g tawnia tawnia

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership to non-root user
RUN chown -R tawnia:tawnia /app

# Switch to non-root user
USER tawnia

# Security: Remove sensitive files
RUN rm -f .env* || true

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "4"]
"""
    
    docker_compose_security = """# Security-hardened Docker Compose for Production

version: '3.8'

services:
  app:
    build: .
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs:rw
      - ./uploads:/app/uploads:rw
    networks:
      - tawnia-internal
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    read_only: true
    tmpfs:
      - /tmp
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - app
    networks:
      - tawnia-internal
    security_opt:
      - no-new-privileges:true

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: tawnia_prod
      POSTGRES_USER: tawnia_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - tawnia-internal
    secrets:
      - db_password
    security_opt:
      - no-new-privileges:true

networks:
  tawnia-internal:
    driver: bridge

volumes:
  postgres_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
"""
    
    return dockerfile_security, docker_compose_security

if __name__ == "__main__":
    """Generate production configuration files"""
    
    # Create production directory
    prod_dir = Path("production-config")
    prod_dir.mkdir(exist_ok=True)
    
    # Generate .env.production
    with open(prod_dir / ".env.production", "w") as f:
        f.write(generate_production_env())
    
    # Generate nginx config
    with open(prod_dir / "nginx.conf", "w") as f:
        f.write(generate_nginx_config())
    
    # Generate Docker configs
    dockerfile, docker_compose = generate_docker_security_config()
    
    with open(prod_dir / "Dockerfile.production", "w") as f:
        f.write(dockerfile)
    
    with open(prod_dir / "docker-compose.production.yml", "w") as f:
        f.write(docker_compose)
    
    # Generate security checklist
    with open(prod_dir / "SECURITY_CHECKLIST.md", "w") as f:
        f.write("# Production Security Checklist\n\n")
        for item in PRODUCTION_SECURITY_CHECKLIST:
            f.write(f"- [ ] {item}\n")
    
    print("Production configuration files generated in 'production-config' directory")
    print("Please review and customize all values before deployment!")