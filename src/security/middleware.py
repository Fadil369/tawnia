"""
Security Middleware for FastAPI
Provides comprehensive security features including rate limiting, authentication, and request validation
"""

import time
import json
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
import jwt
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import ipaddress

from src.utils.logger import setup_logger
from src.security.security_config import get_security_config

logger = setup_logger(__name__)


class RateLimiter:
    """Advanced rate limiter with multiple time windows"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        # Store request timestamps for each IP
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
        self.burst_counter: Dict[str, int] = defaultdict(int)
        self.burst_reset_time: Dict[str, float] = defaultdict(float)
    
    def is_allowed(self, identifier: str) -> tuple[bool, Optional[str]]:
        """Check if request is allowed under rate limits"""
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(identifier, current_time)
        
        # Check burst limit (requests in last 10 seconds)
        if current_time - self.burst_reset_time[identifier] > 10:
            self.burst_counter[identifier] = 0
            self.burst_reset_time[identifier] = current_time
        
        if self.burst_counter[identifier] >= self.burst_limit:
            return False, f"Burst limit exceeded: {self.burst_limit} requests per 10 seconds"
        
        # Check minute limit
        minute_count = sum(1 for timestamp in self.request_history[identifier] 
                          if current_time - timestamp <= 60)
        if minute_count >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check hour limit
        hour_count = sum(1 for timestamp in self.request_history[identifier] 
                        if current_time - timestamp <= 3600)
        if hour_count >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Record the request
        self.request_history[identifier].append(current_time)
        self.burst_counter[identifier] += 1
        
        return True, None
    
    def _cleanup_old_entries(self, identifier: str, current_time: float):
        """Remove entries older than 1 hour"""
        history = self.request_history[identifier]
        while history and current_time - history[0] > 3600:
            history.popleft()


class InputValidator:
    """Request input validation and sanitization"""
    
    @staticmethod
    def validate_content_length(request: Request, max_size_mb: int = 100) -> bool:
        """Validate request content length"""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size_bytes = int(content_length)
                max_bytes = max_size_mb * 1024 * 1024
                return size_bytes <= max_bytes
            except ValueError:
                return False
        return True
    
    @staticmethod
    def validate_content_type(request: Request, allowed_types: List[str] = None) -> bool:
        """Validate request content type"""
        if allowed_types is None:
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
                "text/plain"
            ]
        
        content_type = request.headers.get("content-type", "").split(";")[0].strip()
        return content_type in allowed_types or content_type.startswith("multipart/")
    
    @staticmethod
    def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize request headers"""
        sanitized = {}
        dangerous_headers = [
            "x-forwarded-host",
            "x-forwarded-proto",
            "x-real-ip"
        ]
        
        for key, value in headers.items():
            if key.lower() not in dangerous_headers:
                # Remove potentially dangerous characters
                sanitized_value = ''.join(c for c in value if ord(c) >= 32 and ord(c) < 127)[:1000]
                sanitized[key] = sanitized_value
        
        return sanitized


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, config=None):
        super().__init__(app)
        self.config = config or get_security_config()
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.config.rate_limit.requests_per_minute,
            requests_per_hour=self.config.rate_limit.requests_per_hour,
            burst_limit=self.config.rate_limit.burst_limit
        )
        self.validator = InputValidator()
        
        # Track failed requests for monitoring
        self.failed_requests: Dict[str, deque] = defaultdict(lambda: deque())
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware processing"""
        start_time = time.time()
        
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Security validations
            security_response = await self._perform_security_checks(request, client_ip)
            if security_response:
                return security_response
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            # Log successful request
            process_time = time.time() - start_time
            self._log_request(request, response, client_ip, process_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)[:200]}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    async def _perform_security_checks(self, request: Request, client_ip: str) -> Optional[Response]:
        """Perform all security checks"""
        
        # Check if IP is whitelisted
        if self._is_ip_whitelisted(client_ip):
            return None
        
        # Rate limiting
        allowed, rate_limit_msg = self.rate_limiter.is_allowed(client_ip)
        if not allowed:
            self._log_security_event("rate_limit_exceeded", client_ip, rate_limit_msg)
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "detail": rate_limit_msg},
                headers={"Retry-After": "60"}
            )
        
        # Content length validation
        if not self.validator.validate_content_length(
            request, self.config.network_security.max_request_size_mb
        ):
            self._log_security_event("content_length_exceeded", client_ip)
            return JSONResponse(
                status_code=413,
                content={"error": "Request entity too large"}
            )
        
        # Content type validation for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            if not self.validator.validate_content_type(request):
                self._log_security_event("invalid_content_type", client_ip)
                return JSONResponse(
                    status_code=415,
                    content={"error": "Unsupported media type"}
                )
        
        # Check for suspicious patterns
        if self._detect_suspicious_patterns(request, client_ip):
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden - suspicious activity detected"}
            )
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP address"""
        # Check for forwarded headers (but validate against trusted proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Get first IP from the chain
            ip = forwarded_for.split(",")[0].strip()
            # Validate it's from a trusted proxy
            if self._is_trusted_proxy(request.client.host):
                try:
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    pass
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip and self._is_trusted_proxy(request.client.host):
            try:
                ipaddress.ip_address(real_ip)
                return real_ip
            except ValueError:
                pass
        
        return request.client.host
    
    def _is_trusted_proxy(self, ip: str) -> bool:
        """Check if IP is a trusted proxy"""
        try:
            client_ip = ipaddress.ip_address(ip)
            for trusted in self.config.network_security.trusted_proxies:
                if client_ip == ipaddress.ip_address(trusted):
                    return True
        except ValueError:
            pass
        return False
    
    def _is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        if not self.config.rate_limit.enable_ip_whitelist:
            return False
        
        try:
            client_ip = ipaddress.ip_address(ip)
            for whitelisted in self.config.rate_limit.ip_whitelist:
                if client_ip == ipaddress.ip_address(whitelisted):
                    return True
        except ValueError:
            pass
        return False
    
    def _detect_suspicious_patterns(self, request: Request, client_ip: str) -> bool:
        """Detect suspicious request patterns"""
        
        # Check for common attack patterns in URL
        suspicious_patterns = [
            "../", "..\\", "etc/passwd", "boot.ini", "win.ini",
            "<script", "javascript:", "vbscript:", "onload=", "onerror=",
            "union select", "drop table", "insert into", "delete from",
            "exec(", "system(", "cmd.exe", "/bin/sh", "base64",
            "eval(", "setTimeout(", "setInterval("
        ]
        
        url_path = str(request.url.path).lower()
        query_string = str(request.url.query).lower()
        
        for pattern in suspicious_patterns:
            if pattern in url_path or pattern in query_string:
                self._log_security_event("suspicious_pattern", client_ip, f"Pattern: {pattern}")
                return True
        
        # Check user agent for suspicious patterns
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = [
            "sqlmap", "nmap", "nikto", "masscan", "zap", "burp",
            "crawler", "spider", "bot", "scanner"
        ]
        
        for agent in suspicious_agents:
            if agent in user_agent:
                self._log_security_event("suspicious_user_agent", client_ip, f"Agent: {agent}")
                return True
        
        # Check for too many failed requests from this IP
        current_time = time.time()
        failed_history = self.failed_requests[client_ip]
        
        # Clean old entries (last 10 minutes)
        while failed_history and current_time - failed_history[0] > 600:
            failed_history.popleft()
        
        if len(failed_history) > 10:  # More than 10 failed requests in 10 minutes
            self._log_security_event("too_many_failures", client_ip)
            return True
        
        return False
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        headers = self.config.get_security_headers_dict()
        
        for header, value in headers.items():
            response.headers[header] = value
        
        # Add additional security headers
        response.headers["X-Request-ID"] = f"req_{int(time.time() * 1000)}"
        response.headers["Server"] = "Tawnia-Healthcare-Analytics"
    
    def _log_request(self, request: Request, response: Response, client_ip: str, process_time: float):
        """Log request details"""
        log_data = {
            "client_ip": client_ip,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
            "user_agent": request.headers.get("user-agent", "")[:100],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if response.status_code >= 400:
            self.failed_requests[client_ip].append(time.time())
            logger.warning(f"Failed request: {json.dumps(log_data)}")
        elif process_time > 5.0:  # Slow request
            logger.warning(f"Slow request: {json.dumps(log_data)}")
        else:
            logger.info(f"Request: {client_ip} {request.method} {request.url.path} -> {response.status_code}")
    
    def _log_security_event(self, event_type: str, client_ip: str, details: str = ""):
        """Log security events"""
        log_data = {
            "event_type": event_type,
            "client_ip": client_ip,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.warning(f"Security event: {json.dumps(log_data)}")


class JWTAuthenticationMiddleware:
    """JWT authentication middleware for protected routes"""
    
    def __init__(self, config=None):
        self.config = config or get_security_config()
        self.auth_config = self.config.authentication
        self.security = HTTPBearer(auto_error=False)
    
    async def authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate request using JWT token"""
        
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            return None
        
        # Get token from header
        credentials: HTTPAuthorizationCredentials = await self.security(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Decode and validate token
            payload = jwt.decode(
                credentials.credentials,
                self.auth_config.jwt_secret_key,
                algorithms=[self.auth_config.jwt_algorithm]
            )
            
            # Check token expiration
            if "exp" in payload:
                if datetime.utcnow().timestamp() > payload["exp"]:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired"
                    )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError as e:
            logger.warning(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (doesn't require authentication)"""
        public_endpoints = [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/auth/login",
            "/auth/register",
            "/static",
            "/"
        ]
        
        return any(path.startswith(endpoint) for endpoint in public_endpoints)


def create_security_middleware(app, environment: str = None):
    """Factory function to create security middleware"""
    config = get_security_config(environment)
    return SecurityMiddleware(app, config)