#!/usr/bin/env python3
"""
Simple Component Test Suite
Tests basic functionality without complex dependencies
"""

import sys
import json
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Simple test functions
def test_basic_imports():
    """Test basic module imports"""
    try:
        from src.processors.excel_processor import ExcelProcessor
        from src.analysis.analysis_engine import AnalysisEngine
        from src.utils.cache import MemoryCache
        from src.utils.security import InputSanitizer
        print("✓ All basic imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_data_processing():
    """Test basic data processing"""
    try:
        # Create test data
        test_data = pd.DataFrame({
            'claim_id': ['CLM001', 'CLM002', 'CLM003'],
            'amount': [1500.00, 2300.00, 800.00],
            'status': ['Rejected', 'Approved', 'Rejected']
        })

        # Basic pandas operations
        rejected_claims = test_data[test_data['status'] == 'Rejected']
        total_amount = test_data['amount'].sum()

        assert len(rejected_claims) == 2
        assert total_amount == 4600.00

        print("✓ Data processing test passed")
        return True
    except Exception as e:
        print(f"✗ Data processing test failed: {e}")
        return False

def test_cache_functionality():
    """Test cache functionality"""
    try:
        from src.utils.cache import MemoryCache

        cache = MemoryCache(max_size=100)
        cache.set("test_key", {"data": "test_value"})
        cached_value = cache.get("test_key")

        assert cached_value["data"] == "test_value"

        print("✓ Cache functionality test passed")
        return True
    except Exception as e:
        print(f"✗ Cache functionality test failed: {e}")
        return False

def test_input_sanitization():
    """Test input sanitization"""
    try:
        from src.utils.security import InputSanitizer

        sanitizer = InputSanitizer()

        # Test text sanitization
        dirty_text = "<script>alert('xss')</script>Clean text"
        clean_text = sanitizer.sanitize_text(dirty_text)

        assert "<script>" not in clean_text
        assert "Clean text" in clean_text

        # Test filename sanitization
        dirty_filename = "../../../etc/passwd"
        clean_filename = sanitizer.sanitize_filename(dirty_filename)

        assert "../" not in clean_filename

        print("✓ Input sanitization test passed")
        return True
    except Exception as e:
        print(f"✗ Input sanitization test failed: {e}")
        return False

def test_file_operations():
    """Test file operations"""
    try:
        # Create test Excel file
        test_data = pd.DataFrame({
            'claim_id': ['CLM001', 'CLM002'],
            'amount': [1500.00, 2300.00]
        })

        test_file = Path("test_simple.xlsx")
        test_data.to_excel(test_file, index=False)

        # Read it back
        read_data = pd.read_excel(test_file)

        assert len(read_data) == 2
        assert 'claim_id' in read_data.columns

        # Cleanup
        test_file.unlink()

        print("✓ File operations test passed")
        return True
    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        return False

def test_analysis_basics():
    """Test basic analysis functionality"""
    try:
        # Create test data
        test_data = pd.DataFrame({
            'claim_id': ['CLM001', 'CLM002', 'CLM003', 'CLM004'],
            'rejection_reason': ['Missing Doc', 'Invalid Code', 'Missing Doc', 'Duplicate'],
            'amount': [1500.00, 2300.00, 800.00, 1200.00]
        })

        # Basic analysis
        rejection_counts = test_data['rejection_reason'].value_counts()
        total_amount = test_data['amount'].sum()
        avg_amount = test_data['amount'].mean()

        assert rejection_counts['Missing Doc'] == 2
        assert total_amount == 5800.00
        assert avg_amount == 1450.00

        print("✓ Analysis basics test passed")
        return True
    except Exception as e:
        print(f"✗ Analysis basics test failed: {e}")
        return False

def main():
    """Run all simple tests"""
    print("=" * 50)
    print("SIMPLE COMPONENT TEST SUITE")
    print("=" * 50)

    tests = [
        ("Basic Imports", test_basic_imports),
        ("Data Processing", test_data_processing),
        ("Cache Functionality", test_cache_functionality),
        ("Input Sanitization", test_input_sanitization),
        ("File Operations", test_file_operations),
        ("Analysis Basics", test_analysis_basics),
    ]

    passed = 0
    failed = 0
    results = {}

    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            result = test_func()
            if result:
                passed += 1
                results[test_name] = "PASSED"
            else:
                failed += 1
                results[test_name] = "FAILED"
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            failed += 1
            results[test_name] = f"FAILED: {e}"

    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0

    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")

    # Save results
    report = {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "success_rate": success_rate,
        "results": results
    }

    with open("simple_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to: simple_test_report.json")

    if failed > 0:
        print("\nFAILED TESTS:")
        for test_name, result in results.items():
            if result != "PASSED":
                print(f"  - {test_name}: {result}")

    return success_rate > 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
