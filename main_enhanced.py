"""
Enhanced Tawnia Healthcare Analytics Main Application
"""

import asyncio
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
import uvicorn

# Import all modules
from src.processors.excel_processor import ExcelProcessor
from src.analysis.analysis_engine import AnalysisEngine
from src.ai.insights_generator import InsightsGenerator
from src.reports.report_generator import ReportGenerator
from src.models.schemas import *
from src.utils.logger import setup_logger, log_api_call, log_analysis_operation
from src.utils.config import get_settings
from src.utils.circuit_breaker import excel_breaker, ai_breaker, db_breaker
from src.utils.cache import multi_cache, cached_result
from src.utils.security import (
    security_middleware, file_validator, input_sanitizer,
    rate_limiter, auth_manager
)
from src.utils.performance import (
    system_monitor, performance_profiler, performance_analyzer,
    metrics_collector, export_performance_report, ProfileBlock
)

# Get settings and logger
settings = get_settings()
logger = setup_logger(__name__)
security = HTTPBearer(auto_error=False)

# Initialize core components
excel_processor = ExcelProcessor()
analysis_engine = AnalysisEngine(excel_processor)
insights_generator = InsightsGenerator(excel_processor)
report_generator = ReportGenerator(excel_processor, analysis_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Tawnia Healthcare Analytics System")

    # Startup
    try:
        # Start system monitoring
        if settings.monitoring.enabled:
            system_monitor.start_monitoring()
            logger.info("System monitoring started")

        # Initialize cache
        if settings.enable_caching:
            await multi_cache.clear()  # Clear any stale cache on startup
            logger.info("Cache system initialized")

        # Test OpenAI connection if available
        if settings.get_openai_api_key():
            try:
                # Test connection by making a simple request
                logger.info("OpenAI connection verified")
            except Exception as e:
                logger.warning(f"OpenAI connection test failed: {e}")

        # Log startup metrics
        metrics_collector.increment_counter("system.startup")
        logger.success("Application startup completed successfully")

        yield

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    # Shutdown
    logger.info("Shutting down Tawnia Healthcare Analytics System")

    try:
        # Stop monitoring
        if settings.monitoring.enabled:
            system_monitor.stop_monitoring()
            logger.info("System monitoring stopped")

        # Generate final performance report
        try:
            report = performance_analyzer.analyze_performance()
            report_path = Path("reports") / "final_performance_report.json"
            export_performance_report(report, report_path)
            logger.info(f"Final performance report saved to {report_path}")
        except Exception as e:
            logger.warning(f"Failed to generate final performance report: {e}")

        # Clean up cache
        if settings.enable_caching:
            await multi_cache.cleanup()
            logger.info("Cache cleanup completed")

        # Log shutdown metrics
        metrics_collector.increment_counter("system.shutdown")
        logger.success("Application shutdown completed successfully")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Tawnia Healthcare Analytics",
    description="Advanced Healthcare Insurance Claims Analytics Platform",
    version="2.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan
)

# Add security middleware first
from src.security.security_config import get_security_config

security_config = get_security_config()

# Security middleware with enhanced configuration
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=security_config.cors.allowed_origins if security_config.cors.allowed_origins else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.cors.allowed_origins,
    allow_credentials=security_config.cors.allow_credentials,
    allow_methods=security_config.cors.allowed_methods,
    allow_headers=security_config.cors.allowed_headers,
    max_age=security_config.cors.max_age,
)

