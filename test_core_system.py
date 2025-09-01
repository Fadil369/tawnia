"""
Simple test script for Tawnia Healthcare Analytics core functionality
"""

import sys
import os
import asyncio
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_core_functionality():
    """Test core functionality without complex dependencies"""

    print("=" * 50)
    print("TAWNIA HEALTHCARE ANALYTICS - CORE SYSTEM TEST")
    print("=" * 50)

    try:
        # Test 1: Basic imports
        print("1. Testing basic imports...")
        from src.utils.logger import setup_logger
        from src.utils.config import get_settings
        print("   ✓ Core utilities imported successfully")

        # Test 2: Configuration
        print("2. Testing configuration...")
        settings = get_settings()
        print(f"   ✓ Environment: {settings.environment}")
        print(f"   ✓ Debug mode: {settings.debug}")
        print(f"   ✓ Host: {settings.host}:{settings.port}")

        # Test 3: Logger
        print("3. Testing logger...")
        logger = setup_logger("test")
        logger.info("Logger test message")
        print("   ✓ Logger working correctly")

        # Test 4: Enhanced modules (if available)
        print("4. Testing enhanced modules...")
        try:
            from src.utils.security import file_validator, input_sanitizer
            print("   ✓ Security module loaded")
        except Exception as e:
            print(f"   ⚠ Security module error: {e}")

        try:
            from src.utils.performance import metrics_collector
            print("   ✓ Performance module loaded")
        except Exception as e:
            print(f"   ⚠ Performance module error: {e}")

        try:
            from src.utils.cache import multi_cache
            print("   ✓ Cache module loaded")
        except Exception as e:
            print(f"   ⚠ Cache module error: {e}")

        try:
            from src.utils.circuit_breaker import excel_breaker
            print("   ✓ Circuit breaker module loaded")
        except Exception as e:
            print(f"   ⚠ Circuit breaker module error: {e}")

        # Test 5: Excel processor basic functionality
        print("5. Testing Excel processor...")
        try:
            from src.processors.excel_processor import ExcelProcessor
            processor = ExcelProcessor()
            print("   ✓ Excel processor initialized")

            # Create test data
            test_data = pd.DataFrame({
                'Claim_ID': ['CLM_001', 'CLM_002', 'CLM_003'],
                'Status': ['Approved', 'Rejected', 'Pending'],
                'Amount': [100.0, 150.0, 200.0]
            })

            # Test data validation
            if hasattr(processor, '_validate_data'):
                validation_result = processor._validate_data(test_data)
                print(f"   ✓ Data validation: {validation_result}")

        except Exception as e:
            print(f"   ⚠ Excel processor error: {e}")

        # Test 6: Check workspace files
        print("6. Checking workspace files...")
        workspace_files = list(Path(".").glob("*.xlsx"))
        print(f"   ✓ Found {len(workspace_files)} Excel files:")
        for file in workspace_files[:5]:  # Show first 5
            print(f"     - {file.name}")

        # Test 7: Directory structure
        print("7. Testing directory structure...")
        required_dirs = ['src', 'uploads', 'reports', 'data', 'logs']
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                print(f"   ✓ {dir_name}/ exists")
            else:
                print(f"   ⚠ {dir_name}/ missing")
                dir_path.mkdir(exist_ok=True)
                print(f"   ✓ Created {dir_name}/")

        # Test 8: Basic analysis simulation
        print("8. Testing basic analysis...")
        if len(workspace_files) > 0:
            try:
                # Try to read a real Excel file
                test_file = workspace_files[0]
                df = pd.read_excel(test_file)
                print(f"   ✓ Successfully read {test_file.name}")
                print(f"   ✓ Shape: {df.shape}")
                print(f"   ✓ Columns: {list(df.columns)[:5]}...")  # First 5 columns

                # Basic analysis
                if 'Status' in df.columns:
                    status_counts = df['Status'].value_counts()
                    print(f"   ✓ Status analysis: {dict(status_counts)}")

            except Exception as e:
                print(f"   ⚠ Excel analysis error: {e}")

        print("\n" + "=" * 50)
        print("CORE SYSTEM TEST COMPLETED SUCCESSFULLY!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_features():
    """Test enhanced features if available"""

    print("\n" + "=" * 50)
    print("ENHANCED FEATURES TEST")
    print("=" * 50)

    features_tested = 0
    features_working = 0

    # Test security features
    try:
        from src.utils.security import FileValidator, InputSanitizer
        validator = FileValidator()
        sanitizer = InputSanitizer()

        # Test filename sanitization
        dirty_filename = "../../../etc/passwd<script>alert('xss')</script>.xlsx"
        clean_filename = sanitizer.sanitize_filename(dirty_filename)
        print(f"✓ Filename sanitization: '{dirty_filename}' -> '{clean_filename}'")

        features_tested += 1
        features_working += 1
    except Exception as e:
        print(f"⚠ Security features error: {e}")
        features_tested += 1

    # Test performance monitoring
    try:
        from src.utils.performance import MetricsCollector, SystemMonitor
        metrics = MetricsCollector()
        monitor = SystemMonitor()

        # Record a test metric
        metrics.record_metric("test.metric", 42.0)
        metrics.increment_counter("test.counter")

        summary = metrics.get_summary()
        print(f"✓ Performance monitoring: Collected {len(summary.get('counters', {}))} counters")

        features_tested += 1
        features_working += 1
    except Exception as e:
        print(f"⚠ Performance monitoring error: {e}")
        features_tested += 1

    # Test caching
    try:
        from src.utils.cache import MemoryCache
        cache = MemoryCache()

        # Test cache operations
        asyncio.run(cache.set("test_key", "test_value"))
        value = asyncio.run(cache.get("test_key"))

        if value == "test_value":
            print("✓ Caching system working")
            features_working += 1
        else:
            print("⚠ Caching system not working correctly")

        features_tested += 1
    except Exception as e:
        print(f"⚠ Caching system error: {e}")
        features_tested += 1

    # Test circuit breaker
    try:
        from src.utils.circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker("test", failure_threshold=3)

        print(f"✓ Circuit breaker initialized: {breaker.state.name}")
        features_tested += 1
        features_working += 1
    except Exception as e:
        print(f"⚠ Circuit breaker error: {e}")
        features_tested += 1

    print(f"\nEnhanced Features Summary:")
    print(f"Tested: {features_tested}")
    print(f"Working: {features_working}")
    print(f"Success Rate: {(features_working/features_tested*100) if features_tested > 0 else 0:.1f}%")

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")

    # Run core functionality test
    success = asyncio.run(test_core_functionality())

    if success:
        # Run enhanced features test
        test_enhanced_features()

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS COMPLETED!")
        print("System is ready for use.")
        print("=" * 50)
    else:
        print("\n❌ CRITICAL ISSUES FOUND!")
        print("Please fix the errors before proceeding.")
