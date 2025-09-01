"""
Tawnia Healthcare Analytics System - Python FastAPI Backend
Main server application with comprehensive healthcare insurance data analysis
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path

# Import our modules
from src.processors.excel_processor import ExcelProcessor
from src.analysis.analysis_engine import AnalysisEngine
from src.ai.insights_generator import InsightsGenerator
from src.reports.report_generator import ReportGenerator
from src.utils.logger import setup_logger
from src.utils.config import get_settings
from src.security.security_config import get_security_config
from src.security.middleware import SecurityMiddleware, JWTAuthenticationMiddleware
from src.models.schemas import (
    UploadResponse, AnalysisRequest, AnalysisResponse,
    InsightsRequest, InsightsResponse, ReportRequest, ReportResponse
)

# Initialize logger
logger = setup_logger(__name__)

# Get configuration and security settings
settings = get_settings()
security_config = get_security_config(settings.environment)

# Create directories
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")
DATA_DIR = Path("data")
LOGS_DIR = Path("logs")

for directory in [UPLOAD_DIR, REPORTS_DIR, DATA_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Initialize components with error handling
try:
    excel_processor = ExcelProcessor()
    analysis_engine = AnalysisEngine()
    insights_generator = InsightsGenerator()
    report_generator = ReportGenerator()
    logger.info("All components initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize components: {str(e)}")
    raise RuntimeError(f"Application startup failed: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Tawnia Healthcare Analytics System")
    logger.info(f"Python version: {settings.python_version}")
    logger.info(f"Environment: {settings.environment}")
    yield
    logger.info("Shutting down Tawnia Healthcare Analytics System")

# Create FastAPI app with enhanced security
app = FastAPI(
    title="Tawnia Healthcare Analytics API",
    description="Advanced healthcare insurance data analysis platform with comprehensive security",
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan
)

# Add Security Middleware (FIRST - most important)
app.add_middleware(SecurityMiddleware, config=security_config)

# Add CORS middleware with security-conscious configuration
cors_origins = security_config.network_security.cors_origins
if settings.environment == "development":
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=security_config.network_security.cors_methods,
    allow_headers=security_config.network_security.cors_headers,
)

# Trusted host middleware with security configuration
allowed_hosts = ["localhost", "127.0.0.1"]
if settings.environment == "production":
    # Add production domains here
    allowed_hosts.extend(["yourdomain.com", "www.yourdomain.com"])

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

# Enhanced Security and Authentication
jwt_auth = JWTAuthenticationMiddleware(security_config)
security = HTTPBearer(auto_error=False)

# Static files
app.mount("/static", StaticFiles(directory="public"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "environment": settings.environment,
        "components": {
            "excel_processor": "ready",
            "analysis_engine": "ready",
            "insights_generator": "ready",
            "report_generator": "ready"
        }
    }

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    try:
        with open("public/brainsait-enhanced.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Tawnia Healthcare Analytics System</h1><p>API is running. Visit /docs for documentation.</p>")

# Upload endpoints
@app.post("/api/upload", response_model=UploadResponse)
async def upload_single_file(file: UploadFile = File(...)):
    """Upload and process a single Excel file"""
    try:
        logger.info(f"Processing upload: {file.filename}")

        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) and CSV files are supported")

        # Validate and sanitize filename to prevent path traversal
        from src.utils.security import InputSanitizer
        safe_filename = InputSanitizer.sanitize_filename(file.filename)
        
        # Save uploaded file with validated path
        file_path = UPLOAD_DIR / safe_filename
        # Ensure the resolved path is within UPLOAD_DIR
        if not str(file_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process the file
        result = await excel_processor.process_file(file_path)

        logger.info(f"Successfully processed {file.filename}")
        return UploadResponse(
            success=True,
            message=f"File {file.filename} processed successfully",
            file_id=result["file_id"],
            filename=file.filename,
            data_summary=result["summary"],
            validation_results=result["validation"]
        )

    except Exception as e:
        logger.error(f"Error processing upload {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/upload/multiple", response_model=List[UploadResponse])
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload and process multiple Excel files"""
    try:
        results = []
        for file in files:
            try:
                result = await upload_single_file(file)
                results.append(result)
            except HTTPException as e:
                results.append(UploadResponse(
                    success=False,
                    message=str(e.detail),
                    filename=file.filename
                ))

        return results

    except Exception as e:
        logger.error(f"Error processing multiple uploads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

# Analysis endpoints
@app.post("/api/analyze/rejections", response_model=AnalysisResponse)
async def analyze_rejections(request: AnalysisRequest):
    """Analyze claim rejections"""
    try:
        result = await analysis_engine.analyze_rejections(request.file_ids)
        return AnalysisResponse(
            success=True,
            analysis_type="rejections",
            results=result,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error in rejection analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/trends", response_model=AnalysisResponse)
async def analyze_trends(request: AnalysisRequest):
    """Analyze data trends"""
    try:
        result = await analysis_engine.analyze_trends(request.file_ids)
        return AnalysisResponse(
            success=True,
            analysis_type="trends",
            results=result,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error in trend analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/patterns", response_model=AnalysisResponse)
async def analyze_patterns(request: AnalysisRequest):
    """Analyze data patterns"""
    try:
        result = await analysis_engine.analyze_patterns(request.file_ids)
        return AnalysisResponse(
            success=True,
            analysis_type="patterns",
            results=result,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error in pattern analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/quality", response_model=AnalysisResponse)
async def analyze_quality(request: AnalysisRequest):
    """Analyze data quality"""
    try:
        result = await analysis_engine.analyze_quality(request.file_ids)
        return AnalysisResponse(
            success=True,
            analysis_type="quality",
            results=result,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error in quality analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/comparison", response_model=AnalysisResponse)
async def analyze_comparison(request: AnalysisRequest):
    """Compare multiple datasets"""
    try:
        if len(request.file_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 files required for comparison")

        result = await analysis_engine.analyze_comparison(request.file_ids)
        return AnalysisResponse(
            success=True,
            analysis_type="comparison",
            results=result,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error in comparison analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Insights endpoint
@app.post("/api/insights", response_model=InsightsResponse)
async def generate_insights(request: InsightsRequest):
    """Generate AI-powered insights"""
    try:
        result = await insights_generator.generate_insights(
            file_ids=request.file_ids,
            analysis_type=request.analysis_type,
            custom_prompt=request.custom_prompt
        )
        return InsightsResponse(
            success=True,
            insights=result["insights"],
            recommendations=result["recommendations"],
            confidence_score=result["confidence_score"],
            source=result["source"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Report endpoints
@app.post("/api/reports/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate comprehensive report"""
    try:
        result = await report_generator.generate_report(
            file_ids=request.file_ids,
            format=request.format,
            include_charts=request.include_charts,
            analysis_types=request.analysis_types
        )
        return ReportResponse(
            success=True,
            report_id=result["report_id"],
            filename=result["filename"],
            format=request.format,
            download_url=f"/api/reports/download/{result['report_id']}",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/download/{report_id}")
async def download_report(report_id: str):
    """Download a generated report"""
    try:
        # Validate report_id to prevent path traversal
        if not re.match(r'^[a-zA-Z0-9_-]+$', report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")
        
        # Find report files with the given ID
        report_files = list(REPORTS_DIR.glob(f"{report_id}.*"))
        if not report_files:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report_path = report_files[0]  # Use the first matching file
        
        # Ensure the resolved path is within the reports directory
        if not str(report_path.resolve()).startswith(str(REPORTS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")

        return FileResponse(
            path=report_path,
            filename=report_path.name,
            media_type='application/octet-stream'
        )
    except Exception as e:
        # Sanitize report_id for logging
        safe_report_id = ''.join(c for c in report_id if c.isalnum() or c in '_-')[:50]
        safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
        logger.error(f"Error downloading report {safe_report_id}: {safe_error}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/list")
async def list_reports():
    """List all available reports"""
    try:
        reports = []
        for report_file in REPORTS_DIR.glob("*"):
            if report_file.is_file():
                stat = report_file.stat()
                reports.append({
                    "report_id": report_file.stem,
                    "filename": report_file.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "download_url": f"/api/reports/download/{report_file.stem}"
                })

        return {"reports": reports}
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete a report"""
    try:
        # Validate report_id to prevent path traversal
        if not re.match(r'^[a-zA-Z0-9_-]+$', report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")
        
        # Use more specific pattern to prevent accidental deletion
        report_files = list(REPORTS_DIR.glob(f"{report_id}.*"))
        if not report_files:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Ensure all files are within the reports directory
        for report_file in report_files:
            if not str(report_file.resolve()).startswith(str(REPORTS_DIR.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")

        for report_file in report_files:
            report_file.unlink()

        return {"message": f"Report {report_id} deleted successfully"}
    except Exception as e:
        # Sanitize report_id for logging
        safe_report_id = ''.join(c for c in report_id if c.isalnum() or c in '_-')[:50]
        safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
        logger.error(f"Error deleting report {safe_report_id}: {safe_error}")
        raise HTTPException(status_code=500, detail=str(e))

# File management endpoints
@app.get("/api/files/list")
async def list_uploaded_files():
    """List all uploaded files"""
    try:
        files = []
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "uploaded": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "type": file_path.suffix.lower()
                })

        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded file"""
    try:
        # Sanitize filename to prevent path traversal
        from src.utils.security import InputSanitizer
        safe_filename = InputSanitizer.sanitize_filename(filename)
        
        file_path = UPLOAD_DIR / safe_filename
        
        # Ensure the resolved path is within the upload directory
        if not str(file_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        file_path.unlink()

        return {"message": f"File {filename} deleted successfully"}
    except Exception as e:
        # Sanitize filename for logging
        safe_filename = ''.join(c for c in filename if ord(c) >= 32 or c in ' \t')[:100]
        safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
        logger.error(f"Error deleting file {safe_filename}: {safe_error}")
        raise HTTPException(status_code=500, detail=str(e))

# Add import for regex
import re

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
