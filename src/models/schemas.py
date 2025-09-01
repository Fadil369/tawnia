"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Supported file types"""
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"


class AnalysisType(str, Enum):
    """Available analysis types"""
    REJECTIONS = "rejections"
    TRENDS = "trends"
    PATTERNS = "patterns"
    QUALITY = "quality"
    COMPARISON = "comparison"


class ReportFormat(str, Enum):
    """Available report formats"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


class DataSummary(BaseModel):
    """Data summary model"""
    total_records: int
    columns: List[str]
    date_range: Optional[Dict[str, str]] = None
    file_type: str
    file_size: int
    processing_time: float


class ValidationResult(BaseModel):
    """Validation result model"""
    is_valid: bool
    quality_score: float = Field(..., ge=0, le=1)
    issues: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []


class UploadResponse(BaseModel):
    """Upload response model"""
    success: bool
    message: str
    file_id: Optional[str] = None
    filename: Optional[str] = None
    data_summary: Optional[DataSummary] = None
    validation_results: Optional[ValidationResult] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AnalysisRequest(BaseModel):
    """Analysis request model"""
    file_ids: List[str]
    analysis_type: Optional[AnalysisType] = None
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None
    
    @validator('file_ids')
    def validate_file_ids(cls, v):
        if not v:
            raise ValueError('At least one file_id is required')
        return v


class AnalysisResult(BaseModel):
    """Analysis result model"""
    summary: Dict[str, Any]
    charts: Optional[List[Dict[str, Any]]] = []
    statistics: Dict[str, float]
    insights: List[str] = []
    recommendations: List[str] = []


class AnalysisResponse(BaseModel):
    """Analysis response model"""
    success: bool
    analysis_type: str
    results: AnalysisResult
    processing_time: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class InsightsRequest(BaseModel):
    """AI insights request model"""
    file_ids: List[str]
    analysis_type: Optional[AnalysisType] = None
    custom_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class InsightsResponse(BaseModel):
    """AI insights response model"""
    success: bool
    insights: List[str]
    recommendations: List[str]
    confidence_score: float = Field(..., ge=0, le=1)
    source: str  # "openai" or "statistical"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ReportRequest(BaseModel):
    """Report generation request model"""
    file_ids: List[str]
    format: ReportFormat = ReportFormat.PDF
    include_charts: bool = True
    analysis_types: List[AnalysisType] = [
        AnalysisType.REJECTIONS,
        AnalysisType.TRENDS,
        AnalysisType.QUALITY
    ]
    custom_title: Optional[str] = None
    sections: Optional[List[str]] = None


class ReportResponse(BaseModel):
    """Report generation response model"""
    success: bool
    report_id: str
    filename: str
    format: ReportFormat
    download_url: str
    file_size: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    version: str
    environment: str
    components: Dict[str, str]


class FileInfo(BaseModel):
    """File information model"""
    filename: str
    size: int
    uploaded: str
    type: str
    file_id: Optional[str] = None


class ClaimRecord(BaseModel):
    """Healthcare claim record model"""
    claim_id: Optional[str] = None
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    insurance_provider: Optional[str] = None
    claim_date: Optional[str] = None
    service_date: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    diagnosis_code: Optional[str] = None
    procedure_code: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


class StatisticalMetrics(BaseModel):
    """Statistical metrics model"""
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    quartiles: Dict[str, float]
    outliers_count: int
    null_count: int
    unique_count: int


class TrendAnalysis(BaseModel):
    """Trend analysis model"""
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float = Field(..., ge=0, le=1)
    seasonal_patterns: List[Dict[str, Any]] = []
    anomalies: List[Dict[str, Any]] = []
    forecast: Optional[List[Dict[str, Any]]] = None


class QualityMetrics(BaseModel):
    """Data quality metrics model"""
    completeness: float = Field(..., ge=0, le=1)
    accuracy: float = Field(..., ge=0, le=1)
    consistency: float = Field(..., ge=0, le=1)
    validity: float = Field(..., ge=0, le=1)
    overall_score: float = Field(..., ge=0, le=1)
    issues: List[str] = []
    recommendations: List[str] = []