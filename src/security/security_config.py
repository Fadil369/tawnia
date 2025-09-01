"""
Enhanced Security Configuration for Tawnia Healthcare Analytics
Comprehensive security settings and hardening configurations
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class SecurityHeaders:
    """Security headers configuration"""
    content_security_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    strict_transport_security: str = "max-age=31536000; includeSubDomains; preload"
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = (
        "accelerometer=(), camera=(), geolocation=(), "
        "gyroscope=(), magnetometer=(), microphone=(), "
        "payment=(), usb=()"
    )


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    enable_ip_whitelist: bool = True
    ip_whitelist: List[str] = None
    
    def __post_init__(self):
        if self.ip_whitelist is None:
            self.ip_whitelist = ["127.0.0.1", "::1"]


@dataclass
class AuthenticationConfig:
    """Authentication configuration"""
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    max_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    enable_2fa: bool = False  # Set to True for production
    
    def validate(self) -> bool:
        """Validate authentication configuration"""
        if self.jwt_secret_key == "change-me-in-production":
            logger.warning("JWT secret key is using default value - change in production!")
            return False
        if len(self.jwt_secret_key) < 32:
            logger.error("JWT secret key must be at least 32 characters long")
            return False
        return True


@dataclass
class FileSecurityConfig:
    """File upload and processing security configuration"""
    max_file_size_mb: int = 50
    allowed_extensions: List[str] = None
    upload_path: str = "uploads"
    scan_for_viruses: bool = False  # Enable with ClamAV in production
    quarantine_suspicious_files: bool = True
    allowed_mime_types: List[str] = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = [".xlsx", ".xls", ".csv"]
        if self.allowed_mime_types is None:
            self.allowed_mime_types = [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
                "text/csv"
            ]


@dataclass
class DatabaseSecurityConfig:
    """Database security configuration"""
    enable_ssl: bool = True
    connection_timeout: int = 30
    max_connections: int = 20
    enable_query_logging: bool = False  # Only for debugging
    encrypt_sensitive_fields: bool = True
    backup_encryption: bool = True
    enable_audit_logging: bool = True


@dataclass
class NetworkSecurityConfig:
    """Network security configuration"""
    enable_cors: bool = True
    cors_origins: List[str] = None
    cors_methods: List[str] = None
    cors_headers: List[str] = None
    enable_https_redirect: bool = True
    trusted_proxies: List[str] = None
    max_request_size_mb: int = 100
    
    def __post_init__(self):
        if self.cors_origins is None:
            # Restrictive CORS for production
            self.cors_origins = ["https://localhost:3000", "https://127.0.0.1:3000"]
        if self.cors_methods is None:
            self.cors_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        if self.cors_headers is None:
            self.cors_headers = ["Content-Type", "Authorization", "X-Requested-With"]
        if self.trusted_proxies is None:
            self.trusted_proxies = ["127.0.0.1"]


class SecurityConfig:
    """Main security configuration class"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.headers = SecurityHeaders()
        self.rate_limit = RateLimitConfig()
        self.authentication = AuthenticationConfig()
        self.file_security = FileSecurityConfig()
        self.database_security = DatabaseSecurityConfig()
        self.network_security = NetworkSecurityConfig()
        
        # Apply environment-specific configurations
        self._configure_for_environment()
    
    def _configure_for_environment(self):
        """Configure security settings based on environment"""
        if self.environment == "production":
            self._configure_production()
        elif self.environment == "staging":
            self._configure_staging()
        else:
            self._configure_development()
    
    def _configure_production(self):
        """Production security configuration"""
        logger.info("Applying production security configuration")
        
        # Stricter rate limiting
        self.rate_limit.requests_per_minute = 30
        self.rate_limit.requests_per_hour = 500
        
        # Enhanced authentication
        self.authentication.jwt_access_token_expire_minutes = 15
        self.authentication.enable_2fa = True
        self.authentication.max_login_attempts = 3
        
        # Stricter file security
        self.file_security.max_file_size_mb = 25
        self.file_security.scan_for_viruses = True
        
        # Enhanced database security
        self.database_security.enable_ssl = True
        self.database_security.enable_query_logging = False
        
        # Restrictive CORS
        self.network_security.cors_origins = []  # Configure specific domains
        
        # Stricter CSP
        self.headers.content_security_policy = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
    
    def _configure_staging(self):
        """Staging security configuration"""
        logger.info("Applying staging security configuration")
        
        # Moderate security settings
        self.rate_limit.requests_per_minute = 45
        self.authentication.jwt_access_token_expire_minutes = 20
        self.file_security.scan_for_viruses = True
    
    def _configure_development(self):
        """Development security configuration"""
        logger.info("Applying development security configuration")
        
        # Relaxed but secure development settings
        self.rate_limit.requests_per_minute = 100
        self.authentication.jwt_access_token_expire_minutes = 60
        
        # Allow localhost CORS
        self.network_security.cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:3000",
            "https://127.0.0.1:3000"
        ]
    
    def validate_configuration(self) -> bool:
        """Validate all security configurations"""
        logger.info("Validating security configuration")
        
        is_valid = True
        
        # Validate authentication
        if not self.authentication.validate():
            is_valid = False
        
        # Check for production readiness
        if self.environment == "production":
            if not self._validate_production_readiness():
                is_valid = False
        
        if is_valid:
            logger.info("Security configuration validation passed")
        else:
            logger.error("Security configuration validation failed")
        
        return is_valid
    
    def _validate_production_readiness(self) -> bool:
        """Validate production-specific security requirements"""
        issues = []
        
        if self.authentication.jwt_secret_key == "change-me-in-production":
            issues.append("JWT secret key is using default value")
        
        if not self.database_security.enable_ssl:
            issues.append("Database SSL is disabled")
        
        if not self.file_security.scan_for_viruses:
            issues.append("Virus scanning is disabled")
        
        if not self.authentication.enable_2fa:
            issues.append("Two-factor authentication is disabled")
        
        if len(self.network_security.cors_origins) == 0:
            logger.warning("CORS origins not configured for production")
        
        if issues:
            for issue in issues:
                logger.error(f"Production security issue: {issue}")
            return False
        
        return True
    
    def get_security_headers_dict(self) -> Dict[str, str]:
        """Get security headers as dictionary for middleware"""
        return {
            "Content-Security-Policy": self.headers.content_security_policy,
            "Strict-Transport-Security": self.headers.strict_transport_security,
            "X-Content-Type-Options": self.headers.x_content_type_options,
            "X-Frame-Options": self.headers.x_frame_options,
            "X-XSS-Protection": self.headers.x_xss_protection,
            "Referrer-Policy": self.headers.referrer_policy,
            "Permissions-Policy": self.headers.permissions_policy,
        }
    
    def log_security_status(self):
        """Log current security configuration status"""
        logger.info(f"Security Configuration Status - Environment: {self.environment}")
        logger.info(f"Rate Limiting: {self.rate_limit.requests_per_minute} req/min")
        logger.info(f"JWT Token Expiry: {self.authentication.jwt_access_token_expire_minutes} minutes")
        logger.info(f"2FA Enabled: {self.authentication.enable_2fa}")
        logger.info(f"File Scanning: {self.file_security.scan_for_viruses}")
        logger.info(f"Database SSL: {self.database_security.enable_ssl}")
        logger.info(f"CORS Origins: {len(self.network_security.cors_origins)}")


# Global security configuration instance
_security_config: Optional[SecurityConfig] = None


def get_security_config(environment: str = None) -> SecurityConfig:
    """Get or create global security configuration"""
    global _security_config
    
    if _security_config is None:
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        _security_config = SecurityConfig(environment)
        _security_config.validate_configuration()
        _security_config.log_security_status()
    
    return _security_config


def reset_security_config():
    """Reset global security configuration (for testing)"""
    global _security_config
    _security_config = None