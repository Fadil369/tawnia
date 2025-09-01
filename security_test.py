#!/usr/bin/env python3
"""
Security Test Suite for Tawnia Healthcare Analytics
Validates security configurations and tests for common vulnerabilities
"""

import asyncio
import json
import time
import requests
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.security.security_config import get_security_config, reset_security_config
from src.security.middleware import RateLimiter, InputValidator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SecurityTestSuite:
    """Comprehensive security test suite"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results: List[Dict[str, Any]] = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests"""
        logger.info("Starting security test suite")
        
        test_methods = [
            self.test_security_headers,
            self.test_rate_limiting,
            self.test_input_validation,
            self.test_authentication,
            self.test_cors_configuration,
            self.test_file_upload_security,
            self.test_injection_protection,
            self.test_information_disclosure,
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"Running {test_method.__name__}")
                result = test_method()
                self.results.append(result)
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed: {str(e)}")
                self.results.append({
                    "test": test_method.__name__,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        return self.generate_report()
    
    def test_security_headers(self) -> Dict[str, Any]:
        """Test security headers implementation"""
        test_name = "Security Headers"
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            expected_headers = [
                "Content-Security-Policy",
                "Strict-Transport-Security", 
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Referrer-Policy"
            ]
            
            missing_headers = []
            for header in expected_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            if missing_headers:
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": f"Missing security headers: {missing_headers}",
                    "details": dict(headers)
                }
            
            # Check for secure values
            issues = []
            if "unsafe-eval" in headers.get("Content-Security-Policy", ""):
                issues.append("CSP allows unsafe-eval")
            
            if headers.get("X-Frame-Options") not in ["DENY", "SAMEORIGIN"]:
                issues.append("X-Frame-Options not properly configured")
            
            if issues:
                return {
                    "test": test_name,
                    "status": "WARN",
                    "message": f"Security header issues: {issues}",
                    "details": dict(headers)
                }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "All security headers properly configured"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality"""
        test_name = "Rate Limiting"
        
        try:
            # Test with rate limiter directly
            rate_limiter = RateLimiter(requests_per_minute=5, burst_limit=3)
            test_ip = "192.168.1.100"
            
            # Test burst limit
            allowed_count = 0
            for i in range(5):
                allowed, _ = rate_limiter.is_allowed(test_ip)
                if allowed:
                    allowed_count += 1
            
            if allowed_count > 3:
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": f"Burst limit not enforced: {allowed_count} requests allowed"
                }
            
            # Test rate limit recovery
            time.sleep(11)  # Wait for burst reset
            allowed, _ = rate_limiter.is_allowed(test_ip)
            
            if not allowed:
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Rate limit not properly reset"
                }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "Rate limiting working correctly"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation"""
        test_name = "Input Validation"
        
        try:
            validator = InputValidator()
            
            # Test content length validation
            class MockRequest:
                def __init__(self, headers):
                    self.headers = headers
            
            # Test oversized request
            large_request = MockRequest({"content-length": str(200 * 1024 * 1024)})  # 200MB
            if validator.validate_content_length(large_request, max_size_mb=100):
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Content length validation failed for oversized request"
                }
            
            # Test valid request
            normal_request = MockRequest({"content-length": str(10 * 1024 * 1024)})  # 10MB
            if not validator.validate_content_length(normal_request, max_size_mb=100):
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Content length validation failed for normal request"
                }
            
            # Test content type validation
            valid_json_request = MockRequest({"content-type": "application/json"})
            if not validator.validate_content_type(valid_json_request):
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Content type validation failed for valid JSON"
                }
            
            invalid_request = MockRequest({"content-type": "text/evil"})
            if validator.validate_content_type(invalid_request):
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Content type validation passed for invalid type"
                }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "Input validation working correctly"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_authentication(self) -> Dict[str, Any]:
        """Test authentication mechanisms"""
        test_name = "Authentication"
        
        try:
            # Test unauthenticated access to protected endpoint
            response = self.session.post(f"{self.base_url}/analyze")
            
            if response.status_code == 200:
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Protected endpoint accessible without authentication"
                }
            
            # Test with invalid token
            headers = {"Authorization": "Bearer invalid-token-12345"}
            response = self.session.post(f"{self.base_url}/analyze", headers=headers)
            
            if response.status_code == 200:
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Protected endpoint accessible with invalid token"
                }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "Authentication properly enforced"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration"""
        test_name = "CORS Configuration"
        
        try:
            # Test CORS headers
            headers = {"Origin": "https://evil.com"}
            response = self.session.options(f"{self.base_url}/health", headers=headers)
            
            cors_header = response.headers.get("Access-Control-Allow-Origin", "")
            
            # In production, this should not allow all origins
            if cors_header == "*":
                return {
                    "test": test_name,
                    "status": "WARN",
                    "message": "CORS allows all origins - configure for production"
                }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "CORS properly configured"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_file_upload_security(self) -> Dict[str, Any]:
        """Test file upload security"""
        test_name = "File Upload Security"
        
        try:
            # Test malicious file upload
            malicious_content = b"<?php system($_GET['cmd']); ?>"
            files = {"file": ("evil.php", malicious_content, "application/php")}
            
            response = self.session.post(f"{self.base_url}/upload", files=files)
            
            if response.status_code == 200:
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Malicious file upload was accepted"
                }
            
            # Test oversized file (simulate)
            large_file_data = b"A" * (100 * 1024 * 1024)  # 100MB
            files = {"file": ("large.xlsx", large_file_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            
            response = self.session.post(f"{self.base_url}/upload", files=files)
            
            if response.status_code == 200:
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Oversized file upload was accepted"
                }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "File upload security working correctly"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_injection_protection(self) -> Dict[str, Any]:
        """Test injection attack protection"""
        test_name = "Injection Protection"
        
        try:
            # Test SQL injection patterns
            sql_payloads = [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "UNION SELECT * FROM users"
            ]
            
            for payload in sql_payloads:
                response = self.session.get(f"{self.base_url}/health?search={payload}")
                if "error" in response.text.lower() and "sql" in response.text.lower():
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"SQL injection vulnerability detected with payload: {payload}"
                    }
            
            # Test XSS patterns
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>"
            ]
            
            for payload in xss_payloads:
                response = self.session.get(f"{self.base_url}/health?q={payload}")
                if payload in response.text:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"XSS vulnerability detected with payload: {payload}"
                    }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "Injection protection working correctly"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_information_disclosure(self) -> Dict[str, Any]:
        """Test for information disclosure"""
        test_name = "Information Disclosure"
        
        try:
            # Test for detailed error messages
            response = self.session.get(f"{self.base_url}/nonexistent-endpoint")
            
            if "traceback" in response.text.lower() or "exception" in response.text.lower():
                return {
                    "test": test_name,
                    "status": "FAIL",
                    "message": "Detailed error information exposed"
                }
            
            # Test server header disclosure
            server_header = response.headers.get("Server", "")
            if any(tech in server_header.lower() for tech in ["apache", "nginx", "iis"]):
                return {
                    "test": test_name,
                    "status": "WARN",
                    "message": f"Server technology disclosed: {server_header}"
                }
            
            return {
                "test": test_name,
                "status": "PASS",
                "message": "No information disclosure detected"
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        total_tests = len(self.results)
        passed = len([r for r in self.results if r.get("status") == "PASS"])
        failed = len([r for r in self.results if r.get("status") == "FAIL"])
        warnings = len([r for r in self.results if r.get("status") == "WARN"])
        errors = len([r for r in self.results if r.get("status") == "ERROR"])
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "errors": errors,
                "success_rate": f"{(passed / total_tests * 100):.1f}%" if total_tests > 0 else "0%"
            },
            "results": self.results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recommendations": self.get_recommendations()
        }
        
        return report
    
    def get_recommendations(self) -> List[str]:
        """Get security recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.get("status") == "FAIL"]
        warning_tests = [r for r in self.results if r.get("status") == "WARN"]
        
        if failed_tests:
            recommendations.append("CRITICAL: Address all failed security tests before production deployment")
        
        if warning_tests:
            recommendations.append("Review and address security warnings")
        
        # Always recommend these for production
        recommendations.extend([
            "Ensure JWT secret keys are properly configured for production",
            "Configure CORS origins to specific domains in production",
            "Enable HTTPS and security headers in production",
            "Implement proper monitoring and alerting for security events",
            "Regular security audits and penetration testing"
        ])
        
        return recommendations


def main():
    """Run security tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Test Suite")
    parser.add_argument("--url", default="http://127.0.0.1:3000", help="Base URL to test")
    parser.add_argument("--output", help="Output file for results")
    args = parser.parse_args()
    
    suite = SecurityTestSuite(args.url)
    report = suite.run_all_tests()
    
    # Print summary
    print("\n" + "="*50)
    print("SECURITY TEST REPORT")
    print("="*50)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Success Rate: {report['summary']['success_rate']}")
    
    # Print failed tests
    failed_tests = [r for r in report['results'] if r.get('status') == 'FAIL']
    if failed_tests:
        print("\nFAILED TESTS:")
        for test in failed_tests:
            print(f"  ❌ {test['test']}: {test['message']}")
    
    # Print warnings
    warning_tests = [r for r in report['results'] if r.get('status') == 'WARN']
    if warning_tests:
        print("\nWARNINGS:")
        for test in warning_tests:
            print(f"  ⚠️  {test['test']}: {test['message']}")
    
    # Print recommendations
    if report['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to {args.output}")
    
    # Exit with appropriate code
    if report['summary']['failed'] > 0:
        sys.exit(1)
    elif report['summary']['warnings'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()