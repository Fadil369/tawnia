"""
Enhanced error handling utilities with security and performance improvements
"""

import logging
import traceback
import sys
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone
from functools import wraps
from .log_sanitizer import LogSanitizer, safe_log_error


class SecurityAwareErrorHandler:
    """Error handler that prevents information disclosure while maintaining debugging capability"""
    
    def __init__(self, logger: logging.Logger, debug_mode: bool = False):
        self.logger = logger
        self.debug_mode = debug_mode
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle errors securely without exposing sensitive information
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            Sanitized error response
        """
        error_id = self._generate_error_id()
        
        # Log full error details securely
        self._log_error_securely(error, error_id, context)
        
        # Return sanitized error response
        if self.debug_mode:
            return {
                "error_id": error_id,
                "error_type": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "error_id": error_id,
                "message": "An internal error occurred. Please contact support with the error ID.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _log_error_securely(self, error: Exception, error_id: str, context: Optional[Dict[str, Any]]):
        """Log error with sanitized context"""
        # Sanitize context data
        safe_context = {}
        if context:
            for key, value in context.items():
                safe_key = LogSanitizer.sanitize_for_logging(key)
                safe_value = LogSanitizer.sanitize_for_logging(value)
                safe_context[safe_key] = safe_value
        
        # Log with sanitized information
        safe_log_error(
            self.logger,
            f"Error {error_id}: {type(error).__name__}",
            error_message=LogSanitizer.sanitize_for_logging(str(error)),
            context=safe_context,
            traceback=traceback.format_exc() if self.debug_mode else None
        )


def secure_error_handler(logger: logging.Logger, debug_mode: bool = False):
    """
    Decorator for secure error handling
    
    Args:
        logger: Logger instance
        debug_mode: Whether to include debug information
    """
    handler = SecurityAwareErrorHandler(logger, debug_mode)
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_response = handler.handle_error(e, {
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                raise Exception(f"Internal error: {error_response['error_id']}")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = handler.handle_error(e, {
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                raise Exception(f"Internal error: {error_response['error_id']}")
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and 'async' in str(func.__code__.co_flags):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Monitor and optimize performance with security considerations"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = {}
    
    def track_performance(self, operation_name: str):
        """Decorator to track operation performance"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = datetime.now(timezone.utc)
                try:
                    result = await func(*args, **kwargs)
                    self._record_success(operation_name, start_time)
                    return result
                except Exception as e:
                    self._record_failure(operation_name, start_time, e)
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = datetime.now(timezone.utc)
                try:
                    result = func(*args, **kwargs)
                    self._record_success(operation_name, start_time)
                    return result
                except Exception as e:
                    self._record_failure(operation_name, start_time, e)
                    raise
            
            if hasattr(func, '__code__') and 'async' in str(func.__code__.co_flags):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _record_success(self, operation_name: str, start_time: datetime):
        """Record successful operation metrics"""
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0
            }
        
        metrics = self.metrics[operation_name]
        metrics['total_calls'] += 1
        metrics['successful_calls'] += 1
        metrics['total_duration'] += duration
        metrics['avg_duration'] = metrics['total_duration'] / metrics['total_calls']
        
        # Log slow operations
        if duration > 5.0:  # 5 seconds threshold
            safe_operation_name = LogSanitizer.sanitize_for_logging(operation_name)
            self.logger.warning(f"Slow operation detected: {safe_operation_name} took {duration:.2f}s")
    
    def _record_failure(self, operation_name: str, start_time: datetime, error: Exception):
        """Record failed operation metrics"""
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0
            }
        
        metrics = self.metrics[operation_name]
        metrics['total_calls'] += 1
        metrics['failed_calls'] += 1
        metrics['total_duration'] += duration
        metrics['avg_duration'] = metrics['total_duration'] / metrics['total_calls']
        
        # Log failure
        safe_operation_name = LogSanitizer.sanitize_for_logging(operation_name)
        safe_error = LogSanitizer.sanitize_for_logging(str(error))
        self.logger.error(f"Operation failed: {safe_operation_name} - {safe_error}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics.clear()


# Global instances for easy access
_error_handler = None
_performance_monitor = None


def get_error_handler(logger: logging.Logger, debug_mode: bool = False) -> SecurityAwareErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = SecurityAwareErrorHandler(logger, debug_mode)
    return _error_handler


def get_performance_monitor(logger: logging.Logger) -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(logger)
    return _performance_monitor