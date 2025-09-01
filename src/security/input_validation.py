"""
Input Validation and Sanitization Framework
Comprehensive input validation for all user inputs to prevent injection attacks
"""

import re
import html
import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import unicodedata
from urllib.parse import unquote

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class InputSanitizer:
    """Comprehensive input sanitization utilities"""
    
    # Common injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(or|and)\s+\w+\s*=\s*\w+)",
        r"(\'\s*(or|and)\s*\'\w*\'\s*=\s*\'\w*\')",
        r"(\bunion\s+select\b)",
        r"(\binto\s+outfile\b)",
        r"(\bload_file\s*\()",
    ]
    
    XSS_PATTERNS = [
        r"(<script[^>]*>.*?</script>)",
        r"(javascript:)",
        r"(vbscript:)",
        r"(on\w+\s*=)",
        r"(<iframe[^>]*>.*?</iframe>)",
        r"(<object[^>]*>.*?</object>)",
        r"(<embed[^>]*>.*?</embed>)",
        r"(expression\s*\()",
        r"(@import)",
        r"(data:text/html)",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\.[\\/])",
        r"([\\/]\.\.)",
        r"(\.\.%2f)",
        r"(%2e%2e%2f)",
        r"(\.\.%5c)",
        r"(%2e%2e%5c)",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"(\||&&|\|\||;|`|\$\(|\${)",
        r"(\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ping|wget|curl|nc|nmap)\b)",
        r"(/bin/|/usr/bin/|/sbin/|cmd\.exe|powershell)",
        r"(>|<|>>|2>&1)",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """Sanitize a string input"""
        if not isinstance(value, str):
            value = str(value)
        
        # Normalize unicode
        value = unicodedata.normalize('NFKC', value)
        
        # URL decode
        value = unquote(value)
        
        # Remove null bytes and control characters (except tab, newline, carriage return)
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        # HTML encode if HTML not allowed
        if not allow_html:
            value = html.escape(value, quote=True)
        
        return value
    
    @classmethod
    def validate_no_injection(cls, value: str) -> tuple[bool, List[str]]:
        """Check for injection attack patterns"""
        if not isinstance(value, str):
            value = str(value)
        
        value_lower = value.lower()
        violations = []
        
        # Check SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                violations.append(f"SQL injection pattern detected: {pattern}")
        
        # Check XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                violations.append(f"XSS pattern detected: {pattern}")
        
        # Check path traversal
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                violations.append(f"Path traversal pattern detected: {pattern}")
        
        # Check command injection
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                violations.append(f"Command injection pattern detected: {pattern}")
        
        return len(violations) == 0, violations
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not isinstance(filename, str):
            filename = str(filename)
        
        # Remove directory traversal patterns
        filename = re.sub(r'[\\\/]', '', filename)
        filename = re.sub(r'\.\.+', '', filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Limit length and ensure not empty
        filename = filename.strip()[:255]
        if not filename:
            filename = "sanitized_file"
        
        # Ensure doesn't start with dot (hidden file)
        if filename.startswith('.'):
            filename = 'file_' + filename[1:]
        
        return filename
    
    @classmethod
    def sanitize_json(cls, data: Any, max_depth: int = 10, max_items: int = 1000) -> Any:
        """Recursively sanitize JSON data"""
        if max_depth <= 0:
            logger.warning("Maximum JSON depth reached during sanitization")
            return None
        
        if isinstance(data, dict):
            if len(data) > max_items:
                logger.warning(f"JSON object truncated to {max_items} items")
                data = dict(list(data.items())[:max_items])
            
            sanitized = {}
            for key, value in data.items():
                # Sanitize key
                clean_key = cls.sanitize_string(str(key), max_length=100)
                # Recursively sanitize value
                clean_value = cls.sanitize_json(value, max_depth - 1, max_items)
                sanitized[clean_key] = clean_value
            return sanitized
        
        elif isinstance(data, list):
            if len(data) > max_items:
                logger.warning(f"JSON array truncated to {max_items} items")
                data = data[:max_items]
            
            return [cls.sanitize_json(item, max_depth - 1, max_items) for item in data]
        
        elif isinstance(data, str):
            return cls.sanitize_string(data, max_length=10000)
        
        elif isinstance(data, (int, float, bool, type(None))):
            return data
        
        else:
            # Convert unknown types to string and sanitize
            return cls.sanitize_string(str(data), max_length=1000)


class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not isinstance(email, str) or len(email) > 254:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str, min_length: int = 12) -> tuple[bool, List[str]]:
        """Validate password strength"""
        if not isinstance(password, str):
            return False, ["Password must be a string"]
        
        issues = []
        
        if len(password) < min_length:
            issues.append(f"Password must be at least {min_length} characters long")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):
            issues.append("Password should not contain repeated characters")
        
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome']
        if password.lower() in common_passwords:
            issues.append("Password is too common")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Validate file extension"""
        if not isinstance(filename, str):
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def validate_mime_type(mime_type: str, allowed_types: List[str]) -> bool:
        """Validate MIME type"""
        if not isinstance(mime_type, str):
            return False
        
        return mime_type.lower() in [t.lower() for t in allowed_types]
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        if not isinstance(ip, str):
            return False
        
        # IPv4 pattern
        ipv4_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        
        # IPv6 pattern (simplified)
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        
        return bool(re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        if not isinstance(url, str) or len(url) > 2048:
            return False
        
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], required_fields: List[str], 
                           optional_fields: List[str] = None) -> tuple[bool, List[str]]:
        """Validate JSON data against schema"""
        if optional_fields is None:
            optional_fields = []
        
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check for unknown fields
        allowed_fields = set(required_fields + optional_fields)
        for field in data.keys():
            if field not in allowed_fields:
                errors.append(f"Unknown field: {field}")
        
        return len(errors) == 0, errors


class SecurityInputProcessor:
    """Main processor for secure input handling"""
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.validator = InputValidator()
    
    def process_user_input(self, data: Dict[str, Any], schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user input with validation and sanitization"""
        try:
            # First validate if schema provided
            if schema:
                required_fields = schema.get('required', [])
                optional_fields = schema.get('optional', [])
                valid, errors = self.validator.validate_json_schema(data, required_fields, optional_fields)
                
                if not valid:
                    raise ValueError(f"Schema validation failed: {errors}")
            
            # Sanitize the data
            sanitized_data = self.sanitizer.sanitize_json(data)
            
            # Validate for injection attacks
            for key, value in sanitized_data.items():
                if isinstance(value, str):
                    safe, violations = self.sanitizer.validate_no_injection(value)
                    if not safe:
                        logger.warning(f"Injection patterns detected in field '{key}': {violations}")
                        raise ValueError(f"Invalid input detected in field '{key}'")
            
            return sanitized_data
            
        except Exception as e:
            logger.error(f"Input processing failed: {str(e)}")
            raise
    
    def process_file_upload(self, filename: str, content: bytes, allowed_extensions: List[str], 
                          allowed_mime_types: List[str], max_size: int) -> Dict[str, Any]:
        """Process file upload with security checks"""
        try:
            # Validate file size
            if len(content) > max_size:
                raise ValueError(f"File size {len(content)} exceeds maximum {max_size}")
            
            # Sanitize filename
            clean_filename = self.sanitizer.sanitize_filename(filename)
            
            # Validate file extension
            if not self.validator.validate_file_extension(clean_filename, allowed_extensions):
                raise ValueError(f"File extension not allowed: {Path(clean_filename).suffix}")
            
            # Basic content validation (check for null bytes, which shouldn't be in text files)
            if b'\x00' in content and clean_filename.endswith(('.txt', '.csv', '.json')):
                raise ValueError("File contains null bytes - potential binary file")
            
            # Check for suspicious file signatures
            if self._has_suspicious_signature(content):
                raise ValueError("File has suspicious signature")
            
            return {
                'original_filename': filename,
                'clean_filename': clean_filename,
                'size': len(content),
                'validated': True
            }
            
        except Exception as e:
            logger.error(f"File upload processing failed: {str(e)}")
            raise
    
    def _has_suspicious_signature(self, content: bytes) -> bool:
        """Check for suspicious file signatures"""
        if len(content) < 4:
            return False
        
        # Check for executable signatures
        suspicious_signatures = [
            b'\x4d\x5a',  # PE executable
            b'\x7f\x45\x4c\x46',  # ELF executable
            b'\xcf\xfa\xed\xfe',  # Mach-O executable
            b'\xfe\xed\xfa\xce',  # Mach-O executable (reverse)
            b'<?php',  # PHP script
            b'#!/bin/',  # Shell script
            b'#!/usr/bin/',  # Shell script
        ]
        
        file_start = content[:10]
        for signature in suspicious_signatures:
            if file_start.startswith(signature):
                return True
        
        return False
    
    def validate_api_request(self, request_data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """Validate API request based on endpoint"""
        # Define schemas for different endpoints
        schemas = {
            'upload': {
                'required': ['file'],
                'optional': ['metadata', 'tags']
            },
            'analyze': {
                'required': ['file_id', 'analysis_types'],
                'optional': ['parameters', 'format']
            },
            'insights': {
                'required': ['file_id'],
                'optional': ['focus_areas', 'depth']
            },
            'report': {
                'required': ['file_id', 'format'],
                'optional': ['include_charts', 'template']
            }
        }
        
        schema = schemas.get(endpoint)
        return self.process_user_input(request_data, schema)


# Global instance
_input_processor = None

def get_input_processor() -> SecurityInputProcessor:
    """Get global input processor instance"""
    global _input_processor
    if _input_processor is None:
        _input_processor = SecurityInputProcessor()
    return _input_processor