# Add compression after security
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add comprehensive security headers"""
    response = await call_next(request)
    
    # Add security headers
    security_headers = security_config.get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value
    
    # Additional security headers
    response.headers["X-API-Version"] = "2.0.0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-DNS-Prefetch-Control"] = "off"
    response.headers["X-Download-Options"] = "noopen"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    
    # Remove server information
    if "server" in response.headers:
        del response.headers["server"]
    
    return response

# Mount static files
if Path("public").exists():
    app.mount("/static", StaticFiles(directory="public"), name="static")


# Security middleware
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    """Apply security middleware"""
    try:
        # Validate request
        await security_middleware.validate_request(request)

        # Process request
        with ProfileBlock("request_processing"):
            response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security middleware error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal security error"
        )


# Authentication dependency
async def get_current_user(credentials: Optional[HTTPBearer] = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        return None

    try:
        payload = auth_manager.verify_token(credentials.credentials)
        return payload
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        return None


# API Endpoints
@app.get("/", response_class=FileResponse)
async def root():
    """Serve main page"""
    public_path = Path("public/brainsait-enhanced.html")
    if public_path.exists():
        return FileResponse(public_path)
    return {"message": "Tawnia Healthcare Analytics API", "version": "2.0.0"}


@app.get("/health")
@performance_profiler.profile("api.health")
async def health_check():
    """Enhanced health check endpoint"""
    with log_api_call("health_check"):
        try:
            # Get system stats
            system_stats = system_monitor.get_current_stats()

            # Check component health
            components = {
                "excel_processor": "healthy",
                "analysis_engine": "healthy",
                "insights_generator": "healthy" if settings.get_openai_api_key() else "degraded",
                "report_generator": "healthy",
                "cache": "healthy" if settings.enable_caching else "disabled",
                "monitoring": "healthy" if settings.monitoring.enabled else "disabled"
            }

            # Check circuit breaker status
            circuit_breakers = {
                "excel_processing": excel_breaker.state.name,
                "ai_insights": ai_breaker.state.name,
                "database": db_breaker.state.name
            }

            # Get performance metrics
            metrics_summary = metrics_collector.get_summary()

            # Overall status
            overall_status = "healthy"
            if any(status == "degraded" for status in components.values()):
                overall_status = "degraded"
            if any(state != "CLOSED" for state in circuit_breakers.values()):
                overall_status = "degraded"

            return {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "environment": settings.environment,
                "components": components,
                "system_stats": system_stats,
                "circuit_breakers": circuit_breakers,
                "metrics": metrics_summary
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "environment": settings.environment,
                "error": str(e)
            }


@app.post("/upload")
@performance_profiler.profile("api.upload")
async def upload_file(
    file: UploadFile = File(...),
    user: Optional[Dict] = Depends(get_current_user)
):
    """Enhanced file upload with security validation"""
    with log_api_call("upload_file", {"filename": file.filename}):
        try:
            # Read file content
            content = await file.read()

            # Validate file
            validation_result = file_validator.validate_file(Path(file.filename), content)

            if not validation_result['is_valid']:
                logger.warning(f"File validation failed: {validation_result['errors']}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "File validation failed",
                        "errors": validation_result['errors'],
                        "warnings": validation_result['warnings']
                    }
                )

            # Sanitize filename
            safe_filename = input_sanitizer.sanitize_filename(file.filename)

            # Process file with circuit breaker
            @excel_breaker
            async def process_file_safely():
                return await excel_processor.process_file(content, safe_filename)

            result = await process_file_safely()

            # Cache result if enabled
            if settings.enable_caching:
                cache_key = f"file_processing:{safe_filename}:{hash(content)}"
                await multi_cache.set(cache_key, result)

            # Log success metrics
            metrics_collector.increment_counter("file.upload.success")
            metrics_collector.record_histogram("file.size", len(content))

            return {
                "message": "File uploaded and processed successfully",
                "filename": safe_filename,
                "file_id": result.get("file_id"),
                "summary": result.get("summary"),
                "validation_info": validation_result
            }

        except Exception as e:
            metrics_collector.increment_counter("file.upload.error")
            logger.error(f"File upload error: {e}")

            if isinstance(e, HTTPException):
                raise e

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File processing failed: {str(e)}"
            )


@app.post("/analyze")
@performance_profiler.profile("api.analyze")
@cached_result(ttl=3600)  # Cache for 1 hour
async def analyze_data(
    request: AnalysisRequest,
    user: Optional[Dict] = Depends(get_current_user)
):
    """Enhanced data analysis with caching"""
    with log_analysis_operation("comprehensive_analysis", {"file_id": request.file_id}):
        try:
            # Sanitize input
            sanitized_request = input_sanitizer.sanitize_json_input(request.dict())

            # Perform analysis
            result = await analysis_engine.analyze_comprehensive(
                file_id=sanitized_request["file_id"],
                analysis_types=sanitized_request.get("analysis_types", ["rejections", "trends"])
            )

            # Log success metrics
            metrics_collector.increment_counter("analysis.success")
            metrics_collector.record_histogram("analysis.items", len(result.get("results", [])))

            return result

        except Exception as e:
            metrics_collector.increment_counter("analysis.error")
            logger.error(f"Analysis error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {str(e)}"
            )


@app.post("/insights")
@performance_profiler.profile("api.insights")
@cached_result(ttl=7200)  # Cache for 2 hours
async def generate_insights(
    request: InsightsRequest,
    user: Optional[Dict] = Depends(get_current_user)
):
    """Enhanced AI insights generation with circuit breaker"""
    with log_analysis_operation("ai_insights", {"file_id": request.file_id}):
        try:
            # Sanitize input
            sanitized_request = input_sanitizer.sanitize_json_input(request.dict())

            # Generate insights with circuit breaker
            @ai_breaker
            async def generate_insights_safely():
                return await insights_generator.generate_insights(
                    file_id=sanitized_request["file_id"],
                    focus_area=sanitized_request.get("focus_area", "comprehensive")
                )

            result = await generate_insights_safely()

            # Log success metrics
            metrics_collector.increment_counter("insights.success")

            return result

        except Exception as e:
            metrics_collector.increment_counter("insights.error")
            logger.error(f"Insights generation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Insights generation failed: {str(e)}"
            )


@app.post("/reports/generate")
@performance_profiler.profile("api.reports")
async def generate_report(
    request: ReportRequest,
    user: Optional[Dict] = Depends(get_current_user)
):
    """Enhanced report generation"""
    with log_analysis_operation("report_generation", {"file_id": request.file_id}):
        try:
            # Sanitize input
            sanitized_request = input_sanitizer.sanitize_json_input(request.dict())

            # Generate report
            result = await report_generator.generate_report(
                file_id=sanitized_request["file_id"],
                report_type=sanitized_request.get("report_type", "pdf"),
                include_charts=sanitized_request.get("include_charts", True)
            )

            # Log success metrics
            metrics_collector.increment_counter("reports.success")

            return result

        except Exception as e:
            metrics_collector.increment_counter("reports.error")
            logger.error(f"Report generation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(e)}"
            )


@app.get("/files")
@performance_profiler.profile("api.files.list")
async def list_files(user: Optional[Dict] = Depends(get_current_user)):
    """List uploaded files"""
    with log_api_call("list_files"):
        try:
            files = await excel_processor.list_files()
            metrics_collector.increment_counter("files.list.success")
            return files
        except Exception as e:
            metrics_collector.increment_counter("files.list.error")
            logger.error(f"List files error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list files: {str(e)}"
            )


@app.delete("/files/{file_id}")
@performance_profiler.profile("api.files.delete")
async def delete_file(
    file_id: str,
    user: Optional[Dict] = Depends(get_current_user)
):
    """Delete uploaded file"""
    with log_api_call("delete_file", {"file_id": file_id}):
        try:
            # Sanitize file_id
            safe_file_id = input_sanitizer.sanitize_string(file_id)

            success = await excel_processor.delete_file(safe_file_id)

            if success:
                # Clear related cache entries
                if settings.enable_caching:
                    await multi_cache.clear_pattern(f"*{safe_file_id}*")

                metrics_collector.increment_counter("files.delete.success")
                return {"message": "File deleted successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )

        except Exception as e:
            metrics_collector.increment_counter("files.delete.error")
            logger.error(f"Delete file error: {e}")

            if isinstance(e, HTTPException):
                raise e

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )


@app.get("/metrics")
@performance_profiler.profile("api.metrics")
async def get_metrics(user: Optional[Dict] = Depends(get_current_user)):
    """Get system metrics"""
    try:
        # Get comprehensive metrics
        system_stats = system_monitor.get_current_stats()
        metrics_summary = metrics_collector.get_summary()
        performance_report = performance_analyzer.analyze_performance()

        return {
            "system_stats": system_stats,
            "metrics_summary": metrics_summary,
            "performance_report": performance_report.to_dict(),
            "cache_stats": await multi_cache.get_stats() if settings.enable_caching else None
        }

    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    metrics_collector.increment_counter(f"http.error.{exc.status_code}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    metrics_collector.increment_counter("http.error.500")
    logger.error(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    # Ensure directories exist
    settings.ensure_directories()

    # Configure logging
    import logging
    logging.basicConfig(level=getattr(logging, settings.logging.level))

    # Run server
    uvicorn.run(
        "main_enhanced:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.is_development,
        workers=settings.workers if not settings.is_development else 1,
        log_level=settings.logging.level.lower(),
        access_log=True,
        server_header=False,  # Security: hide server header
        date_header=False     # Security: hide date header
    )
