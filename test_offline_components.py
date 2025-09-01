#!/usr/bin/env python3
"""
Offline Component Test Suite
Tests individual components without requiring a running server
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.processors.excel_processor import ExcelProcessor
from src.analysis.analysis_engine import AnalysisEngine
from src.ai.insights_generator import InsightsGenerator
from src.reports.report_generator import ReportGenerator
from src.utils.config import Settings
from src.utils.logger import setup_api_logging, get_api_logger
from src.utils.cache import MemoryCache, FileCache
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.security import FileValidator, InputSanitizer
from src.utils.performance import MetricsCollector, SystemMonitor

class OfflineTestSuite:
    def __init__(self):
        """Initialize the offline test suite."""
        self.results = {}
        self.settings = Settings()
        setup_api_logging()
        self.logger = get_api_logger()

        # Initialize components
        self.excel_processor = ExcelProcessor()
        self.analysis_engine = AnalysisEngine()
        self.insights_generator = InsightsGenerator()
        self.report_generator = ReportGenerator()
        self.file_validator = FileValidator()
        self.input_sanitizer = InputSanitizer()
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor()

        # Create test data
        self.create_test_data()

    def create_test_data(self):
        """Create sample test data."""
        self.test_data = pd.DataFrame({
            'claim_id': ['CLM001', 'CLM002', 'CLM003', 'CLM004', 'CLM005'],
            'patient_id': ['PAT001', 'PAT002', 'PAT003', 'PAT004', 'PAT005'],
            'provider_id': ['PRV001', 'PRV002', 'PRV001', 'PRV003', 'PRV002'],
            'rejection_reason': ['Missing Documentation', 'Invalid Code', 'Pre-authorization Required', 'Duplicate Claim', 'Coverage Expired'],
            'amount': [1500.00, 2300.00, 800.00, 1200.00, 950.00],
            'submission_date': pd.to_datetime(['2025-01-15', '2025-01-20', '2025-01-25', '2025-01-30', '2025-02-05']),
            'rejection_date': pd.to_datetime(['2025-01-18', '2025-01-23', '2025-01-28', '2025-02-02', '2025-02-08']),
            'status': ['Rejected', 'Rejected', 'Rejected', 'Rejected', 'Rejected']
        })

        # Save test data to Excel file
        test_file_path = Path("test_data.xlsx")
        self.test_data.to_excel(test_file_path, index=False)
        self.test_file_path = test_file_path

    async def test_excel_processor(self) -> Dict[str, Any]:
        """Test Excel processor functionality."""
        try:
            self.logger.info("Testing Excel Processor...")

            # Test file processing
            result = await self.excel_processor.process_file(str(self.test_file_path))

            # Validate results
            assert 'data' in result
            assert 'summary' in result
            assert 'metadata' in result
            assert len(result['data']) == 5

            return {"status": "PASSED", "message": "Excel processor working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Excel processor failed: {str(e)}"}

    async def test_analysis_engine(self) -> Dict[str, Any]:
        """Test analysis engine functionality."""
        try:
            self.logger.info("Testing Analysis Engine...")

            # Test rejection analysis
            rejection_analysis = await self.analysis_engine.analyze_rejections(self.test_data)

            # Test trend analysis
            trend_analysis = await self.analysis_engine.analyze_trends(self.test_data)

            # Test pattern detection
            pattern_analysis = await self.analysis_engine.detect_patterns(self.test_data)

            # Validate results
            assert 'rejection_categories' in rejection_analysis
            assert 'trends' in trend_analysis
            assert 'patterns' in pattern_analysis

            return {"status": "PASSED", "message": "Analysis engine working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Analysis engine failed: {str(e)}"}

    async def test_insights_generator(self) -> Dict[str, Any]:
        """Test AI insights generator (without API calls)."""
        try:
            self.logger.info("Testing Insights Generator...")

            # Test fallback insights (without OpenAI API)
            insights = await self.insights_generator._generate_fallback_insights(
                self.test_data, {"test": "analysis"}
            )

            # Validate results
            assert 'summary' in insights
            assert 'key_findings' in insights
            assert 'recommendations' in insights

            return {"status": "PASSED", "message": "Insights generator (fallback) working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Insights generator failed: {str(e)}"}

    async def test_report_generator(self) -> Dict[str, Any]:
        """Test report generator functionality."""
        try:
            self.logger.info("Testing Report Generator...")

            # Test data for report
            analysis_results = {
                "rejections": {"total": 5, "by_reason": {"Missing Documentation": 1}},
                "trends": {"monthly_trend": "increasing"},
                "patterns": {"provider_patterns": {"PRV001": 2}}
            }

            insights = {
                "summary": "Test summary",
                "key_findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1"]
            }

            # Test PDF generation
            pdf_result = await self.report_generator.generate_pdf_report(
                self.test_data, analysis_results, insights
            )

            # Test Excel generation
            excel_result = await self.report_generator.generate_excel_report(
                self.test_data, analysis_results, insights
            )

            # Validate results
            assert pdf_result is not None
            assert excel_result is not None

            return {"status": "PASSED", "message": "Report generator working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Report generator failed: {str(e)}"}

    def test_file_validator(self) -> Dict[str, Any]:
        """Test file validator functionality."""
        try:
            self.logger.info("Testing File Validator...")

            # Test valid file
            is_valid = self.file_validator.validate_file(self.test_file_path)
            assert is_valid == True

            # Test file type validation
            is_excel = self.file_validator.is_excel_file("test.xlsx")
            assert is_excel == True

            is_not_excel = self.file_validator.is_excel_file("test.txt")
            assert is_not_excel == False

            return {"status": "PASSED", "message": "File validator working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"File validator failed: {str(e)}"}

    def test_input_sanitizer(self) -> Dict[str, Any]:
        """Test input sanitizer functionality."""
        try:
            self.logger.info("Testing Input Sanitizer...")

            # Test text sanitization
            clean_text = self.input_sanitizer.sanitize_text("<script>alert('xss')</script>Normal text")
            assert "<script>" not in clean_text
            assert "Normal text" in clean_text

            # Test filename sanitization
            clean_filename = self.input_sanitizer.sanitize_filename("../../../etc/passwd")
            assert "../" not in clean_filename

            return {"status": "PASSED", "message": "Input sanitizer working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Input sanitizer failed: {str(e)}"}

    def test_cache_system(self) -> Dict[str, Any]:
        """Test caching system functionality."""
        try:
            self.logger.info("Testing Cache System...")

            # Test memory cache
            memory_cache = MemoryCache(max_size=100)
            memory_cache.set("test_key", {"data": "test_value"})
            cached_value = memory_cache.get("test_key")
            assert cached_value["data"] == "test_value"

            # Test file cache
            file_cache = FileCache()
            file_cache.set("file_test_key", {"data": "file_test_value"})
            cached_file_value = file_cache.get("file_test_key")
            assert cached_file_value["data"] == "file_test_value"

            return {"status": "PASSED", "message": "Cache system working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Cache system failed: {str(e)}"}

    def test_circuit_breaker(self) -> Dict[str, Any]:
        """Test circuit breaker functionality."""
        try:
            self.logger.info("Testing Circuit Breaker...")

            # Test circuit breaker creation
            cb = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=5,
                expected_exception=Exception
            )

            # Test successful operation
            @cb
            def successful_operation():
                return "success"

            result = successful_operation()
            assert result == "success"
            assert cb.state == "closed"

            return {"status": "PASSED", "message": "Circuit breaker working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Circuit breaker failed: {str(e)}"}

    def test_metrics_collector(self) -> Dict[str, Any]:
        """Test metrics collector functionality."""
        try:
            self.logger.info("Testing Metrics Collector...")

            # Test metric recording
            self.metrics_collector.record_request("test_endpoint", 200, 0.5)
            self.metrics_collector.record_counter("test_counter")
            self.metrics_collector.record_gauge("test_gauge", 42.0)

            # Test metric retrieval
            metrics = self.metrics_collector.get_metrics()
            assert "requests" in metrics
            assert "counters" in metrics
            assert "gauges" in metrics

            return {"status": "PASSED", "message": "Metrics collector working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"Metrics collector failed: {str(e)}"}

    def test_system_monitor(self) -> Dict[str, Any]:
        """Test system monitor functionality."""
        try:
            self.logger.info("Testing System Monitor...")

            # Test system metrics collection
            system_metrics = self.system_monitor.get_system_metrics()

            # Validate metrics
            assert "cpu_percent" in system_metrics
            assert "memory_percent" in system_metrics
            assert "disk_usage" in system_metrics

            return {"status": "PASSED", "message": "System monitor working correctly"}

        except Exception as e:
            return {"status": "FAILED", "message": f"System monitor failed: {str(e)}"}

    async def run_all_tests(self):
        """Run all offline component tests."""
        test_methods = [
            ("Excel Processor", self.test_excel_processor),
            ("Analysis Engine", self.test_analysis_engine),
            ("Insights Generator", self.test_insights_generator),
            ("Report Generator", self.test_report_generator),
            ("File Validator", self.test_file_validator),
            ("Input Sanitizer", self.test_input_sanitizer),
            ("Cache System", self.test_cache_system),
            ("Circuit Breaker", self.test_circuit_breaker),
            ("Metrics Collector", self.test_metrics_collector),
            ("System Monitor", self.test_system_monitor),
        ]

        self.logger.info("Starting Offline Component Test Suite")

        passed = 0
        failed = 0

        for test_name, test_method in test_methods:
            self.logger.info(f"Running {test_name} tests...")

            try:
                if asyncio.iscoroutinefunction(test_method):
                    result = await test_method()
                else:
                    result = test_method()

                if result["status"] == "PASSED":
                    self.logger.success(f"{test_name} tests PASSED")
                    passed += 1
                else:
                    self.logger.error(f"{test_name} tests FAILED: {result['message']}")
                    failed += 1

                self.results[test_name] = result

            except Exception as e:
                self.logger.error(f"{test_name} tests FAILED: {str(e)}")
                self.results[test_name] = {"status": "FAILED", "message": str(e)}
                failed += 1

        # Generate test report
        self.generate_test_report(passed, failed)

        # Cleanup
        self.cleanup()

    def generate_test_report(self, passed: int, failed: int):
        """Generate a comprehensive test report."""
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0

        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "results": self.results,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
            }
        }

        # Save detailed report
        with open("offline_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info("=" * 50)
        self.logger.info("OFFLINE COMPONENT TEST SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total Tests: {total}")
        self.logger.info(f"Passed: {passed}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info(f"Report saved to: offline_test_report.json")

        if failed > 0:
            self.logger.warning("FAILED TESTS:")
            for test_name, result in self.results.items():
                if result["status"] == "FAILED":
                    self.logger.error(f"  - {test_name}: {result['message']}")

    def cleanup(self):
        """Clean up test files and resources."""
        try:
            if self.test_file_path.exists():
                self.test_file_path.unlink()
        except Exception as e:
            self.logger.warning(f"Cleanup warning: {e}")

async def main():
    """Main entry point for offline tests."""
    test_suite = OfflineTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
