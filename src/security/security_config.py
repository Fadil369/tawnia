"""
Enhanced Security Configuration for Tawnia Healthcare Analytics
Implements comprehensive security settings and best practices
"""

import os
import secrets
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SecurityLevel(Enum):
    """Security level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    requests_per_minute: int = 30
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_size: int = 900  # 15 minutes
    
    # Progressive rate limiting
    strike_threshold: int = 3
    penalty_multiplier: float = 2.0
    max_penalty_time: int = 3600  # 1 hour


@dataclass  
class AuthenticationConfig:
    """Enhanced authentication configuration"""
    jwt_secret_key: str = field(default_factory=lambda: os.getenv(
        "JWT_SECRET", 
        "CHANGE_ME_PRODUCTION_SECRET_" + secrets.token_urlsafe(32)
    ))
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Password policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_history_limit: int = 12
    
    # Account security
    max_login_attempts: int = 3
    account_lockout_duration_minutes: int = 30
    enable_2fa: bool = True
    session_timeout_minutes: int = 30
    
    # JWT Security
    jwt_issuer: str = "tawnia-healthcare-analytics"
    jwt_audience: str = "tawnia-api"
    enable_jwt_blacklist: bool = True
    
    def validate(self) -> bool:
        """Validate authentication configuration"""
        if self.jwt_secret_key.startswith("CHANGE_ME"):
            logger.error("JWT secret key must be changed from default value!")
            return False
        if len(self.jwt_secret_key) < 32:
            logger.error("JWT secret key must be at least 32 characters long")
            return False
        if self.password_min_length < 8:
            logger.warning("Password minimum length should be at least 8 characters")
        return True


@dataclass
class CORSConfig:
    """CORS configuration with security focus"""
    enabled: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: [
        "https://tawnia.brainsait.io"
    ])
    allowed_methods: List[str] = field(default_factory=lambda: [
        "GET", "POST", "PUT", "DELETE", "OPTIONS"
    ])
    allowed_headers: List[str] = field(default_factory=lambda: [
        "Content-Type", 
        "Authorization", 
        "X-Requested-With",
        "X-CSRF-Token"
    ])
    allow_credentials: bool = True
    max_age: int = 86400
    
    def validate_development(self) -> bool:
        """Allow localhost for development"""
        env = os.getenv("ENVIRONMENT", "production")
        if env == "development":
            if "http://localhost:3000" not in self.allowed_origins:
                self.allowed_origins.extend([
                    "http://localhost:3000",
                    "http://localhost:8000",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:8000"
                ])
        return True


@dataclass
class ContentSecurityConfig:
    """Content Security Policy configuration"""
    enabled: bool = True
    
    # CSP Directives
    default_src: List[str] = field(default_factory=lambda: ["'self'"])
    script_src: List[str] = field(default_factory=lambda: [
        "'self'",
        "https://cdnjs.cloudflare.com",
        "https://cdn.jsdelivr.net"
    ])
    style_src: List[str] = field(default_factory=lambda: [
        "'self'",
        "'unsafe-inline'",
        "https://cdnjs.cloudflare.com",
        "https://fonts.googleapis.com"
    ])
    img_src: List[str] = field(default_factory=lambda: [
        "'self'",
        "data:",
        "https:"
    ])
    font_src: List[str] = field(default_factory=lambda: [
        "'self'",
        "https://fonts.gstatic.com"
    ])
    connect_src: List[str] = field(default_factory=lambda: ["'self'"])
    frame_src: List[str] = field(default_factory=lambda: ["'none'"])
    object_src: List[str] = field(default_factory=lambda: ["'none'"])
    
    # Additional Security Headers
    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    
    # HSTS Configuration
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True


@dataclass
class FileSecurityConfig:
    """File upload and processing security"""
    enabled: bool = True
    
    # File restrictions
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_files_per_request: int = 3
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".xlsx", ".xls", ".csv"
    ])
    
    # File validation
    enable_content_type_validation: bool = True
    enable_magic_number_validation: bool = True
    enable_filename_sanitization: bool = True
    
    # Storage security
    upload_directory: str = "uploads"
    enable_virus_scanning: bool = False  # Requires external service
    quarantine_suspicious_files: bool = True
    
    # Processing limits
    max_rows_per_file: int = 1000000
    max_columns_per_file: int = 1000
    processing_timeout_seconds: int = 300  # 5 minutes


@dataclass
class AuditConfig:
    """Audit and logging configuration"""
    enabled: bool = True
    
    # Audit events
    log_authentication_events: bool = True
    log_authorization_failures: bool = True
    log_file_operations: bool = True
    log_data_access: bool = True
    log_configuration_changes: bool = True
    
    # Security events
    log_rate_limit_violations: bool = True
    log_suspicious_activity: bool = True
    log_security_policy_violations: bool = True
    
    # Retention
    audit_log_retention_days: int = 365
    security_log_retention_days: int = 730  # 2 years
    
    # Sensitive data handling
    mask_sensitive_data: bool = True
    log_ip_addresses: bool = True
    log_user_agents: bool = True


@dataclass
class SecurityConfig:
    """Master security configuration"""
    
    # Security level
    security_level: SecurityLevel = SecurityLevel.HIGH
    
    # Component configurations
    rate_limiting: RateLimitConfig = field(default_factory=RateLimitConfig)
    authentication: AuthenticationConfig = field(default_factory=AuthenticationConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    content_security: ContentSecurityConfig = field(default_factory=ContentSecurityConfig)
    file_security: FileSecurityConfig = field(default_factory=FileSecurityConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    
    # Global security settings
    enable_https_only: bool = True
    enable_security_headers: bool = True
    enable_input_validation: bool = True
    enable_output_encoding: bool = True
    
    # Development vs Production
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    
    def __post_init__(self):
        """Post initialization validation and adjustment"""
        # Adjust settings based on environment
        if self.environment == "development":
            self.cors.validate_development()
            logger.warning("Running in development mode - some security restrictions relaxed")
        
        # Validate all configurations
        self.validate()
    
    def validate(self) -> bool:
        """Validate all security configurations"""
        is_valid = True
        
        if not self.authentication.validate():
            is_valid = False
            
        if self.environment == "production":
            if not self.enable_https_only:
                logger.error("HTTPS must be enabled in production")
                is_valid = False
                
            if "localhost" in str(self.cors.allowed_origins):
                logger.error("Localhost should not be allowed in production CORS")
                is_valid = False
        
        return is_valid
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers dictionary"""
        headers = {}
        
        if self.enable_security_headers:
            csp = self.content_security
            
            # Content Security Policy
            if csp.enabled:
                csp_directives = [
                    f"default-src {' '.join(csp.default_src)}",
                    f"script-src {' '.join(csp.script_src)}",
                    f"style-src {' '.join(csp.style_src)}",
                    f"img-src {' '.join(csp.img_src)}",
                    f"font-src {' '.join(csp.font_src)}",
                    f"connect-src {' '.join(csp.connect_src)}",
                    f"frame-src {' '.join(csp.frame_src)}",
                    f"object-src {' '.join(csp.object_src)}"
                ]
                headers["Content-Security-Policy"] = "; ".join(csp_directives)
            
            # Other security headers
            headers.update({
                "X-Frame-Options": csp.x_frame_options,
                "X-Content-Type-Options": csp.x_content_type_options,
                "X-XSS-Protection": csp.x_xss_protection,
                "Referrer-Policy": csp.referrer_policy,
            })
            
            # HSTS for HTTPS
            if self.enable_https_only:
                hsts_value = f"max-age={csp.hsts_max_age}"
                if csp.hsts_include_subdomains:
                    hsts_value += "; includeSubDomains"
                if csp.hsts_preload:
                    hsts_value += "; preload"
                headers["Strict-Transport-Security"] = hsts_value
        
        return headers


# Global configuration instance
_security_config: Optional[SecurityConfig] = None


def get_security_config() -> SecurityConfig:
    """Get or create global security configuration"""
    global _security_config
    
    if _security_config is None:
        _security_config = SecurityConfig()
        logger.info(f"Security configuration initialized for {_security_config.environment} environment")
    
    return _security_config


def update_security_config(config: SecurityConfig) -> None:
    """Update global security configuration"""
    global _security_config
    _security_config = config
    logger.info("Security configuration updated")


# Configuration validation on import
if __name__ != "__main__":
    config = get_security_config()
    if not config.validate():
        logger.error("Security configuration validation failed!")