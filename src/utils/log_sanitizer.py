"""
Log sanitization utilities to prevent log injection attacks
"""

import re
import logging
from typing import Any, Union


class LogSanitizer:
    """Utility class for sanitizing log messages to prevent injection attacks"""
    
    # Characters that could be used for log injection
    DANGEROUS_CHARS = ['\n', '\r', '\t', '\x00', '\x08', '\x0b', '\x0c']
    
    # Pattern to match ANSI escape sequences
    ANSI_ESCAPE_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    @classmethod
    def sanitize_for_logging(cls, message: Union[str, Any]) -> str:
        """
        Sanitize a message for safe logging
        
        Args:
            message: The message to sanitize (will be converted to string)
            
        Returns:
            Sanitized string safe for logging
        """
        if message is None:
            return "None"
        
        # Convert to string
        str_message = str(message)
        
        # Remove dangerous characters
        for char in cls.DANGEROUS_CHARS:
            str_message = str_message.replace(char, ' ')
        
        # Remove ANSI escape sequences
        str_message = cls.ANSI_ESCAPE_PATTERN.sub('', str_message)
        
        # Limit length to prevent log flooding
        if len(str_message) > 1000:
            str_message = str_message[:997] + "..."
        
        # Replace multiple spaces with single space
        str_message = re.sub(r'\s+', ' ', str_message)
        
        return str_message.strip()
    
    @classmethod
    def sanitize_filename(cls, filename: Union[str, Any]) -> str:
        """
        Sanitize filename for logging
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            Sanitized filename safe for logging
        """
        if filename is None:
            return "unknown_file"
        
        str_filename = str(filename)
        
        # Remove path separators and dangerous characters
        str_filename = re.sub(r'[/\\:*?"<>|]', '_', str_filename)
        
        # Remove control characters
        str_filename = ''.join(c for c in str_filename if ord(c) >= 32 or c in ' \t')
        
        # Limit length
        if len(str_filename) > 255:
            str_filename = str_filename[:252] + "..."
        
        return str_filename.strip() or "sanitized_filename"
    
    @classmethod
    def create_safe_logger_extra(cls, **kwargs) -> dict:
        """
        Create a dictionary of extra fields for logging with sanitized values
        
        Args:
            **kwargs: Key-value pairs to include in log extra
            
        Returns:
            Dictionary with sanitized values
        """
        safe_extra = {}
        for key, value in kwargs.items():
            # Sanitize key
            safe_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
            # Sanitize value
            safe_value = cls.sanitize_for_logging(value)
            safe_extra[safe_key] = safe_value
        
        return safe_extra


# Convenience functions for common use cases
def safe_log_info(logger: logging.Logger, message: str, **kwargs):
    """Log info message with sanitized content"""
    sanitized_message = LogSanitizer.sanitize_for_logging(message)
    safe_extra = LogSanitizer.create_safe_logger_extra(**kwargs)
    logger.info(sanitized_message, extra=safe_extra)


def safe_log_error(logger: logging.Logger, message: str, **kwargs):
    """Log error message with sanitized content"""
    sanitized_message = LogSanitizer.sanitize_for_logging(message)
    safe_extra = LogSanitizer.create_safe_logger_extra(**kwargs)
    logger.error(sanitized_message, extra=safe_extra)


def safe_log_warning(logger: logging.Logger, message: str, **kwargs):
    """Log warning message with sanitized content"""
    sanitized_message = LogSanitizer.sanitize_for_logging(message)
    safe_extra = LogSanitizer.create_safe_logger_extra(**kwargs)
    logger.warning(sanitized_message, extra=safe_extra)