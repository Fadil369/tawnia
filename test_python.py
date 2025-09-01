"""
Comprehensive test suite for Tawnia Healthcare Analytics Python version
"""

import asyncio
import pytest
import httpx
import tempfile
import os
from pathlib import Path
import pandas as pd
import json
from typing import Dict, Any

# Test configuration
TEST_BASE_URL = "http://localhost:3000"
TEST_TIMEOUT = 30


class TestHealthcareAnalytics:
    """Main test class for the healthcare analytics system"""

    @pytest.fixture(scope="session")
    def event_loop(self):
        """Create an instance of the default event loop for the test session."""
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture(scope="session")
    async def client(self):
        """Create an async HTTP client for testing"""
        async with httpx.AsyncClient(base_url=TEST_BASE_URL, timeout=TEST_TIMEOUT) as client:
            yield client

    @pytest.fixture
    def sample_excel_data(self):
        """Create sample healthcare claims data"""
        data = {
            'claim_id': [f'CLM{i:06d}' for i in range(1, 101)],
            'patient_id': [f'PAT{i:05d}' for i in range(1, 101)],
            'provider_id': [f'PRV{i:03d}' for i in range(1, 21)] * 5,
            'insurance_provider': ['Tawuniya', 'BUPA', 'AlRajhi Takaful'] * 33 + ['Tawuniya'],
            'claim_date': pd.date_range('2025-01-01', periods=100, freq='D'),
            'service_date': pd.date_range('2024-12-25', periods=100, freq='D'),
            'amount': [round(x, 2) for x in (1000 + 500 * pd.Series(range(100)).apply(lambda x: x % 10))],
            'status': ['approved'] * 70 + ['denied'] * 20 + ['pending'] * 10,
            'rejection_reason': [''] * 70 + ['invalid_procedure_code'] * 10 + ['missing_authorization'] * 10 + [''] * 10,
            'diagnosis_code': [f'D{i:03d}' for i in range(1, 101)],
            'procedure_code': [f'P{i:03d}' for i in range(1, 101)]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_excel_file(self, sample_excel_data):
        """Create a temporary Excel file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            sample_excel_data.to_excel(tmp.name, index=False)
            yield tmp.name
        os.unlink(tmp.name)

    # Health check tests
    async def test_health_check(self, client):
        """Test the health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "components" in data

        # Check all components are ready
        components = data["components"]
        assert components["excel_processor"] == "ready"
        assert components["analysis_engine"] == "ready"
        assert components["insights_generator"] == "ready"
        assert components["report_generator"] == "ready"

    # File upload tests
    async def test_single_file_upload(self, client, sample_excel_file):
        """Test uploading a single Excel file"""
        with open(sample_excel_file, 'rb') as f:
            files = {'file': ('test_claims.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = await client.post("/api/upload", files=files)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "file_id" in data
        assert data["filename"] == "test_claims.xlsx"
        assert "data_summary" in data
        assert "validation_results" in data

        # Check data summary
        summary = data["data_summary"]
        assert summary["total_records"] == 100
        assert len(summary["columns"]) > 0
        assert summary["file_type"] == ".xlsx"

        # Check validation results
        validation = data["validation_results"]
        assert "is_valid" in validation
        assert "quality_score" in validation
        assert 0 <= validation["quality_score"] <= 1

        return data["file_id"]

    async def test_file_upload_validation(self, client):
        """Test file upload validation"""
        # Test invalid file type
        files = {'file': ('test.txt', b'invalid content', 'text/plain')}
        response = await client.post("/api/upload", files=files)
        assert response.status_code == 400
        assert "only Excel" in response.json()["detail"].lower()

    async def test_multiple_file_upload(self, client, sample_excel_file):
        """Test uploading multiple files"""
        files = []
        for i in range(2):
            with open(sample_excel_file, 'rb') as f:
                content = f.read()
            files.append(('files', (f'test_claims_{i}.xlsx', content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')))

        response = await client.post("/api/upload/multiple", files=files)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        for result in data:
            assert result["success"] is True
            assert "file_id" in result

    # Analysis tests
    async def test_rejection_analysis(self, client, sample_excel_file):
        """Test rejection analysis"""
        # First upload a file
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        # Run rejection analysis
        request_data = {"file_ids": [file_id]}
        response = await client.post("/api/analyze/rejections", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["analysis_type"] == "rejections"
        assert "results" in data
        assert "timestamp" in data

        # Check results structure
        results = data["results"]
        assert "summary" in results
        assert "statistics" in results
        assert "insights" in results
        assert "recommendations" in results

        # Check summary content
        summary = results["summary"]
        assert "total_claims" in summary
        assert "total_rejections" in summary
        assert "rejection_rate" in summary

    async def test_trend_analysis(self, client, sample_excel_file):
        """Test trend analysis"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {"file_ids": [file_id]}
        response = await client.post("/api/analyze/trends", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["analysis_type"] == "trends"
        assert "results" in data

    async def test_pattern_analysis(self, client, sample_excel_file):
        """Test pattern analysis"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {"file_ids": [file_id]}
        response = await client.post("/api/analyze/patterns", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["analysis_type"] == "patterns"

    async def test_quality_analysis(self, client, sample_excel_file):
        """Test quality analysis"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {"file_ids": [file_id]}
        response = await client.post("/api/analyze/quality", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["analysis_type"] == "quality"

    async def test_comparison_analysis(self, client, sample_excel_file):
        """Test comparison analysis"""
        # Upload two files
        file_ids = []
        for i in range(2):
            file_id = await self.test_single_file_upload(client, sample_excel_file)
            file_ids.append(file_id)

        request_data = {"file_ids": file_ids}
        response = await client.post("/api/analyze/comparison", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["analysis_type"] == "comparison"

    async def test_comparison_analysis_insufficient_files(self, client, sample_excel_file):
        """Test comparison analysis with insufficient files"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {"file_ids": [file_id]}
        response = await client.post("/api/analyze/comparison", json=request_data)

        assert response.status_code == 400
        assert "at least 2 files" in response.json()["detail"].lower()

    # AI Insights tests
    async def test_insights_generation(self, client, sample_excel_file):
        """Test AI insights generation"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {
            "file_ids": [file_id],
            "analysis_type": "rejections"
        }
        response = await client.post("/api/insights", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "insights" in data
        assert "recommendations" in data
        assert "confidence_score" in data
        assert "source" in data
        assert "timestamp" in data

        # Check insights structure
        assert isinstance(data["insights"], list)
        assert isinstance(data["recommendations"], list)
        assert 0 <= data["confidence_score"] <= 1
        assert data["source"] in ["openai", "statistical"]

    async def test_insights_custom_prompt(self, client, sample_excel_file):
        """Test AI insights with custom prompt"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {
            "file_ids": [file_id],
            "custom_prompt": "Focus on financial impact of rejections"
        }
        response = await client.post("/api/insights", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    # Report generation tests
    async def test_pdf_report_generation(self, client, sample_excel_file):
        """Test PDF report generation"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {
            "file_ids": [file_id],
            "format": "pdf",
            "include_charts": True
        }
        response = await client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "report_id" in data
        assert "filename" in data
        assert data["format"] == "pdf"
        assert "download_url" in data
        assert "timestamp" in data

    async def test_excel_report_generation(self, client, sample_excel_file):
        """Test Excel report generation"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {
            "file_ids": [file_id],
            "format": "excel",
            "include_charts": True
        }
        response = await client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["format"] == "excel"

    async def test_json_report_generation(self, client, sample_excel_file):
        """Test JSON report generation"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {
            "file_ids": [file_id],
            "format": "json"
        }
        response = await client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["format"] == "json"

    async def test_csv_report_generation(self, client, sample_excel_file):
        """Test CSV report generation"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        request_data = {
            "file_ids": [file_id],
            "format": "csv"
        }
        response = await client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["format"] == "csv"

    async def test_report_download(self, client, sample_excel_file):
        """Test report download"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        # Generate report
        request_data = {
            "file_ids": [file_id],
            "format": "pdf"
        }
        response = await client.post("/api/reports/generate", json=request_data)
        report_data = response.json()
        report_id = report_data["report_id"]

        # Download report
        response = await client.get(f"/api/reports/download/{report_id}")
        assert response.status_code == 200
        assert len(response.content) > 0

    async def test_report_list(self, client, sample_excel_file):
        """Test listing reports"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        # Generate a report first
        request_data = {
            "file_ids": [file_id],
            "format": "pdf"
        }
        await client.post("/api/reports/generate", json=request_data)

        # List reports
        response = await client.get("/api/reports/list")
        assert response.status_code == 200

        data = response.json()
        assert "reports" in data
        assert isinstance(data["reports"], list)

    async def test_report_deletion(self, client, sample_excel_file):
        """Test report deletion"""
        file_id = await self.test_single_file_upload(client, sample_excel_file)

        # Generate report
        request_data = {
            "file_ids": [file_id],
            "format": "pdf"
        }
        response = await client.post("/api/reports/generate", json=request_data)
        report_data = response.json()
        report_id = report_data["report_id"]

        # Delete report
        response = await client.delete(f"/api/reports/{report_id}")
        assert response.status_code == 200

        data = response.json()
        assert "deleted successfully" in data["message"]

    # File management tests
    async def test_file_listing(self, client, sample_excel_file):
        """Test listing uploaded files"""
        await self.test_single_file_upload(client, sample_excel_file)

        response = await client.get("/api/files/list")
        assert response.status_code == 200

        data = response.json()
        assert "files" in data
        assert isinstance(data["files"], list)
        assert len(data["files"]) > 0

    async def test_file_deletion(self, client, sample_excel_file):
        """Test file deletion"""
        await self.test_single_file_upload(client, sample_excel_file)

        # Get file list to find a file to delete
        response = await client.get("/api/files/list")
        files = response.json()["files"]

        if files:
            filename = files[0]["filename"]
            response = await client.delete(f"/api/files/{filename}")
            assert response.status_code == 200

            data = response.json()
            assert "deleted successfully" in data["message"]

    # Error handling tests
    async def test_analysis_with_invalid_file_id(self, client):
        """Test analysis with invalid file ID"""
        request_data = {"file_ids": ["invalid-file-id"]}
        response = await client.post("/api/analyze/rejections", json=request_data)

        # Should handle gracefully (might return empty results or error)
        assert response.status_code in [200, 400, 500]

    async def test_insights_with_invalid_file_id(self, client):
        """Test insights with invalid file ID"""
        request_data = {"file_ids": ["invalid-file-id"]}
        response = await client.post("/api/insights", json=request_data)

        # Should handle gracefully
        assert response.status_code in [200, 400, 500]

    async def test_report_generation_with_invalid_file_id(self, client):
        """Test report generation with invalid file ID"""
        request_data = {"file_ids": ["invalid-file-id"], "format": "pdf"}
        response = await client.post("/api/reports/generate", json=request_data)

        # Should handle gracefully
        assert response.status_code in [200, 400, 500]

    async def test_nonexistent_report_download(self, client):
        """Test downloading non-existent report"""
        response = await client.get("/api/reports/download/nonexistent-report-id")
        assert response.status_code == 404

    async def test_nonexistent_file_deletion(self, client):
        """Test deleting non-existent file"""
        response = await client.delete("/api/files/nonexistent-file.xlsx")
        assert response.status_code == 404


# Performance tests
class TestPerformance:
    """Performance and load testing"""

    async def test_large_file_processing(self, client):
        """Test processing large files"""
        # Create a larger dataset
        large_data = {
            'claim_id': [f'CLM{i:06d}' for i in range(1, 1001)],  # 1000 records
            'amount': [1000 + (i % 100) * 10 for i in range(1000)],
            'status': ['approved'] * 800 + ['denied'] * 200
        }
        df = pd.DataFrame(large_data)

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False)

            try:
                with open(tmp.name, 'rb') as f:
                    files = {'file': ('large_test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    response = await client.post("/api/upload", files=files, timeout=60)

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data_summary"]["total_records"] == 1000

            finally:
                os.unlink(tmp.name)

    async def test_concurrent_requests(self, client, sample_excel_file):
        """Test handling concurrent requests"""
        # Upload a file first
        file_id = await TestHealthcareAnalytics().test_single_file_upload(client, sample_excel_file)

        # Make concurrent analysis requests
        tasks = []
        for analysis_type in ["rejections", "trends", "quality"]:
            request_data = {"file_ids": [file_id]}
            task = client.post(f"/api/analyze/{analysis_type}", json=request_data)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that all requests completed successfully
        for response in responses:
            if isinstance(response, Exception):
                pytest.fail(f"Request failed with exception: {response}")
            assert response.status_code == 200


# Integration tests
class TestIntegration:
    """End-to-end integration tests"""

    async def test_complete_workflow(self, client, sample_excel_file):
        """Test complete analysis workflow"""
        # 1. Upload file
        with open(sample_excel_file, 'rb') as f:
            files = {'file': ('workflow_test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = await client.post("/api/upload", files=files)

        assert response.status_code == 200
        file_id = response.json()["file_id"]

        # 2. Run multiple analyses
        analysis_types = ["rejections", "trends", "patterns", "quality"]
        for analysis_type in analysis_types:
            request_data = {"file_ids": [file_id]}
            response = await client.post(f"/api/analyze/{analysis_type}", json=request_data)
            assert response.status_code == 200

        # 3. Generate insights
        request_data = {"file_ids": [file_id], "analysis_type": "rejections"}
        response = await client.post("/api/insights", json=request_data)
        assert response.status_code == 200

        # 4. Generate reports in all formats
        formats = ["pdf", "excel", "json", "csv"]
        report_ids = []

        for format_type in formats:
            request_data = {
                "file_ids": [file_id],
                "format": format_type,
                "include_charts": True
            }
            response = await client.post("/api/reports/generate", json=request_data)
            assert response.status_code == 200
            report_ids.append(response.json()["report_id"])

        # 5. Download reports
        for report_id in report_ids:
            response = await client.get(f"/api/reports/download/{report_id}")
            assert response.status_code == 200
            assert len(response.content) > 0

        # 6. List files and reports
        response = await client.get("/api/files/list")
        assert response.status_code == 200

        response = await client.get("/api/reports/list")
        assert response.status_code == 200

        # 7. Cleanup
        for report_id in report_ids:
            await client.delete(f"/api/reports/{report_id}")


if __name__ == "__main__":
    """Run tests if script is executed directly"""
    import sys

    print("Tawnia Healthcare Analytics - Python Test Suite")
    print("=" * 50)

    # Check if server is running
    async def check_server():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{TEST_BASE_URL}/health", timeout=5)
                return response.status_code == 200
        except Exception:
            return False

    server_running = asyncio.run(check_server())

    if not server_running:
        print(f"ERROR: Server is not running at {TEST_BASE_URL}")
        print("Please start the server first with: python main.py")
        sys.exit(1)

    print(f"Server is running at {TEST_BASE_URL}")
    print("Running tests...")

    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])

    sys.exit(exit_code)
