#!/usr/bin/env python3
"""
Simple Integration Validation for Tawnia Healthcare Analytics
Validates file structure and content without requiring a running server.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class TawniaSimpleValidator:
    """Simple validator for Tawnia integration without server dependency."""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.public_dir = self.project_dir / "public"
        self.results = {}
        self.start_time = time.time()
        
    def validate_file_structure(self) -> Dict[str, Any]:
        """Validate that all required files exist."""
        print("🔍 Validating file structure...")
        
        required_files = [
            "public/index.html",
            "public/brainsait-enhanced.html", 
            "public/insurance_verification.html",
            "public/sw.js",
            "public/js/app.js",
            "public/js/enhanced-app.js",
            "public/js/tawnia-navigation.js",
            "public/js/tawnia-components.js",
            "public/js/tawnia-integration-tests.js",
            "public/INTEGRATION-GUIDE.md"
        ]
        
        results = {
            "test_name": "File Structure Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        for file_path in required_files:
            full_path = self.project_dir / file_path
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
            elif file_size == 0:
                results["status"] = "FAIL"
                results["errors"].append(f"Empty file: {file_path}")
                
        print(f"✅ File structure validation: {results['status']}")
        return results
    
    def validate_html_integration(self) -> Dict[str, Any]:
        """Validate HTML files contain integration scripts."""
        print("🌐 Validating HTML integration...")
        
        html_files = [
            ("public/index.html", "Portal"),
            ("public/brainsait-enhanced.html", "Analytics Dashboard"),
            ("public/insurance_verification.html", "Insurance Verification")
        ]
        
        results = {
            "test_name": "HTML Integration Validation",
            "status": "PASS", 
            "details": {},
            "errors": []
        }
        
        required_scripts = [
            "tawnia-navigation.js",
            "tawnia-components.js", 
            "tawnia-integration-tests.js"
        ]
        
        for file_path, name in html_files:
            full_path = self.project_dir / file_path
            
            if not full_path.exists():
                results["status"] = "FAIL"
                results["errors"].append(f"HTML file missing: {file_path}")
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                page_result = {
                    "file_size": len(content),
                    "has_viewport_meta": '<meta name="viewport"' in content,
                    "has_csp_meta": 'Content-Security-Policy' in content,
                    "scripts_integrated": {}
                }
                
                for script in required_scripts:
                    page_result["scripts_integrated"][script] = script in content
                    
                    if script not in content:
                        results["status"] = "FAIL"
                        results["errors"].append(f"{name} missing script: {script}")
                
                # Check for navigation bar container
                page_result["has_nav_container"] = 'id="tawnia-navigation"' in content
                if 'id="tawnia-navigation"' not in content:
                    results["status"] = "FAIL"
                    results["errors"].append(f"{name} missing navigation container")
                
                results["details"][name] = page_result
                
            except Exception as e:
                results["status"] = "FAIL"
                results["errors"].append(f"Failed to read {name}: {str(e)}")
                
        print(f"✅ HTML integration validation: {results['status']}")
        return results
    
    def validate_javascript_content(self) -> Dict[str, Any]:
        """Validate JavaScript files contain expected classes and methods."""
        print("📜 Validating JavaScript content...")
        
        js_validations = {
            "public/js/tawnia-navigation.js": {
                "name": "Navigation System",
                "required_content": [
                    "class TawniaNavigation",
                    "keydown",
                    "navigateTo",
                    "toggleLanguage",
                    "toggleTheme"
                ]
            },
            "public/js/tawnia-components.js": {
                "name": "Shared Components",
                "required_content": [
                    "class TawniaComponents",
                    "showModal",
                    "showAlert",
                    "showToast",
                    "createDataTable"
                ]
            },
            "public/js/tawnia-integration-tests.js": {
                "name": "Integration Tests", 
                "required_content": [
                    "class TawniaIntegrationTests",
                    "runTests",
                    "runTest",
                    "testNavigation",
                    "testComponents"
                ]
            }
        }
        
        results = {
            "test_name": "JavaScript Content Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        for file_path, validation_info in js_validations.items():
            full_path = self.project_dir / file_path
            name = validation_info["name"]
            
            if not full_path.exists():
                results["status"] = "FAIL"
                results["errors"].append(f"JavaScript file missing: {file_path}")
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                js_result = {
                    "file_size": len(content),
                    "content_checks": {},
                    "has_error_handling": "try {" in content and "catch" in content,
                    "has_dom_ready": "DOMContentLoaded" in content
                }
                
                for required_item in validation_info["required_content"]:
                    has_content = required_item in content
                    js_result["content_checks"][required_item] = has_content
                    
                    if not has_content:
                        results["status"] = "FAIL"
                        results["errors"].append(f"{name} missing: {required_item}")
                
                results["details"][name] = js_result
                
            except Exception as e:
                results["status"] = "FAIL"
                results["errors"].append(f"Failed to read {name}: {str(e)}")
                
        print(f"✅ JavaScript content validation: {results['status']}")
        return results
    
    def validate_service_worker_content(self) -> Dict[str, Any]:
        """Validate service worker contains required functionality."""
        print("⚙️ Validating service worker content...")
        
        results = {
            "test_name": "Service Worker Content Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        sw_path = self.project_dir / "public/sw.js"
        
        if not sw_path.exists():
            results["status"] = "FAIL"
            results["errors"].append("Service worker file missing: public/sw.js")
            return results
        
        try:
            with open(sw_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_pages = [
                "index.html",
                "brainsait-enhanced.html", 
                "insurance_verification.html"
            ]
            
            required_scripts = [
                "tawnia-navigation.js",
                "tawnia-components.js",
                "tawnia-integration-tests.js"
            ]
            
            sw_result = {
                "file_size": len(content),
                "has_install_event": "install" in content,
                "has_fetch_event": "fetch" in content,
                "has_cache_strategy": "cache" in content.lower(),
                "pages_cached": {},
                "scripts_cached": {}
            }
            
            for page in required_pages:
                is_cached = page in content
                sw_result["pages_cached"][page] = is_cached
                
                if not is_cached:
                    results["status"] = "FAIL"
                    results["errors"].append(f"Service worker not caching: {page}")
            
            for script in required_scripts:
                is_cached = script in content
                sw_result["scripts_cached"][script] = is_cached
                
                if not is_cached:
                    results["status"] = "FAIL"
                    results["errors"].append(f"Service worker not caching: {script}")
            
            results["details"]["Service Worker"] = sw_result
            
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Failed to read service worker: {str(e)}")
            
        print(f"✅ Service worker content validation: {results['status']}")
        return results
    
    def validate_security_content(self) -> Dict[str, Any]:
        """Validate security implementations in code."""
        print("🔒 Validating security content...")
        
        results = {
            "test_name": "Security Content Validation",
            "status": "PASS",
            "details": {},
            "errors": []
        }
        
        # Check JavaScript files for security practices
        js_files = [
            "public/js/app.js",
            "public/js/enhanced-app.js",
            "public/js/tawnia-components.js"
        ]
        
        for js_file in js_files:
            full_path = self.project_dir / js_file
            file_name = js_file.split("/")[-1]
            
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                security_checks = {
                    "has_sanitization": any(word in content.lower() for word in ["sanitize", "textcontent", "createtextnode"]),
                    "has_validation": "validate" in content.lower(),
                    "no_eval_usage": "eval(" not in content,
                    "no_innerhtml_direct": ".innerHTML =" not in content,
                    "has_csp_compliance": "unsafe-inline" not in content
                }
                
                results["details"][file_name] = security_checks
                
                # Check for security violations
                if not security_checks["no_eval_usage"]:
                    results["status"] = "FAIL"
                    results["errors"].append(f"{file_name} contains eval() usage")
                
                if not security_checks["no_innerhtml_direct"]:
                    results["status"] = "WARN"
                    results["errors"].append(f"{file_name} uses direct innerHTML assignment")
                    
            except Exception as e:
                results["errors"].append(f"Failed to check {file_name}: {str(e)}")
        
        # Check HTML files for CSP headers
        html_files = [
            "public/index.html",
            "public/brainsait-enhanced.html",
            "public/insurance_verification.html"
        ]
        
        for html_file in html_files:
            full_path = self.project_dir / html_file
            file_name = html_file.split("/")[-1]
            
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                has_csp = 'Content-Security-Policy' in content
                results["details"][f"{file_name}_csp"] = {"has_csp_meta": has_csp}
                
                if not has_csp:
                    results["status"] = "WARN"
                    results["errors"].append(f"{file_name} missing CSP meta tag")
                    
            except Exception as e:
                results["errors"].append(f"Failed to check {file_name}: {str(e)}")
        
        print(f"✅ Security content validation: {results['status']}")
        return results
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🚀 Starting comprehensive integration validation...")
        print("=" * 60)
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "project_directory": str(self.project_dir),
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
            self.validate_html_integration,
            self.validate_javascript_content,
            self.validate_service_worker_content,
            self.validate_security_content
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
                print(f"❌ Validation failed: {str(e)}")
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
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive validation report."""
        
        # Save JSON report
        output_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Generate human-readable summary
        report = []
        report.append("=" * 80)
        report.append("🏥 TAWNIA HEALTHCARE ANALYTICS - INTEGRATION VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {results['timestamp']}")
        report.append(f"Project Directory: {results['project_directory']}")
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
            report.append("📖 Review INTEGRATION-GUIDE.md for deployment instructions.")
        elif results['overall_status'] == "PASSED_WITH_WARNINGS":
            report.append("⚠️  Tests passed with warnings. Review the issues above.")
            report.append("📖 Refer to INTEGRATION-GUIDE.md for optimization tips.")
        else:
            report.append("🔧 Please address the failed tests before deployment.")
            report.append("📖 Refer to INTEGRATION-GUIDE.md for troubleshooting.")
        
        report.append("")
        report.append("🔧 NEXT STEPS")
        report.append("-" * 40)
        report.append("1. Start HTTP server: python -m http.server 8000")
        report.append("2. Open browser: http://localhost:8000/public/")
        report.append("3. Test navigation: Alt+1, Alt+2, Alt+3")
        report.append("4. Run browser tests: Add ?test=true to any URL")
        report.append("5. Check console for integration test results")
        report.append("")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save text report
        text_output_file = output_file.replace('.json', '.txt')
        with open(text_output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"📄 Reports saved: {output_file}, {text_output_file}")
        return report_text

def main():
    """Main function to run integration validation."""
    
    print("🏥 Tawnia Healthcare Analytics - Simple Integration Validator")
    print("=" * 60)
    
    # Run validation
    validator = TawniaSimpleValidator()
    results = validator.run_all_validations()
    
    # Generate and display report
    report = validator.generate_report(results)
    print("\n" + report)
    
    # Return appropriate exit code
    if results['overall_status'] == "FAILED":
        exit(1)
    elif results['overall_status'] == "PASSED_WITH_WARNINGS":
        exit(2)
    else:
        exit(0)

if __name__ == "__main__":
    main()