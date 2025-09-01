"""
Advanced security utilities for Tawnia Healthcare Analytics
"""

import hashlib
import hmac
import secrets
import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import magic
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SecurityError(Exception):
    """Security-related exception"""
    pass


class FileValidator:
    """Advanced file validation and security checks"""

    # Allowed MIME types for healthcare data files
    ALLOWED_MIME_TYPES = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'text/csv',  # .csv
        'application/json',  # .json
    }

    # Maximum file sizes by type (in bytes)
    MAX_FILE_SIZES = {
        '.xlsx': 100 * 1024 * 1024,  # 100MB
        '.xls': 50 * 1024 * 1024,    # 50MB
        '.csv': 20 * 1024 * 1024,    # 20MB
        '.json': 10 * 1024 * 1024,   # 10MB
    }

    # Dangerous patterns in filenames
    DANGEROUS_PATTERNS = [
        r'\.\./',  # Path traversal
        r'\.exe$',  # Executable files
        r'\.bat$',  # Batch files
        r'\.cmd$',  # Command files
        r'\.scr$',  # Screen saver files
        r'\.vbs$',  # VBScript files
        r'\.js$',   # JavaScript files
        r'\.jar$',  # Java archive files
    ]

    @classmethod
    def validate_file(cls, file_path: Path, content: bytes) -> Dict[str, Any]:
        """Comprehensive file validation"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {
                'size': len(content),
                'extension': file_path.suffix.lower(),
                'mime_type': None
            }
        }

        try:
            # Check file extension
            if not cls._validate_extension(file_path, validation_result):
                return validation_result

            # Check file size
            if not cls._validate_size(file_path, content, validation_result):
                return validation_result

            # Check MIME type
            if not cls._validate_mime_type(content, validation_result):
                return validation_result

            # Check filename for dangerous patterns
            if not cls._validate_filename(file_path, validation_result):
                return validation_result

            # Check file content for malicious patterns
            if not cls._validate_content(content, validation_result):
                return validation_result

            validation_result['is_valid'] = True
            # Sanitize filename for logging to prevent log injection
            safe_filename = cls._sanitize_for_logging(file_path.name)
            logger.info(f"File validation passed: {safe_filename}")

        except Exception as e:
            validation_result['errors'].append(f"Validation error: {str(e)}")
            # Sanitize filename for logging to prevent log injection
            safe_filename = cls._sanitize_for_logging(file_path.name)
            safe_error = cls._sanitize_for_logging(str(e))
            logger.error(f"File validation error for {safe_filename}: {safe_error}")

        return validation_result

    @classmethod
    def _validate_extension(cls, file_path: Path, result: Dict) -> bool:
        """Validate file extension"""
        extension = file_path.suffix.lower()
        allowed_extensions = list(cls.MAX_FILE_SIZES.keys())

        if extension not in allowed_extensions:
            result['errors'].append(f"File extension '{extension}' not allowed")
            return False

        return True

    @classmethod
    def _validate_size(cls, file_path: Path, content: bytes, result: Dict) -> bool:
        """Validate file size"""
        size = len(content)
        extension = file_path.suffix.lower()
        # Use 10MB default to align with smallest defined maximum
        max_size = cls.MAX_FILE_SIZES.get(extension, 10 * 1024 * 1024)

        if size > max_size:
            result['errors'].append(
                f"File size {size} bytes exceeds maximum {max_size} bytes for {extension}"
            )
            return False

        if size == 0:
            result['errors'].append("File is empty")
            return False

        return True

    @classmethod
    def _validate_mime_type(cls, content: bytes, result: Dict) -> bool:
        """Validate MIME type using python-magic"""
        try:
            mime_type = magic.from_buffer(content, mime=True)
            result['file_info']['mime_type'] = mime_type

            if mime_type not in cls.ALLOWED_MIME_TYPES:
                result['errors'].append(f"MIME type '{mime_type}' not allowed")
                return False

            return True

        except Exception as e:
            result['warnings'].append(f"Could not determine MIME type: {str(e)}")
            return True  # Allow if MIME detection fails

    @classmethod
    def _validate_filename(cls, file_path: Path, result: Dict) -> bool:
        """Validate filename for dangerous patterns"""
        filename = file_path.name

        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                result['errors'].append(f"Dangerous pattern detected in filename: {pattern}")
                return False

        # Check for null bytes and control characters
        if '\x00' in filename or any(ord(c) < 32 for c in filename if c not in '\t\n\r'):
            result['errors'].append("Invalid characters in filename")
            return False

        return True

    @classmethod
    def _validate_content(cls, content: bytes, result: Dict) -> bool:
        """Validate file content for malicious patterns"""
        # Check for embedded executables or scripts
        dangerous_signatures = [
            b'MZ',  # PE executable
            b'\x7fELF',  # ELF executable
            b'<script',  # JavaScript
            b'javascript:',  # JavaScript URL
            b'vbscript:',  # VBScript URL
        ]

        content_lower = content.lower()
        for signature in dangerous_signatures:
            if signature in content_lower:
                result['warnings'].append(f"Potentially dangerous content pattern detected")
                break

        return True

    @classmethod
    def _sanitize_for_logging(cls, text: str) -> str:
        """Sanitize text for safe logging to prevent log injection"""
        if not isinstance(text, str):
            text = str(text)
        # Remove newlines, carriage returns, and other control characters
        text = ''.join(c for c in text if ord(c) >= 32 or c in ' \t')
        # Limit length to prevent log flooding
        return text[:200] + '...' if len(text) > 200 else text


class InputSanitizer:
    """Input sanitization utilities"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks"""
        if not isinstance(filename, str):
            filename = str(filename)
        
        # Remove null bytes and control characters
        filename = ''.join(c for c in filename if ord(c) >= 32)
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\.\.+', '.', filename)
        filename = filename.strip('. ')
        
        # Prevent reserved names on Windows
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        name_part = filename.split('.')[0].upper()
        if name_part in reserved_names:
            filename = f"file_{filename}"
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_len = 255 - len(ext) - 1 if ext else 255
            filename = name[:max_name_len] + ('.' + ext if ext else '')
        
        # Ensure filename is not empty
        if not filename or filename == '.':
            filename = 'unnamed_file'

        return filename

    @staticmethod
    def sanitize_json_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize JSON input data"""
        if not isinstance(data, dict):
            raise SecurityError("Input must be a dictionary")

        sanitized = {}
        for key, value in data.items():
            # Sanitize keys
            clean_key = re.sub(r'[^\w\-_]', '', str(key))
            if not clean_key:
                continue

            # Sanitize values
            if isinstance(value, str):
                # Remove potentially dangerous characters
                clean_value = re.sub(r'[<>"\']', '', value)
                clean_value = clean_value.strip()
                sanitized[clean_key] = clean_value
            elif isinstance(value, (int, float, bool)):
                sanitized[clean_key] = value
            elif isinstance(value, list):
                sanitized[clean_key] = [
                    InputSanitizer.sanitize_string(str(item)) for item in value
                ]
            elif isinstance(value, dict):
                sanitized[clean_key] = InputSanitizer.sanitize_json_input(value)

        return sanitized

    @staticmethod
    def sanitize_string(text: str) -> str:
        """Sanitize string input"""
        if not isinstance(text, str):
            text = str(text)

        # Remove null bytes and control characters (except common whitespace)
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\t\n\r')

        # Remove potentially dangerous patterns
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)

        return text.strip()


class RateLimiter:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self):
        self.request_counts = {}  # IP -> {window_start: timestamp, count: int}
        self.blocked_ips = {}     # IP -> block_until_timestamp

    def is_allowed(
        self,
        client_ip: str,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        block_duration: int = 300  # 5 minutes
    ) -> bool:
        """Check if request is allowed based on rate limits"""
        current_time = datetime.now()

        # Check if IP is currently blocked
        if client_ip in self.blocked_ips:
            if current_time.timestamp() < self.blocked_ips[client_ip]:
                return False
            else:
                del self.blocked_ips[client_ip]

        # Initialize tracking for new IPs
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {
                'minute_window': current_time.replace(second=0, microsecond=0),
                'minute_count': 0,
                'hour_window': current_time.replace(minute=0, second=0, microsecond=0),
                'hour_count': 0
            }

        client_data = self.request_counts[client_ip]

        # Check minute window
        minute_window = current_time.replace(second=0, microsecond=0)
        if client_data['minute_window'] != minute_window:
            client_data['minute_window'] = minute_window
            client_data['minute_count'] = 0

        # Check hour window
        hour_window = current_time.replace(minute=0, second=0, microsecond=0)
        if client_data['hour_window'] != hour_window:
            client_data['hour_window'] = hour_window
            client_data['hour_count'] = 0

        # Check limits
        if (client_data['minute_count'] >= requests_per_minute or
            client_data['hour_count'] >= requests_per_hour):

            # Block IP for specified duration
            self.blocked_ips[client_ip] = (
                current_time + timedelta(seconds=block_duration)
            ).timestamp()

            # Sanitize IP for logging
            safe_ip = InputSanitizer.sanitize_string(client_ip)
            logger.warning(f"Rate limit exceeded for IP {safe_ip}")
            return False

        # Increment counters
        client_data['minute_count'] += 1
        client_data['hour_count'] += 1

        return True

    def cleanup_old_entries(self):
        """Clean up old tracking entries"""
        current_time = datetime.now()

        # Remove old blocked IPs
        expired_blocks = [
            ip for ip, block_until in self.blocked_ips.items()
            if current_time.timestamp() >= block_until
        ]
        for ip in expired_blocks:
            del self.blocked_ips[ip]

        # Remove old request counts (older than 1 hour)
        hour_ago = current_time - timedelta(hours=1)
        expired_requests = [
            ip for ip, data in self.request_counts.items()
            if data['hour_window'] < hour_ago.replace(minute=0, second=0, microsecond=0)
        ]
        for ip in expired_requests:
            del self.request_counts[ip]


class AuthenticationManager:
    """JWT-based authentication manager"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_blacklist = set()

    def create_access_token(
        self,
        user_id: str,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)

        expire = datetime.utcnow() + expires_delta
        payload = {
            "user_id": user_id,
            "permissions": permissions or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # JWT ID for blacklisting
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti in self.token_blacklist:
                raise SecurityError("Token has been revoked")

            return payload

        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.InvalidTokenError:
            raise SecurityError("Invalid token")

    def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding it to blacklist"""
        try:
            payload = jwt.decode(
                token, self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Allow expired tokens for revocation
            )
            jti = payload.get("jti")
            if jti:
                self.token_blacklist.add(jti)
                return True
        except Exception:
            pass
        return False


class SecurityMiddleware:
    """Security middleware for FastAPI"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.file_validator = FileValidator()
        self.input_sanitizer = InputSanitizer()

    async def validate_request(self, request: Request) -> bool:
        """Validate incoming request for security"""
        client_ip = request.client.host

        # Rate limiting
        if not self.rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Content-Type validation for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type and not any(
                allowed in content_type for allowed in [
                    "application/json",
                    "multipart/form-data",
                    "application/x-www-form-urlencoded"
                ]
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid content type"
                )

        return True


# Global instances
security_middleware = SecurityMiddleware()
file_validator = FileValidator()
input_sanitizer = InputSanitizer()
rate_limiter = RateLimiter()

# Default authentication manager (should be configured with proper secret)
auth_manager = AuthenticationManager(
    secret_key=secrets.token_urlsafe(32),  # Generate random secret in production
    algorithm="HS256"
)
