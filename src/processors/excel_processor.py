"""
Excel file processor using pandas for advanced data analysis
"""

import pandas as pd
import numpy as np
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import uuid
import json
from datetime import datetime, timedelta
import re
from dataclasses import dataclass

from ..utils.logger import setup_logger
from ..models.schemas import DataSummary, ValidationResult, ClaimRecord, StatisticalMetrics

logger = setup_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of file processing"""
    file_id: str
    summary: DataSummary
    validation: ValidationResult
    data: pd.DataFrame
    metadata: Dict[str, Any]


class ExcelProcessor:
    """Advanced Excel file processor with healthcare-specific validation"""

    def __init__(self):
        self.processed_files: Dict[str, ProcessingResult] = {}
        self.healthcare_columns = {
            'claim_id': ['claim_id', 'claimid', 'claim_number', 'claim_no'],
            'patient_id': ['patient_id', 'patientid', 'patient_number', 'patient_no'],
            'provider_id': ['provider_id', 'providerid', 'provider_code'],
            'insurance_provider': ['insurance_provider', 'insurer', 'insurance_company'],
            'claim_date': ['claim_date', 'date_submitted', 'submission_date'],
            'service_date': ['service_date', 'date_of_service', 'dos'],
            'amount': ['amount', 'claim_amount', 'billed_amount', 'total_amount'],
            'status': ['status', 'claim_status', 'approval_status'],
            'rejection_reason': ['rejection_reason', 'deny_reason', 'rejection_code'],
            'diagnosis_code': ['diagnosis_code', 'icd_code', 'diagnosis'],
            'procedure_code': ['procedure_code', 'cpt_code', 'procedure']
        }

    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process an uploaded Excel/CSV file"""
        try:
            start_time = datetime.now()
            logger.info(f"Processing file: {file_path}")

            # Read file based on extension
            df = await self._read_file(file_path)

            # Generate unique file ID
            file_id = str(uuid.uuid4())

            # Normalize column names
            df = self._normalize_columns(df)

            # Detect file type and structure
            file_type = await self._detect_file_type(df)

            # Validate data
            validation_result = await self._validate_data(df, file_type)

            # Generate summary
            processing_time = (datetime.now() - start_time).total_seconds()
            summary = self._generate_summary(df, file_path, processing_time)

            # Store processing result
            result = ProcessingResult(
                file_id=file_id,
                summary=summary,
                validation=validation_result,
                data=df,
                metadata={
                    'file_path': str(file_path),
                    'file_type': file_type,
                    'processed_at': datetime.now().isoformat(),
                    'processing_time': processing_time
                }
            )

            self.processed_files[file_id] = result

            logger.info(f"Successfully processed {file_path} with ID {file_id}")

            return {
                'file_id': file_id,
                'summary': summary.dict(),
                'validation': validation_result.dict()
            }

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise ValueError(f"File not found: {file_path}")
        except PermissionError:
            logger.error(f"Permission denied accessing file: {file_path}")
            raise ValueError(f"Permission denied accessing file: {file_path}")
        except Exception as e:
            # Sanitize error message for logging
            safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
            logger.error(f"Error processing file {file_path}: {safe_error}")
            raise

    async def _read_file(self, file_path: Path) -> pd.DataFrame:
        """Read file based on extension"""
        suffix = file_path.suffix.lower()

        try:
            if suffix == '.csv':
                # Try different encodings and delimiters
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not decode CSV file with any encoding")

            elif suffix in ['.xlsx', '.xls']:
                # Read Excel file
                df = pd.read_excel(file_path, engine='openpyxl' if suffix == '.xlsx' else 'xlrd')

            else:
                raise ValueError(f"Unsupported file format: {suffix}")

            if df.empty:
                raise ValueError("File is empty or contains no readable data")

            return df

        except Exception as e:
            # Sanitize error message for logging
            safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
            logger.error(f"Error reading file {file_path}: {safe_error}")
            raise

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names for consistency"""
        # Convert to lowercase and replace spaces/special chars with underscores
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)

        # Map common healthcare column variations
        column_mapping = {}
        for standard_name, variations in self.healthcare_columns.items():
            for col in df.columns:
                if col in variations:
                    column_mapping[col] = standard_name
                    break

        if column_mapping:
            df = df.rename(columns=column_mapping)
            logger.info(f"Mapped columns: {column_mapping}")

        return df

    async def _detect_file_type(self, df: pd.DataFrame) -> str:
        """Detect the type of healthcare data"""
        columns = set(df.columns.str.lower())

        # Check for healthcare insurance claim patterns
        claim_indicators = ['claim', 'patient', 'provider', 'insurance', 'amount', 'status']
        medical_indicators = ['diagnosis', 'procedure', 'icd', 'cpt']
        financial_indicators = ['amount', 'cost', 'payment', 'billing']

        claim_score = sum(1 for indicator in claim_indicators if any(indicator in col for col in columns))
        medical_score = sum(1 for indicator in medical_indicators if any(indicator in col for col in columns))
        financial_score = sum(1 for indicator in financial_indicators if any(indicator in col for col in columns))

        if claim_score >= 3:
            return "healthcare_claims"
        elif medical_score >= 2:
            return "medical_records"
        elif financial_score >= 2:
            return "financial_data"
        else:
            return "general_data"

    async def _validate_data(self, df: pd.DataFrame, file_type: str) -> ValidationResult:
        """Comprehensive data validation"""
        issues = []
        warnings = []
        recommendations = []

        # Basic data quality checks
        total_records = len(df)
        null_percentage = (df.isnull().sum().sum() / (total_records * len(df.columns))) * 100

        # Check for empty dataframe
        if total_records == 0:
            issues.append("File contains no data records")

        # Check for high null percentage
        if null_percentage > 30:
            issues.append(f"High percentage of missing data: {null_percentage:.1f}%")
        elif null_percentage > 15:
            warnings.append(f"Moderate missing data: {null_percentage:.1f}%")

        # Healthcare-specific validations
        if file_type == "healthcare_claims":
            issues.extend(await self._validate_healthcare_claims(df))

        # Date validation
        date_issues = await self._validate_dates(df)
        issues.extend(date_issues)

        # Numeric validation
        numeric_issues = await self._validate_numeric_fields(df)
        issues.extend(numeric_issues)

        # Duplicate records check
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            warnings.append(f"Found {duplicate_count} duplicate records")
            recommendations.append("Consider removing duplicate records")

        # Data consistency checks
        consistency_issues = await self._check_data_consistency(df)
        warnings.extend(consistency_issues)

        # Calculate quality score
        quality_score = self._calculate_quality_score(df, issues, warnings)

        # Generate recommendations
        if quality_score < 0.7:
            recommendations.append("Data quality is below acceptable threshold")
            recommendations.append("Consider data cleaning before analysis")

        if null_percentage > 10:
            recommendations.append("Address missing data through imputation or collection")

        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations
        )

    async def _validate_healthcare_claims(self, df: pd.DataFrame) -> List[str]:
        """Validate healthcare claims data"""
        issues = []

        # Check for required columns
        required_columns = ['claim_id', 'amount', 'status']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")

        # Validate claim amounts
        if 'amount' in df.columns:
            amount_col = df['amount']
            negative_amounts = (amount_col < 0).sum()
            if negative_amounts > 0:
                issues.append(f"Found {negative_amounts} claims with negative amounts")

            zero_amounts = (amount_col == 0).sum()
            if zero_amounts > len(df) * 0.1:  # More than 10% zero amounts
                issues.append(f"High number of zero-amount claims: {zero_amounts}")

        # Validate status values
        if 'status' in df.columns:
            valid_statuses = ['approved', 'denied', 'pending', 'rejected', 'paid', 'processing']
            invalid_statuses = df[~df['status'].str.lower().isin(valid_statuses)]['status'].unique()
            if len(invalid_statuses) > 0:
                issues.append(f"Invalid status values found: {list(invalid_statuses)}")

        return issues

    async def _validate_dates(self, df: pd.DataFrame) -> List[str]:
        """Validate date columns"""
        issues = []

        date_columns = [col for col in df.columns if 'date' in col.lower()]

        for col in date_columns:
            try:
                # Try to convert to datetime
                date_series = pd.to_datetime(df[col], errors='coerce')
                null_dates = date_series.isnull().sum()

                if null_dates > 0:
                    issues.append(f"Invalid dates in column '{col}': {null_dates} records")

                # Check for future dates (beyond today + 1 year)
                future_threshold = datetime.now() + timedelta(days=365)
                future_dates = (date_series > future_threshold).sum()
                if future_dates > 0:
                    issues.append(f"Future dates found in '{col}': {future_dates} records")

                # Check for very old dates (before 1900)
                old_threshold = datetime(1900, 1, 1)
                old_dates = (date_series < old_threshold).sum()
                if old_dates > 0:
                    issues.append(f"Very old dates found in '{col}': {old_dates} records")

            except Exception as e:
                # Sanitize error message
                safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:100]
                issues.append(f"Error validating dates in column '{col}': {safe_error}")

        return issues

    async def _validate_numeric_fields(self, df: pd.DataFrame) -> List[str]:
        """Validate numeric fields"""
        issues = []

        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            series = df[col]

            # Check for infinite values
            inf_count = np.isinf(series).sum()
            if inf_count > 0:
                issues.append(f"Infinite values in column '{col}': {inf_count} records")

            # Check for extremely large values (potential data entry errors)
            if col.lower() in ['amount', 'cost', 'payment']:
                large_values = (series > 1000000).sum()  # Values > 1M
                if large_values > 0:
                    issues.append(f"Unusually large values in '{col}': {large_values} records")

        return issues

    async def _check_data_consistency(self, df: pd.DataFrame) -> List[str]:
        """Check for data consistency issues"""
        warnings = []

        # Check date consistency (service date should be before or equal to claim date)
        if 'service_date' in df.columns and 'claim_date' in df.columns:
            try:
                service_dates = pd.to_datetime(df['service_date'], errors='coerce')
                claim_dates = pd.to_datetime(df['claim_date'], errors='coerce')
                inconsistent = (service_dates > claim_dates).sum()
                if inconsistent > 0:
                    warnings.append(f"Service dates after claim dates: {inconsistent} records")
            except Exception as e:
                # Log error instead of silent pass (CWE-703 fix)
                logger.warning(f"Error validating service dates: {str(e)[:100]}")
                continue

        # Check amount consistency
        if 'amount' in df.columns and 'status' in df.columns:
            try:
                denied_with_amount = df[(df['status'].str.lower() == 'denied') & (df['amount'] > 0)]
                if len(denied_with_amount) > 0:
                    warnings.append(f"Denied claims with positive amounts: {len(denied_with_amount)} records")
            except Exception as e:
                # Log error instead of silent pass (CWE-703 fix)
                logger.warning(f"Error validating denied claims: {str(e)[:100]}")
                continue

        return warnings

    def _calculate_quality_score(self, df: pd.DataFrame, issues: List[str], warnings: List[str]) -> float:
        """Calculate overall data quality score"""
        base_score = 1.0

        # Penalty for issues
        base_score -= len(issues) * 0.1

        # Penalty for warnings
        base_score -= len(warnings) * 0.05

        # Penalty for missing data
        null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        base_score -= (null_percentage / 100) * 0.3

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))

    def _generate_summary(self, df: pd.DataFrame, file_path: Path, processing_time: float) -> DataSummary:
        """Generate data summary"""
        # Detect date range
        date_range = None
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        if date_columns:
            try:
                for col in date_columns:
                    date_series = pd.to_datetime(df[col], errors='coerce').dropna()
                    if not date_series.empty:
                        date_range = {
                            'start': date_series.min().isoformat(),
                            'end': date_series.max().isoformat(),
                            'column': col
                        }
                        break
            except Exception as e:
                # Log error instead of silent pass (CWE-703 fix)
                logger.warning(f"Error finding column pattern: {str(e)[:100]}")
                continue

        return DataSummary(
            total_records=len(df),
            columns=list(df.columns),
            date_range=date_range,
            file_type=file_path.suffix.lower(),
            file_size=file_path.stat().st_size,
            processing_time=processing_time
        )

    def get_processed_data(self, file_id: str) -> Optional[pd.DataFrame]:
        """Get processed data by file ID"""
        result = self.processed_files.get(file_id)
        return result.data if result else None

    def get_processing_result(self, file_id: str) -> Optional[ProcessingResult]:
        """Get complete processing result by file ID"""
        return self.processed_files.get(file_id)

    def get_file_ids(self) -> List[str]:
        """Get all processed file IDs"""
        return list(self.processed_files.keys())

    async def validate_claim_data(self, claim_data: Dict[str, Any]) -> bool:
        """Validate individual claim record"""
        try:
            # Check required fields
            required_fields = ['claim_id', 'amount']
            for field in required_fields:
                if not claim_data.get(field):
                    return False

            # Validate amount
            amount = claim_data.get('amount')
            if not isinstance(amount, (int, float)) or amount < 0:
                return False

            # Validate dates
            for date_field in ['claim_date', 'service_date']:
                if date_field in claim_data:
                    if not self.is_valid_date(claim_data[date_field]):
                        return False

            return True

        except Exception:
            return False

    def is_valid_date(self, date_value: Any) -> bool:
        """Check if a value is a valid date"""
        if pd.isna(date_value):
            return False

        try:
            parsed_date = pd.to_datetime(date_value)
            # Check if date is reasonable (not too far in past or future)
            min_date = datetime(1900, 1, 1)
            max_date = datetime.now() + timedelta(days=365)
            # Handle timezone-aware datetime comparison
            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.replace(tzinfo=None)
            return min_date <= parsed_date <= max_date
        except Exception:
            return False

    def is_valid_amount(self, amount: Any) -> bool:
        """Check if an amount is valid"""
        try:
            if pd.isna(amount):
                return False

            num_amount = float(amount)
            return num_amount >= 0 and num_amount <= 10000000  # Reasonable upper limit
        except Exception:
            return False

    def is_valid_insurance_provider(self, provider: Any) -> bool:
        """Check if insurance provider is valid"""
        if pd.isna(provider) or not provider:
            return False

        # Check if it's a reasonable string
        provider_str = str(provider).strip()
        return len(provider_str) >= 2 and len(provider_str) <= 100

    async def get_statistics(self, file_id: str) -> Optional[Dict[str, StatisticalMetrics]]:
        """Get statistical metrics for numeric columns"""
        df = self.get_processed_data(file_id)
        if df is None:
            return None

        stats = {}
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            series = df[col].dropna()
            if not series.empty:
                stats[col] = StatisticalMetrics(
                    mean=float(series.mean()),
                    median=float(series.median()),
                    std_dev=float(series.std()),
                    min_value=float(series.min()),
                    max_value=float(series.max()),
                    quartiles={
                        'q1': float(series.quantile(0.25)),
                        'q3': float(series.quantile(0.75))
                    },
                    outliers_count=int(self._count_outliers(series)),
                    null_count=int(df[col].isnull().sum()),
                    unique_count=int(series.nunique())
                )

        return stats

    def _count_outliers(self, series: pd.Series) -> int:
        """Count outliers using IQR method"""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return ((series < lower_bound) | (series > upper_bound)).sum()
