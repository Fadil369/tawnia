"""
Logging configuration for the application
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
import json
from datetime import datetime


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            if frame.f_back is None:
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logger(name: str, log_level: str = "INFO", log_file: Optional[str] = None) -> logger:
    """Setup and configure logger"""

    # Remove default handler
    logger.remove()

    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / "app.log"

    # Console handler with colors
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # File handler with rotation
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="100 MB",
        retention="10 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )

    # Error file handler
    error_log_file = Path(log_file).parent / "error.log"
    logger.add(
        error_log_file,
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        rotation="50 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )

    # JSON structured logging for production
    json_log_file = Path(log_file).parent / "app.json"
    logger.add(
        json_log_file,
        level="INFO",
        format=lambda record: json.dumps({
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "extra": record.get("extra", {})
        }) + "\n",
        rotation="100 MB",
        retention="30 days",
        compression="zip"
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Suppress some noisy loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger


def log_function_call(func_name: str, params: dict = None, execution_time: float = None):
    """Log function call details"""
    log_data = {
        "function": func_name,
        "timestamp": datetime.now().isoformat(),
    }

    if params:
        log_data["parameters"] = params

    if execution_time:
        log_data["execution_time_seconds"] = execution_time

    logger.info(f"Function call: {func_name}", extra=log_data)


def log_api_request(method: str, endpoint: str, status_code: int, response_time: float, user_id: str = None):
    """Log API request details"""
    log_data = {
        "type": "api_request",
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "response_time_ms": response_time * 1000,
        "timestamp": datetime.now().isoformat()
    }

    if user_id:
        log_data["user_id"] = user_id

    level = "ERROR" if status_code >= 400 else "INFO"
    logger.log(level, f"API {method} {endpoint} - {status_code} ({response_time:.3f}s)", extra=log_data)


def log_data_processing(file_id: str, operation: str, records_processed: int, success: bool, error_message: str = None):
    """Log data processing operations"""
    log_data = {
        "type": "data_processing",
        "file_id": file_id,
        "operation": operation,
        "records_processed": records_processed,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }

    if error_message:
        log_data["error_message"] = error_message

    level = "ERROR" if not success else "INFO"
    message = f"Data processing {operation} for {file_id}: {records_processed} records"
    if not success and error_message:
        message += f" - Error: {error_message}"

    logger.log(level, message, extra=log_data)


def log_analysis_operation(analysis_type: str, file_ids: list, duration: float, success: bool, error_message: str = None):
    """Log analysis operations"""
    log_data = {
        "type": "analysis_operation",
        "analysis_type": analysis_type,
        "file_ids": file_ids,
        "duration_seconds": duration,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }

    if error_message:
        log_data["error_message"] = error_message

    level = "ERROR" if not success else "INFO"
    message = f"Analysis {analysis_type} for {len(file_ids)} files completed in {duration:.2f}s"
    if not success and error_message:
        message += f" - Error: {error_message}"

    logger.log(level, message, extra=log_data)


def log_ai_operation(operation: str, model: str, tokens_used: int = None, success: bool = True, error_message: str = None):
    """Log AI operations"""
    log_data = {
        "type": "ai_operation",
        "operation": operation,
        "model": model,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }

    if tokens_used:
        log_data["tokens_used"] = tokens_used

    if error_message:
        log_data["error_message"] = error_message

    level = "ERROR" if not success else "INFO"
    message = f"AI operation {operation} using {model}"
    if tokens_used:
        message += f" - {tokens_used} tokens"
    if not success and error_message:
        message += f" - Error: {error_message}"

    logger.log(level, message, extra=log_data)


# Custom context manager for operation logging
class LoggedOperation:
    """Context manager for logging operations with timing"""

    def __init__(self, operation_name: str, **kwargs):
        self.operation_name = operation_name
        self.kwargs = kwargs
        self.start_time = None
        self.logger = logger

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}", extra={"operation": self.operation_name, **self.kwargs})
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        success = exc_type is None

        log_data = {
            "operation": self.operation_name,
            "duration_seconds": duration,
            "success": success,
            **self.kwargs
        }

        if exc_val:
            log_data["error"] = str(exc_val)
            log_data["error_type"] = exc_type.__name__ if exc_type else None

        level = "ERROR" if not success else "INFO"
        message = f"Operation {self.operation_name} completed in {duration:.2f}s"
        if not success:
            message += f" with error: {exc_val}"

        self.logger.log(level, message, extra=log_data)

        return False  # Don't suppress exceptions
