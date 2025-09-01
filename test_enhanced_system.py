"""
Comprehensive test script for enhanced Tawnia Healthcare Analytics System
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import httpx
from loguru import logger

# Configure logger
logger.add("test_results.log", rotation="1 MB", level="INFO")


class EnhancedSystemTester:
    """Comprehensive system testing suite"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.uploaded_files = []

    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("Starting Enhanced System Test Suite")

        # Test categories
        test_categories = [
            ("Health Check", self.test_health_check),
            ("Security", self.test_security_features),
            ("File Upload & Validation", self.test_file_upload),
            ("Performance Monitoring", self.test_performance_monitoring),
            ("Caching System", self.test_caching),
            ("Circuit Breaker", self.test_circuit_breaker),
            ("Analytics Engine", self.test_analytics),
            ("AI Insights", self.test_ai_insights),
            ("Report Generation", self.test_reporting),
            ("Error Handling", self.test_error_handling),
            ("Metrics Collection", self.test_metrics),
            ("Cleanup", self.cleanup_test_files)
        ]

        # Run tests
        for category, test_func in test_categories:
            logger.info(f"Running {category} tests...")
            try:
                await test_func()
                self.test_results.append({
                    "category": category,
                    "status": "PASSED",
                    "timestamp": time.time()
                })
                logger.success(f"{category} tests PASSED")
            except Exception as e:
                self.test_results.append({
                    "category": category,
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": time.time()
                })
                logger.error(f"{category} tests FAILED: {e}")

        # Generate test report
        await self.generate_test_report()
        await self.client.aclose()

    async def test_health_check(self):
        """Test enhanced health check endpoint"""
        response = await self.client.get(f"{self.base_url}/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "system_stats" in data
        assert "circuit_breakers" in data
        assert "metrics" in data

        logger.info(f"Health check status: {data['status']}")
        logger.info(f"Components: {data['components']}")

    async def test_security_features(self):
        """Test security middleware and validation"""
        # Test rate limiting (make multiple requests)
        for i in range(5):
            response = await self.client.get(f"{self.base_url}/health")
            assert response.status_code == 200

        # Test security headers
        response = await self.client.get(f"{self.base_url}/health")
        headers = response.headers

        expected_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "strict-transport-security"
        ]

        for header in expected_headers:
            assert header in headers, f"Missing security header: {header}"

        logger.info("Security headers validated")

    async def test_file_upload(self):
        """Test file upload with validation"""
        # Create test Excel file
        test_data = self.create_test_excel_data()
        test_file_path = Path("test_claims.xlsx")
        test_data.to_excel(test_file_path, index=False)

        try:
            # Test valid file upload
            with open(test_file_path, "rb") as f:
                files = {"file": ("test_claims.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                response = await self.client.post(f"{self.base_url}/upload", files=files)

            assert response.status_code == 200
            data = response.json()
            assert "file_id" in data
            assert "validation_info" in data

            self.uploaded_files.append(data["file_id"])
            logger.info(f"File uploaded successfully: {data['file_id']}")

            # Test invalid file (wrong extension)
            with open("test_invalid.txt", "w") as f:
                f.write("This is not an Excel file")

            with open("test_invalid.txt", "rb") as f:
                files = {"file": ("test_invalid.txt", f, "text/plain")}
                response = await self.client.post(f"{self.base_url}/upload", files=files)

            assert response.status_code == 400
            logger.info("Invalid file correctly rejected")

        finally:
            # Clean up test files
            test_file_path.unlink(missing_ok=True)
            Path("test_invalid.txt").unlink(missing_ok=True)

    async def test_performance_monitoring(self):
        """Test performance monitoring features"""
        # Make several requests to generate metrics
        for _ in range(3):
            await self.client.get(f"{self.base_url}/health")

        # Check metrics endpoint
        response = await self.client.get(f"{self.base_url}/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "system_stats" in data
        assert "metrics_summary" in data
        assert "performance_report" in data

        # Verify system stats structure
        system_stats = data["system_stats"]
        expected_keys = ["cpu", "memory", "disk"]
        for key in expected_keys:
            assert key in system_stats, f"Missing system stat: {key}"

        logger.info("Performance monitoring validated")

    async def test_caching(self):
        """Test caching system"""
        if not self.uploaded_files:
            await self.test_file_upload()

        file_id = self.uploaded_files[0]

        # Make the same analysis request twice
        request_data = {
            "file_id": file_id,
            "analysis_types": ["rejections", "trends"]
        }

        # First request (cache miss)
        start_time = time.time()
        response1 = await self.client.post(f"{self.base_url}/analyze", json=request_data)
        first_duration = time.time() - start_time

        assert response1.status_code == 200

        # Second request (cache hit)
        start_time = time.time()
        response2 = await self.client.post(f"{self.base_url}/analyze", json=request_data)
        second_duration = time.time() - start_time

        assert response2.status_code == 200

        # Cache should make second request faster (though this is not guaranteed)
        logger.info(f"First request: {first_duration:.3f}s, Second request: {second_duration:.3f}s")

    async def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        # This is a basic test - in practice, we'd need to simulate failures
        response = await self.client.get(f"{self.base_url}/health")
        data = response.json()

        circuit_breakers = data.get("circuit_breakers", {})
        expected_breakers = ["excel_processing", "ai_insights", "database"]

        for breaker in expected_breakers:
            assert breaker in circuit_breakers, f"Missing circuit breaker: {breaker}"
            # All should be CLOSED (working) initially
            assert circuit_breakers[breaker] == "CLOSED", f"Circuit breaker {breaker} not closed"

        logger.info("Circuit breakers validated")

    async def test_analytics(self):
        """Test analytics engine"""
        if not self.uploaded_files:
            await self.test_file_upload()

        file_id = self.uploaded_files[0]

        request_data = {
            "file_id": file_id,
            "analysis_types": ["rejections", "trends", "patterns", "quality"]
        }

        response = await self.client.post(f"{self.base_url}/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert "summary" in data

        # Check that all requested analysis types are present
        results = data["results"]
        for analysis_type in request_data["analysis_types"]:
            assert any(analysis_type in str(result) for result in results), f"Missing analysis type: {analysis_type}"

        logger.info("Analytics engine validated")

    async def test_ai_insights(self):
        """Test AI insights generation"""
        if not self.uploaded_files:
            await self.test_file_upload()

        file_id = self.uploaded_files[0]

        request_data = {
            "file_id": file_id,
            "focus_area": "rejections"
        }

        response = await self.client.post(f"{self.base_url}/insights", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "insights" in data
        assert "recommendations" in data

        logger.info("AI insights generation validated")

    async def test_reporting(self):
        """Test report generation"""
        if not self.uploaded_files:
            await self.test_file_upload()

        file_id = self.uploaded_files[0]

        request_data = {
            "file_id": file_id,
            "report_type": "pdf",
            "include_charts": True
        }

        response = await self.client.post(f"{self.base_url}/reports/generate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "report_path" in data or "report_url" in data
        assert "format" in data

        logger.info("Report generation validated")

    async def test_error_handling(self):
        """Test error handling"""
        # Test with invalid file_id
        request_data = {
            "file_id": "invalid_id_12345",
            "analysis_types": ["rejections"]
        }

        response = await self.client.post(f"{self.base_url}/analyze", json=request_data)
        assert response.status_code in [400, 404, 500]  # Should handle error gracefully

        # Test malformed request
        response = await self.client.post(f"{self.base_url}/analyze", json={})
        assert response.status_code == 422  # Validation error

        logger.info("Error handling validated")

    async def test_metrics(self):
        """Test metrics collection"""
        # Generate some activity
        await self.client.get(f"{self.base_url}/health")
        await self.client.get(f"{self.base_url}/files")

        response = await self.client.get(f"{self.base_url}/metrics")
        assert response.status_code == 200

        data = response.json()

        # Check metrics structure
        assert "system_stats" in data
        assert "metrics_summary" in data
        assert "performance_report" in data

        # Check that some metrics were collected
        metrics = data["metrics_summary"]
        assert "counters" in metrics
        assert "gauges" in metrics

        logger.info("Metrics collection validated")

    async def cleanup_test_files(self):
        """Clean up uploaded test files"""
        for file_id in self.uploaded_files:
            try:
                response = await self.client.delete(f"{self.base_url}/files/{file_id}")
                if response.status_code == 200:
                    logger.info(f"Cleaned up file: {file_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up file {file_id}: {e}")

    def create_test_excel_data(self) -> pd.DataFrame:
        """Create test Excel data for healthcare claims"""
        return pd.DataFrame({
            'Claim_ID': [f'CLM_{i:06d}' for i in range(1, 101)],
            'Patient_ID': [f'PAT_{i:06d}' for i in range(1, 101)],
            'Provider_ID': [f'PRV_{(i % 20) + 1:03d}' for i in range(100)],
            'Service_Date': pd.date_range('2024-01-01', periods=100, freq='D'),
            'Diagnosis_Code': [f'ICD_{(i % 50) + 1:03d}' for i in range(100)],
            'Procedure_Code': [f'CPT_{(i % 30) + 1:05d}' for i in range(100)],
            'Claim_Amount': [round(100 + (i * 5.5), 2) for i in range(100)],
            'Approved_Amount': [round(80 + (i * 4.2), 2) for i in range(100)],
            'Status': ['Approved', 'Rejected', 'Pending'] * 33 + ['Approved'],
            'Rejection_Reason': ['Valid'] * 33 + ['Code Error'] * 33 + ['Missing Info'] * 34,
            'Processing_Date': pd.date_range('2024-01-15', periods=100, freq='D'),
        })

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            "test_suite": "Enhanced Tawnia Healthcare Analytics",
            "timestamp": time.time(),
            "total_tests": len(self.test_results),
            "passed": len([r for r in self.test_results if r["status"] == "PASSED"]),
            "failed": len([r for r in self.test_results if r["status"] == "FAILED"]),
            "results": self.test_results
        }

        # Save report
        report_path = Path("test_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Log summary
        logger.info("=" * 50)
        logger.info("TEST SUITE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {report['total_tests']}")
        logger.info(f"Passed: {report['passed']}")
        logger.info(f"Failed: {report['failed']}")
        success_rate = (report['passed'] / report['total_tests'] * 100) if report['total_tests'] > 0 else 0.0
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Report saved to: {report_path}")

        if report['failed'] > 0:
            logger.warning("FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    logger.error(f"  - {result['category']}: {result.get('error', 'Unknown error')}")


async def main():
    """Run the test suite"""
    tester = EnhancedSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
