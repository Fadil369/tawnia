"""
Enhanced configuration management for Tawnia Healthcare Analytics
"""

import os
import secrets
import sys
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, validator, SecretStr
import json


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: Optional[str] = Field(default=None, env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")


class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: Optional[str] = Field(default=None, env="REDIS_URL")
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[SecretStr] = Field(default=None, env="REDIS_PASSWORD")
    ssl: bool = Field(default=False, env="REDIS_SSL")
    timeout: int = Field(default=5, env="REDIS_TIMEOUT")
    max_connections: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")


class OpenAISettings(BaseSettings):
    """OpenAI API configuration"""
    api_key: Optional[SecretStr] = Field(default=None, env="OPENAI_API_KEY")
    model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    top_p: float = Field(default=1.0, env="OPENAI_TOP_P")
    frequency_penalty: float = Field(default=0.0, env="OPENAI_FREQUENCY_PENALTY")
    presence_penalty: float = Field(default=0.0, env="OPENAI_PRESENCE_PENALTY")
    timeout: int = Field(default=30, env="OPENAI_TIMEOUT")
    max_retries: int = Field(default=3, env="OPENAI_MAX_RETRIES")

    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v

    @validator('top_p')
    def validate_top_p(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('top_p must be between 0 and 1')
        return v


class SecuritySettings(BaseSettings):
    """Security configuration"""
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_hours: int = Field(default=24, env="JWT_EXPIRE_HOURS")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    max_login_attempts: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    login_attempt_window: int = Field(default=900, env="LOGIN_ATTEMPT_WINDOW")  # 15 minutes
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # 1 minute
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    @validator('allowed_origins', pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @validator('allowed_hosts', pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v


class FileProcessingSettings(BaseSettings):
    """File processing configuration"""
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    chunk_size: int = Field(default=8192, env="CHUNK_SIZE")
    upload_directory: str = Field(default="uploads", env="UPLOAD_DIRECTORY")
    reports_directory: str = Field(default="reports", env="REPORTS_DIRECTORY")
    temp_directory: str = Field(default="temp", env="TEMP_DIRECTORY")
    backup_directory: str = Field(default="backups", env="BACKUP_DIRECTORY")
    allowed_extensions: List[str] = Field(
        default=[".xlsx", ".xls", ".csv", ".json"],
        env="ALLOWED_EXTENSIONS"
    )
    max_concurrent_uploads: int = Field(default=5, env="MAX_CONCURRENT_UPLOADS")
    file_retention_days: int = Field(default=30, env="FILE_RETENTION_DAYS")

    @validator('allowed_extensions', pre=True)
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    file: Optional[str] = Field(default=None, env="LOG_FILE")
    max_size: str = Field(default="10MB", env="LOG_MAX_SIZE")
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        env="LOG_FORMAT"
    )
    json_logs: bool = Field(default=False, env="LOG_JSON")

    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class CacheSettings(BaseSettings):
    """Caching configuration"""
    ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    cleanup_interval: int = Field(default=300, env="CACHE_CLEANUP_INTERVAL")  # 5 minutes
    compression: bool = Field(default=True, env="CACHE_COMPRESSION")
    serializer: str = Field(default="pickle", env="CACHE_SERIALIZER")  # pickle, json, msgpack

    @validator('serializer')
    def validate_serializer(cls, v):
        valid_serializers = ['pickle', 'json', 'msgpack']
        if v not in valid_serializers:
            raise ValueError(f'Serializer must be one of: {valid_serializers}')
        return v


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration"""
    enabled: bool = Field(default=True, env="MONITORING_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    performance_sampling_rate: float = Field(default=0.1, env="PERFORMANCE_SAMPLING_RATE")
    retain_metrics_days: int = Field(default=7, env="RETAIN_METRICS_DAYS")
    alert_email: Optional[str] = Field(default=None, env="ALERT_EMAIL")
    alert_webhook: Optional[str] = Field(default=None, env="ALERT_WEBHOOK")

    @validator('performance_sampling_rate')
    def validate_sampling_rate(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Performance sampling rate must be between 0 and 1')
        return v


class CloudflareSettings(BaseSettings):
    """Cloudflare deployment configuration"""
    account_id: Optional[str] = Field(default=None, env="CLOUDFLARE_ACCOUNT_ID")
    api_token: Optional[SecretStr] = Field(default=None, env="CLOUDFLARE_API_TOKEN")
    zone_id: Optional[str] = Field(default=None, env="CLOUDFLARE_ZONE_ID")
    worker_name: str = Field(default="tawnia-analytics", env="CLOUDFLARE_WORKER_NAME")
    pages_project: str = Field(default="tawnia-frontend", env="CLOUDFLARE_PAGES_PROJECT")
    environment: str = Field(default="production", env="CLOUDFLARE_ENVIRONMENT")


class Settings(BaseSettings):
    """Main configuration class"""

    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")
    workers: int = Field(default=1, env="WORKERS")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    openai: OpenAISettings = OpenAISettings()
    security: SecuritySettings = SecuritySettings()
    file_processing: FileProcessingSettings = FileProcessingSettings()
    logging: LoggingSettings = LoggingSettings()
    cache: CacheSettings = CacheSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    cloudflare: CloudflareSettings = CloudflareSettings()

    # Feature flags
    enable_ai_insights: bool = Field(default=True, env="ENABLE_AI_INSIGHTS")
    enable_advanced_analytics: bool = Field(default=True, env="ENABLE_ADVANCED_ANALYTICS")
    enable_real_time_processing: bool = Field(default=False, env="ENABLE_REAL_TIME_PROCESSING")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    enable_circuit_breaker: bool = Field(default=True, env="ENABLE_CIRCUIT_BREAKER")

    # Legacy fields for backward compatibility
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    max_files: int = Field(default=10, env="MAX_FILES")
    allowed_extensions: List[str] = Field(default=[".xlsx", ".xls", ".csv"], env="ALLOWED_EXTENSIONS")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=900, env="RATE_LIMIT_WINDOW")  # 15 minutes
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    reports_dir: str = Field(default="reports", env="REPORTS_DIR")
    data_dir: str = Field(default="data", env="DATA_DIR")
    logs_dir: str = Field(default="logs", env="LOGS_DIR")
    analysis_timeout: int = Field(default=300, env="ANALYSIS_TIMEOUT")  # 5 minutes
    batch_size: int = Field(default=1000, env="BATCH_SIZE")
    ai_fallback_enabled: bool = Field(default=True, env="AI_FALLBACK_ENABLED")
    ai_confidence_threshold: float = Field(default=0.7, env="AI_CONFIDENCE_THRESHOLD")
    default_report_format: str = Field(default="pdf", env="DEFAULT_REPORT_FORMAT")
    include_charts_default: bool = Field(default=True, env="INCLUDE_CHARTS_DEFAULT")

    # System information
    python_version: str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # Class-level constants for better performance
    VALID_ENVIRONMENTS = ['development', 'testing', 'staging', 'production']
    
    @validator('environment')
    def validate_environment(cls, v):
        if v not in cls.VALID_ENVIRONMENTS:
            raise ValueError(f'Environment must be one of: {cls.VALID_ENVIRONMENTS}')
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

    def get_database_url(self) -> Optional[str]:
        """Get database URL with fallback"""
        return self.database.url

    def get_redis_url(self) -> str:
        """Get Redis URL"""
        if self.redis.url:
            return self.redis.url

        auth = ""
        if self.redis.password:
            auth = f":{self.redis.password.get_secret_value()}@"

        protocol = "rediss" if self.redis.ssl else "redis"
        return f"{protocol}://{auth}{self.redis.host}:{self.redis.port}/{self.redis.db}"

    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return self.openai.api_key.get_secret_value() if self.openai.api_key else None

    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.file_processing.upload_directory,
            self.file_processing.reports_directory,
            self.file_processing.temp_directory,
            self.file_processing.backup_directory,
            self.upload_dir,
            self.reports_dir,
            self.data_dir,
            self.logs_dir,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding secrets)"""
        data = self.dict()

        # Remove sensitive information and sanitize output
        def sanitize_value(value):
            if isinstance(value, str):
                # Basic HTML escaping to prevent XSS
                return value.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
            return value

        # Recursively sanitize all string values
        def sanitize_dict(d):
            if isinstance(d, dict):
                return {k: sanitize_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            else:
                return sanitize_value(d)

        data = sanitize_dict(data)

        # Remove sensitive information
        if 'openai' in data and 'api_key' in data['openai']:
            data['openai']['api_key'] = "***" if data['openai']['api_key'] else None

        if 'redis' in data and 'password' in data['redis']:
            data['redis']['password'] = "***" if data['redis']['password'] else None

        if 'cloudflare' in data and 'api_token' in data['cloudflare']:
            data['cloudflare']['api_token'] = "***" if data['cloudflare']['api_token'] else None

        return data

    def save_to_file(self, file_path: Union[str, Path]):
        """Save configuration to file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"  # For nested settings like DATABASE__URL


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.ensure_directories()
    return settings


# Global settings instance for backward compatibility
settings = get_settings()
