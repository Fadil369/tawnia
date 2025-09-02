#!/usr/bin/env python3
"""
Integration Validation Script for Tawnia Healthcare Analytics
Tests the public folder integration and ensures all components work correctly.
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TawniaIntegrationValidator:
    """Validates the integration of the Tawnia Healthcare Analytics system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.public_dir = Path(__file__).parent / "public"
        self.results = {}
        self.start_time = time.time()
        
    def validate_file_structure(self) -> Dict[str, Any]:
        """Validate that all required files exist in the public directory."""
        logger.info("🔍 Validating file structure...")
        
        required_files = [
            "index.html",
            "brainsait-enhanced.html", 
            "insurance_verification.html",
            "sw.js",
            "js/app.js",
            "js/enhanced-app.js",
            "js/tawnia-navigation.js",
            "js/tawnia-components.js",
            "js/tawnia-integration-tests.js",
            "INTEGRATION-GUIDE.md"
        ]
        
        results = {
            "test_name": "File Structure Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        for file_path in required_files:
            full_path = self.public_dir / file_path
            exists = full_path.exists()
            file_size = full_path.stat().st_size if exists else 0
            
            results["details"][file_path] = {
                "exists": exists,
                "size_bytes": file_size,
                "readable": exists and os.access(full_path, os.R_OK)
            }
            
            if not exists:
                results["status"] = "FAIL"
                results["errors"].append(f"Missing file: {file_path}")
                
        logger.info(f"✅ File structure validation: {results['status']}")
        return results
    
    def validate_html_pages(self) -> Dict[str, Any]:
        """Validate that HTML pages load correctly and contain required elements."""
        logger.info("🌐 Validating HTML pages...")
        
        pages = [
            {"path": "/public/index.html", "name": "Portal"},
            {"path": "/public/brainsait-enhanced.html", "name": "Analytics Dashboard"},
            {"path": "/public/insurance_verification.html", "name": "Insurance Verification"}
        ]
        
        results = {
            "test_name": "HTML Pages Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        for page in pages:
            try:
                response = requests.get(f"{self.base_url}{page['path']}", timeout=10)
                
                page_result = {
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "has_navigation_script": "tawnia-navigation.js" in response.text,
                    "has_components_script": "tawnia-components.js" in response.text,
                    "has_integration_tests": "tawnia-integration-tests.js" in response.text,
                    "has_viewport_meta": '<meta name="viewport"' in response.text,
                    "has_csp_meta": 'Content-Security-Policy' in response.text
                }
                
                results["details"][page["name"]] = page_result
                
                if response.status_code != 200:
                    results["status"] = "FAIL"
                    results["errors"].append(f"{page['name']} returned status {response.status_code}")
                    
            except requests.RequestException as e:
                results["status"] = "FAIL"
                results["errors"].append(f"Failed to load {page['name']}: {str(e)}")
                results["details"][page["name"]] = {"error": str(e)}
                
        logger.info(f"✅ HTML pages validation: {results['status']}")
        return results
    
    def validate_javascript_files(self) -> Dict[str, Any]:
        """Validate JavaScript files for syntax and content."""
        logger.info("📜 Validating JavaScript files...")
        
        js_files = [
            {"path": "/public/js/app.js", "name": "Main App"},
            {"path": "/public/js/enhanced-app.js", "name": "Enhanced App"},
            {"path": "/public/js/tawnia-navigation.js", "name": "Navigation System"},
            {"path": "/public/js/tawnia-components.js", "name": "Shared Components"},
            {"path": "/public/js/tawnia-integration-tests.js", "name": "Integration Tests"}
        ]
        
        results = {
            "test_name": "JavaScript Files Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        for js_file in js_files:
            try:
                response = requests.get(f"{self.base_url}{js_file['path']}", timeout=10)
                
                js_result = {
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "has_class_definition": "class " in response.text,
                    "has_error_handling": "try {" in response.text or "catch" in response.text,
                    "has_dom_ready": "DOMContentLoaded" in response.text,
                    "has_comments": "//" in response.text or "/*" in response.text
                }
                
                # Specific validations
                if js_file["name"] == "Navigation System":
                    js_result["has_navigation_class"] = "TawniaNavigation" in response.text
                    js_result["has_keyboard_shortcuts"] = "keydown" in response.text
                    
                elif js_file["name"] == "Shared Components":
                    js_result["has_components_class"] = "TawniaComponents" in response.text
                    js_result["has_modal_component"] = "showModal" in response.text
                    
                elif js_file["name"] == "Integration Tests":
                    js_result["has_test_class"] = "TawniaIntegrationTests" in response.text
                    js_result["has_test_methods"] = "runTests" in response.text
                
                results["details"][js_file["name"]] = js_result
                
                if response.status_code != 200:
                    results["status"] = "FAIL"
                    results["errors"].append(f"{js_file['name']} returned status {response.status_code}")
                    
            except requests.RequestException as e:
                results["status"] = "FAIL"
                results["errors"].append(f"Failed to load {js_file['name']}: {str(e)}")
                results["details"][js_file["name"]] = {"error": str(e)}
                
        logger.info(f"✅ JavaScript files validation: {results['status']}")
        return results
    
    def validate_service_worker(self) -> Dict[str, Any]:
        """Validate service worker functionality."""
        logger.info("⚙️ Validating service worker...")
        
        results = {
            "test_name": "Service Worker Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        try:
            response = requests.get(f"{self.base_url}/public/sw.js", timeout=10)
            
            sw_result = {
                "status_code": response.status_code,
                "content_length": len(response.content),
                "has_install_event": "install" in response.text,
                "has_fetch_event": "fetch" in response.text,
                "has_cache_strategy": "cache" in response.text.lower(),
                "has_version_control": "version" in response.text.lower(),
                "has_all_pages_cached": all(page in response.text for page in [
                    "index.html", "brainsait-enhanced.html", "insurance_verification.html"
                ])
            }
            
            results["details"]["Service Worker"] = sw_result
            
            if response.status_code != 200:
                results["status"] = "FAIL"
                results["errors"].append(f"Service worker returned status {response.status_code}")
                
        except requests.RequestException as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Failed to load service worker: {str(e)}")
            results["details"]["Service Worker"] = {"error": str(e)}
            
        logger.info(f"✅ Service worker validation: {results['status']}")
        return results
    
    def validate_security_headers(self) -> Dict[str, Any]:
        """Validate security implementations."""
        logger.info("🔒 Validating security measures...")
        
        results = {
            "test_name": "Security Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        # Check for XSS protection in JavaScript files
        js_files = ["app.js", "enhanced-app.js", "tawnia-components.js"]
        
        for js_file in js_files:
            try:
                response = requests.get(f"{self.base_url}/public/js/{js_file}", timeout=10)
                
                security_checks = {
                    "has_sanitization": "sanitize" in response.text.lower() or "textContent" in response.text,
                    "has_validation": "validate" in response.text.lower(),
                    "no_eval_usage": "eval(" not in response.text,
                    "no_innerhtml_direct": ".innerHTML =" not in response.text,
                    "has_csp_compliance": "unsafe-inline" not in response.text
                }
                
                results["details"][js_file] = security_checks
                
                # Check for security violations
                if not security_checks["no_eval_usage"]:
                    results["status"] = "FAIL"
                    results["errors"].append(f"{js_file} contains eval() usage")
                    
            except requests.RequestException as e:
                results["errors"].append(f"Failed to check {js_file}: {str(e)}")
        
        logger.info(f"✅ Security validation: {results['status']}")
        return results
    
    def validate_performance(self) -> Dict[str, Any]:
        """Validate performance metrics."""
        logger.info("⚡ Validating performance...")
        
        results = {
            "test_name": "Performance Validation", 
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        pages = [
            "/public/index.html",
            "/public/brainsait-enhanced.html",
            "/public/insurance_verification.html"
        ]
        
        for page in pages:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{page}", timeout=10)
                load_time = time.time() - start_time
                
                page_name = page.split("/")[-1].replace(".html", "")
                
                perf_result = {
                    "load_time_ms": round(load_time * 1000, 2),
                    "size_kb": round(len(response.content) / 1024, 2),
                    "status_code": response.status_code,
                    "has_compression": "gzip" in response.headers.get("content-encoding", ""),
                    "has_cache_headers": "cache-control" in response.headers
                }
                
                results["details"][page_name] = perf_result
                
                # Performance thresholds
                if load_time > 2.0:  # 2 seconds
                    results["status"] = "WARN"
                    results["errors"].append(f"{page_name} load time exceeds 2s: {load_time:.2f}s")
                    
                if len(response.content) > 1024 * 1024:  # 1MB
                    results["status"] = "WARN"
                    results["errors"].append(f"{page_name} size exceeds 1MB: {perf_result['size_kb']}KB")
                    
            except requests.RequestException as e:
                results["status"] = "FAIL"
                results["errors"].append(f"Failed to test {page}: {str(e)}")
        
        logger.info(f"✅ Performance validation: {results['status']}")
        return results
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests and generate comprehensive report."""
        logger.info("🚀 Starting comprehensive integration validation...")
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        
        # Run all validation tests
        validations = [
            self.validate_file_structure,
            self.validate_html_pages,
            self.validate_javascript_files,
            self.validate_service_worker,
            self.validate_security_headers,
            self.validate_performance
        ]
        
        for validation in validations:
            try:
                result = validation()
                validation_results["tests"].append(result)
                validation_results["summary"]["total_tests"] += 1
                
                if result["status"] == "PASS":
                    validation_results["summary"]["passed"] += 1
                elif result["status"] == "FAIL":
                    validation_results["summary"]["failed"] += 1
                elif result["status"] == "WARN":
                    validation_results["summary"]["warnings"] += 1
                    
            except Exception as e:
                logger.error(f"Validation failed: {str(e)}")
                validation_results["tests"].append({
                    "test_name": validation.__name__,
                    "status": "ERROR",
                    "error": str(e)
                })
                validation_results["summary"]["failed"] += 1
                validation_results["summary"]["total_tests"] += 1
        
        # Calculate execution time
        validation_results["execution_time_seconds"] = round(time.time() - self.start_time, 2)
        
        # Generate final status
        if validation_results["summary"]["failed"] > 0:
            validation_results["overall_status"] = "FAILED"
        elif validation_results["summary"]["warnings"] > 0:
            validation_results["overall_status"] = "PASSED_WITH_WARNINGS"
        else:
            validation_results["overall_status"] = "PASSED"
        
        return validation_results
    
    def generate_report(self, results: Dict[str, Any], output_file: str = None) -> str:
        """Generate a comprehensive validation report."""
        
        if output_file is None:
            output_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Save JSON report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Generate human-readable summary
        report = []
        report.append("=" * 80)
        report.append("🏥 TAWNIA HEALTHCARE ANALYTICS - INTEGRATION VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {results['timestamp']}")
        report.append(f"Base URL: {results['base_url']}")
        report.append(f"Execution Time: {results['execution_time_seconds']}s")
        report.append(f"Overall Status: {results['overall_status']}")
        report.append("")
        
        # Summary
        summary = results['summary']
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tests: {summary['total_tests']}")
        report.append(f"✅ Passed: {summary['passed']}")
        report.append(f"❌ Failed: {summary['failed']}")
        report.append(f"⚠️  Warnings: {summary['warnings']}")
        report.append("")
        
        # Detailed results
        report.append("📋 DETAILED RESULTS")
        report.append("-" * 40)
        
        for test in results['tests']:
            status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "ERROR": "💥"}
            emoji = status_emoji.get(test['status'], "❓")
            
            report.append(f"{emoji} {test['test_name']}: {test['status']}")
            
            if test.get('errors'):
                for error in test['errors']:
                    report.append(f"   - {error}")
            
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        
        if results['overall_status'] == "PASSED":
            report.append("🎉 All tests passed! The integration is working correctly.")
            report.append("🚀 Ready for production deployment.")
        else:
            report.append("🔧 Please address the failed tests before deployment.")
            report.append("📖 Refer to INTEGRATION-GUIDE.md for troubleshooting.")
        
        report.append("")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save text report
        text_output_file = output_file.replace('.json', '.txt')
        with open(text_output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"📄 Reports saved: {output_file}, {text_output_file}")
        return report_text

def main():
    """Main function to run integration validation."""
    
    print("🏥 Tawnia Healthcare Analytics - Integration Validator")
    print("=" * 60)
    
    # Check if server is running
    try:
        requests.get("http://localhost:8000", timeout=5)
        print("✅ Server detected on http://localhost:8000")
    except requests.RequestException:
        print("❌ Server not running on http://localhost:8000")
        print("💡 Please start the server with: python -m http.server 8000")
        return
    
    # Run validation
    validator = TawniaIntegrationValidator()
    results = validator.run_all_validations()
    
    # Generate and display report
    report = validator.generate_report(results)
    print(report)
    
    # Return appropriate exit code
    if results['overall_status'] == "FAILED":
        exit(1)
    elif results['overall_status'] == "PASSED_WITH_WARNINGS":
        exit(2)
    else:
        exit(0)

if __name__ == "__main__":
    main()