"""
Secure Logging Framework
Provides secure logging with sensitive data protection and security event monitoring
"""

import os
import re
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
import hashlib

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SecurityEventType(Enum):
    """Security event types for categorization"""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    INPUT_VALIDATION_FAILURE = "input_validation_failure"
    FILE_UPLOAD_BLOCKED = "file_upload_blocked"
    INJECTION_ATTEMPT = "injection_attempt"
    ADMIN_ACTION = "admin_action"
    DATA_ACCESS = "data_access"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGE = "config_change"


class LogLevel(Enum):
    """Log levels with security considerations"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"


class SecureLogger:
    """Secure logging with sensitive data protection"""
    
    # Patterns for sensitive data detection
    SENSITIVE_PATTERNS = {
        'password': [
            r'password["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
            r'pwd["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
            r'pass["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
        ],
        'api_key': [
            r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
            r'apikey["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
            r'secret[_-]?key["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
        ],
        'token': [
            r'token["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
            r'access[_-]?token["\']?\s*[:=]\s*["\']?([^"\';\s,}]+)',
            r'bearer\s+([a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+)',
        ],
        'credit_card': [
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
        ],
        'ssn': [
            r'\b\d{3}-\d{2}-\d{4}\b',
            r'\b\d{9}\b',
        ],
        'email': [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        'ip_address': [
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        ],
        'phone': [
            r'\b\d{3}-\d{3}-\d{4}\b',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
        ],
    }
    
    def __init__(self, log_dir: str = "logs", environment: str = "development"):
        self.log_dir = Path(log_dir)
        self.environment = environment
        self.log_dir.mkdir(exist_ok=True)
        
        # Security log file
        self.security_log_file = self.log_dir / "security.log"
        self.audit_log_file = self.log_dir / "audit.log"
        self.access_log_file = self.log_dir / "access.log"
        
    def sanitize_log_data(self, data: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Sanitize log data to remove sensitive information"""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return self._sanitize_dict(data)
        else:
            return self._sanitize_string(str(data))
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string for logging"""
        sanitized = text
        
        # Replace sensitive patterns
        for category, patterns in self.SENSITIVE_PATTERNS.items():
            for pattern in patterns:
                # Create a hash of the sensitive data for tracking if needed
                def replace_func(match):
                    sensitive_value = match.group(1) if match.groups() else match.group(0)
                    # Create a short hash for reference
                    hash_value = hashlib.sha256(sensitive_value.encode()).hexdigest()[:8]
                    return f"[{category.upper()}_REDACTED_{hash_value}]"
                
                sanitized = re.sub(pattern, replace_func, sanitized, flags=re.IGNORECASE)
        
        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)
        
        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "...[TRUNCATED]"
        
        return sanitized
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary"""
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = self._sanitize_string(str(key))
            
            # Check if key suggests sensitive data
            sensitive_keys = ['password', 'token', 'secret', 'key', 'auth', 'credential']
            if any(sensitive in clean_key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and value:
                    hash_value = hashlib.sha256(str(value).encode()).hexdigest()[:8]
                    sanitized[clean_key] = f"[REDACTED_{hash_value}]"
                else:
                    sanitized[clean_key] = "[REDACTED]"
            else:
                # Recursively sanitize value
                if isinstance(value, dict):
                    sanitized[clean_key] = self._sanitize_dict(value)
                elif isinstance(value, list):
                    sanitized[clean_key] = [
                        self._sanitize_dict(item) if isinstance(item, dict) 
                        else self._sanitize_string(str(item))
                        for item in value
                    ]
                else:
                    sanitized[clean_key] = self._sanitize_string(str(value))
        
        return sanitized
    
    def log_security_event(self, event_type: SecurityEventType, details: Dict[str, Any], 
                          level: LogLevel = LogLevel.WARNING, user_id: Optional[str] = None,
                          ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Log security event with structured data"""
        
        # Create security event record
        event_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "level": level.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": self._sanitize_string(user_agent) if user_agent else None,
            "details": self.sanitize_log_data(details),
            "environment": self.environment,
            "event_id": self._generate_event_id()
        }
        
        # Log to security file
        self._write_to_file(self.security_log_file, event_record)
        
        # Also log to main logger based on level
        log_message = f"Security Event [{event_type.value}]: {json.dumps(event_record, default=str)}"
        
        if level == LogLevel.CRITICAL:
            logger.critical(log_message)
        elif level == LogLevel.ERROR:
            logger.error(log_message)
        elif level == LogLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def log_audit_event(self, action: str, resource: str, user_id: str, 
                       details: Dict[str, Any], success: bool = True):
        """Log audit event for compliance"""
        
        audit_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "resource": resource,
            "user_id": user_id,
            "success": success,
            "details": self.sanitize_log_data(details),
            "environment": self.environment,
            "audit_id": self._generate_event_id()
        }
        
        # Log to audit file
        self._write_to_file(self.audit_log_file, audit_record)
        
        # Log to main logger
        logger.info(f"Audit Event: {json.dumps(audit_record, default=str)}")
    
    def log_access_event(self, method: str, path: str, status_code: int,
                        user_id: Optional[str] = None, ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None, response_time: Optional[float] = None):
        """Log access event"""
        
        access_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": self._sanitize_string(user_agent) if user_agent else None,
            "response_time": response_time,
            "environment": self.environment
        }
        
        # Log to access file
        self._write_to_file(self.access_log_file, access_record)
    
    def _write_to_file(self, file_path: Path, record: Dict[str, Any]):
        """Write record to log file"""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, default=str) + '\n')
        except Exception as e:
            # Fallback to main logger if file logging fails
            logger.error(f"Failed to write to log file {file_path}: {str(e)}")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = str(int(time.time() * 1000000))
        return f"evt_{timestamp}"


class SecurityEventMonitor:
    """Monitor security events and trigger alerts"""
    
    def __init__(self, secure_logger: SecureLogger):
        self.logger = secure_logger
        self.event_counts = {}
        self.alert_thresholds = {
            SecurityEventType.AUTHENTICATION_FAILURE: {'count': 5, 'window': 300},  # 5 failures in 5 minutes
            SecurityEventType.RATE_LIMIT_EXCEEDED: {'count': 10, 'window': 600},    # 10 rate limits in 10 minutes
            SecurityEventType.INJECTION_ATTEMPT: {'count': 3, 'window': 300},       # 3 injection attempts in 5 minutes
            SecurityEventType.SUSPICIOUS_ACTIVITY: {'count': 5, 'window': 600},     # 5 suspicious activities in 10 minutes
        }
    
    def process_security_event(self, event_type: SecurityEventType, details: Dict[str, Any],
                             user_id: Optional[str] = None, ip_address: Optional[str] = None):
        """Process security event and check for alert conditions"""
        
        # Log the event
        self.logger.log_security_event(event_type, details, user_id=user_id, ip_address=ip_address)
        
        # Check for alert conditions
        self._check_alert_thresholds(event_type, ip_address or user_id or "unknown")
    
    def _check_alert_thresholds(self, event_type: SecurityEventType, identifier: str):
        """Check if event threshold is exceeded"""
        if event_type not in self.alert_thresholds:
            return
        
        current_time = time.time()
        threshold = self.alert_thresholds[event_type]
        
        # Initialize tracking if needed
        if event_type not in self.event_counts:
            self.event_counts[event_type] = {}
        
        if identifier not in self.event_counts[event_type]:
            self.event_counts[event_type][identifier] = []
        
        # Add current event
        self.event_counts[event_type][identifier].append(current_time)
        
        # Clean old events outside the time window
        window_start = current_time - threshold['window']
        self.event_counts[event_type][identifier] = [
            event_time for event_time in self.event_counts[event_type][identifier]
            if event_time >= window_start
        ]
        
        # Check if threshold exceeded
        event_count = len(self.event_counts[event_type][identifier])
        if event_count >= threshold['count']:
            self._trigger_alert(event_type, identifier, event_count, threshold)
    
    def _trigger_alert(self, event_type: SecurityEventType, identifier: str, 
                      count: int, threshold: Dict[str, int]):
        """Trigger security alert"""
        alert_details = {
            "alert_type": "threshold_exceeded",
            "event_type": event_type.value,
            "identifier": identifier,
            "count": count,
            "threshold": threshold,
            "severity": "HIGH"
        }
        
        self.logger.log_security_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            alert_details,
            LogLevel.CRITICAL
        )
        
        # In production, this could also:
        # - Send notifications to security team
        # - Trigger automated responses (like IP blocking)
        # - Update security dashboards
        logger.critical(f"SECURITY ALERT: {event_type.value} threshold exceeded for {identifier}")


# Authentication and authorization logging
class AuthLogger:
    """Specialized logger for authentication and authorization events"""
    
    def __init__(self, secure_logger: SecureLogger):
        self.secure_logger = secure_logger
    
    def log_login_attempt(self, username: str, success: bool, ip_address: str, 
                         user_agent: str, failure_reason: Optional[str] = None):
        """Log login attempt"""
        details = {
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "failure_reason": failure_reason
        }
        
        event_type = SecurityEventType.AUTHENTICATION_SUCCESS if success else SecurityEventType.AUTHENTICATION_FAILURE
        level = LogLevel.INFO if success else LogLevel.WARNING
        
        self.secure_logger.log_security_event(event_type, details, level, ip_address=ip_address, user_agent=user_agent)
    
    def log_logout(self, user_id: str, ip_address: str):
        """Log logout event"""
        details = {
            "action": "logout",
            "user_id": user_id,
            "ip_address": ip_address
        }
        
        self.secure_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_SUCCESS, 
            details, 
            LogLevel.INFO,
            user_id=user_id,
            ip_address=ip_address
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, 
                                ip_address: str, reason: str):
        """Log authorization failure"""
        details = {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "reason": reason,
            "ip_address": ip_address
        }
        
        self.secure_logger.log_security_event(
            SecurityEventType.AUTHORIZATION_FAILURE,
            details,
            LogLevel.WARNING,
            user_id=user_id,
            ip_address=ip_address
        )


# Global instances
_secure_logger = None
_security_monitor = None
_auth_logger = None

def get_secure_logger(environment: str = None) -> SecureLogger:
    """Get global secure logger instance"""
    global _secure_logger
    if _secure_logger is None:
        env = environment or os.getenv("ENVIRONMENT", "development")
        _secure_logger = SecureLogger(environment=env)
    return _secure_logger

def get_security_monitor() -> SecurityEventMonitor:
    """Get global security monitor instance"""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityEventMonitor(get_secure_logger())
    return _security_monitor

def get_auth_logger() -> AuthLogger:
    """Get global auth logger instance"""
    global _auth_logger
    if _auth_logger is None:
        _auth_logger = AuthLogger(get_secure_logger())
    return _auth_logger