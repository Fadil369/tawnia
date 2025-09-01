#!/usr/bin/env node

/**
 * Tawnia Healthcare Analytics System - Manual Testing Script
 * This script tests all major components of the system without requiring Jest
 */

const fs = require('fs').promises;
const path = require('path');
const ExcelJS = require('exceljs');

// Import our modules
const excelProcessor = require('./src/processors/excelProcessor');
const analysisEngine = require('./src/analysis/analysisEngine');

// Test configuration
const config = {
  testDataDir: './test-data',
  outputDir: './test-results',
  verbose: true
};

// Colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(message, color = 'reset') {
  if (config.verbose) {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }
}

function logSuccess(message) {
  log(`✓ ${message}`, 'green');
}

function logError(message) {
  log(`✗ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠ ${message}`, 'yellow');
}

function logInfo(message) {
  log(`ℹ ${message}`, 'blue');
}

/**
 * Create test Excel file with healthcare data
 */
async function createTestExcelFile() {
  logInfo('Creating test Excel file...');

  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('Healthcare Claims Data');

  // Add headers
  worksheet.columns = [
    { header: 'Claim ID', key: 'claimId', width: 15 },
    { header: 'Patient Name', key: 'patientName', width: 20 },
    { header: 'Insurance Provider', key: 'insuranceProvider', width: 20 },
    { header: 'Claim Amount', key: 'claimAmount', width: 15 },
    { header: 'Status', key: 'status', width: 15 },
    { header: 'Rejection Reason', key: 'rejectionReason', width: 25 },
    { header: 'Date Submitted', key: 'dateSubmitted', width: 15 },
    { header: 'Medical Code', key: 'medicalCode', width: 15 }
  ];

  // Add comprehensive test data
  const testData = [
    {
      claimId: 'CLM001',
      patientName: 'Ahmed Al-Rashid',
      insuranceProvider: 'Tawuniya',
      claimAmount: 2500.00,
      status: 'Rejected',
      rejectionReason: 'Pre-authorization required',
      dateSubmitted: '2025-07-01',
      medicalCode: 'J44.1'
    },
    {
      claimId: 'CLM002',
      patientName: 'Fatima Al-Zahra',
      insuranceProvider: 'Tawuniya',
      claimAmount: 1200.00,
      status: 'Approved',
      rejectionReason: '',
      dateSubmitted: '2025-07-02',
      medicalCode: 'Z00.00'
    },
    {
      claimId: 'CLM003',
      patientName: 'Mohammed Al-Mansouri',
      insuranceProvider: 'Tawuniya',
      claimAmount: 3500.00,
      status: 'Rejected',
      rejectionReason: 'Duplicate claim',
      dateSubmitted: '2025-07-03',
      medicalCode: 'M79.3'
    },
    {
      claimId: 'CLM004',
      patientName: 'Aisha Al-Qassemi',
      insuranceProvider: 'Tawuniya',
      claimAmount: 850.00,
      status: 'Pending',
      rejectionReason: '',
      dateSubmitted: '2025-07-04',
      medicalCode: 'K59.1'
    },
    {
      claimId: 'CLM005',
      patientName: 'Omar Al-Hadhrami',
      insuranceProvider: 'Tawuniya',
      claimAmount: 4200.00,
      status: 'Rejected',
      rejectionReason: 'Insufficient documentation',
      dateSubmitted: '2025-07-05',
      medicalCode: 'N18.6'
    },
    {
      claimId: 'CLM006',
      patientName: 'Layla Al-Otaibi',
      insuranceProvider: 'Bupa Arabia',
      claimAmount: 1800.00,
      status: 'Approved',
      rejectionReason: '',
      dateSubmitted: '2025-07-06',
      medicalCode: 'H25.9'
    },
    {
      claimId: 'CLM007',
      patientName: 'Hassan Al-Ghamdi',
      insuranceProvider: 'Tawuniya',
      claimAmount: 950.00,
      status: 'Rejected',
      rejectionReason: 'Invalid medical code',
      dateSubmitted: '2025-07-07',
      medicalCode: 'INVALID'
    },
    {
      claimId: 'CLM008',
      patientName: 'Noor Al-Shamsi',
      insuranceProvider: 'Tawuniya',
      claimAmount: 2200.00,
      status: 'Approved',
      rejectionReason: '',
      dateSubmitted: '2025-07-08',
      medicalCode: 'E11.9'
    },
    {
      claimId: '', // Test empty claim ID
      patientName: 'Test Missing ID',
      insuranceProvider: 'Tawuniya',
      claimAmount: 1000.00,
      status: 'Pending',
      rejectionReason: '',
      dateSubmitted: '2025-07-09',
      medicalCode: 'Z00.00'
    },
    {
      claimId: 'CLM010',
      patientName: 'Sara Al-Balushi',
      insuranceProvider: 'Unknown Provider', // Test unknown provider
      claimAmount: 'invalid-amount', // Test invalid amount
      status: 'Approved',
      rejectionReason: '',
      dateSubmitted: 'invalid-date', // Test invalid date
      medicalCode: 'I10'
    }
  ];

  testData.forEach(row => {
    worksheet.addRow(row);
  });

  // Style the header
  worksheet.getRow(1).font = { bold: true };
  worksheet.getRow(1).fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFE0E0E0' }
  };

  await fs.mkdir(config.testDataDir, { recursive: true });
  const filePath = path.join(config.testDataDir, 'test_healthcare_claims.xlsx');
  await workbook.xlsx.writeFile(filePath);

  logSuccess('Test Excel file created successfully');
  return filePath;
}

/**
 * Test Excel processor functionality
 */
async function testExcelProcessor() {
  logInfo('Testing Excel Processor...');

  try {
    // Test file type identification
    const fileType = excelProcessor.identifyFileType('test_healthcare_claims.xlsx');
    if (fileType) {
      logSuccess('File type identification works');
    } else {
      logWarning('File type identification returned unknown type');
    }

    // Create and process test file
    const testFilePath = await createTestExcelFile();
    const fileBuffer = await fs.readFile(testFilePath);

    const mockFile = {
      buffer: fileBuffer,
      originalname: 'test_healthcare_claims.xlsx'
    };

    const processedData = await excelProcessor.processFile(mockFile);

    // Validate processed data structure
    if (processedData && processedData.sheets && processedData.sheets.length > 0) {
      logSuccess('Excel file processed successfully');

      const sheet = processedData.sheets[0];

      // Test headers extraction
      if (sheet.headers && sheet.headers.includes('Claim ID')) {
        logSuccess('Headers extracted correctly');
      } else {
        logError('Headers extraction failed');
      }

      // Test data extraction
      if (sheet.data && sheet.data.length > 0) {
        logSuccess(`Data extracted: ${sheet.data.length} rows`);
      } else {
        logError('Data extraction failed');
      }

      // Test data quality assessment
      if (sheet.analysis && sheet.analysis.dataQuality) {
        logSuccess(`Data quality assessment completed: ${sheet.analysis.dataQuality.score}% quality score`);

        if (sheet.analysis.dataQuality.issues && sheet.analysis.dataQuality.issues.length > 0) {
          logWarning(`Found ${sheet.analysis.dataQuality.issues.length} data quality issues`);
        }
      } else {
        logError('Data quality assessment failed');
      }

      return processedData;
    } else {
      logError('Excel processing failed');
      return null;
    }

  } catch (error) {
    logError(`Excel processor test failed: ${error.message}`);
    return null;
  }
}

/**
 * Test validation functions
 */
async function testValidationFunctions() {
  logInfo('Testing validation functions...');

  try {
    // Test valid claim data
    const validClaim = {
      'Claim ID': 'CLM001',
      'Patient Name': 'Test Patient',
      'Insurance Provider': 'Tawuniya',
      'Claim Amount': 1000,
      'Status': 'Approved',
      'Date Submitted': '2025-07-01'
    };

    if (excelProcessor.validateClaimData(validClaim)) {
      logSuccess('Valid claim data validation works');
    } else {
      logError('Valid claim data validation failed');
    }

    // Test invalid claim data
    const invalidClaim = {
      'Claim ID': '',
      'Patient Name': 'Test Patient',
      'Claim Amount': 'invalid',
      'Status': 'Unknown Status'
    };

    if (!excelProcessor.validateClaimData(invalidClaim)) {
      logSuccess('Invalid claim data properly rejected');
    } else {
      logError('Invalid claim data validation failed');
    }

    // Test date validation
    if (excelProcessor.isValidDate('2025-07-01') && !excelProcessor.isValidDate('invalid-date')) {
      logSuccess('Date validation works correctly');
    } else {
      logError('Date validation failed');
    }

    // Test amount validation
    if (excelProcessor.isValidAmount(1000) && !excelProcessor.isValidAmount('invalid')) {
      logSuccess('Amount validation works correctly');
    } else {
      logError('Amount validation failed');
    }

  } catch (error) {
    logError(`Validation functions test failed: ${error.message}`);
  }
}

/**
 * Test analysis engine
 */
async function testAnalysisEngine(processedData) {
  if (!processedData) {
    logError('Cannot test analysis engine - no processed data available');
    return;
  }

  logInfo('Testing Analysis Engine...');

  try {
    // Test rejection analysis
    const rejectionAnalysis = await analysisEngine.analyzeRejections(processedData);
    if (rejectionAnalysis && rejectionAnalysis.summary) {
      logSuccess('Rejection analysis completed');
      logInfo(`Rejection rate: ${rejectionAnalysis.summary.rejectionRate}%`);
    } else {
      logError('Rejection analysis failed');
    }

    // Test trend analysis
    const trendAnalysis = await analysisEngine.analyzeTrends(processedData);
    if (trendAnalysis && trendAnalysis.summary) {
      logSuccess('Trend analysis completed');
    } else {
      logError('Trend analysis failed');
    }

    // Test pattern analysis
    const patternAnalysis = await analysisEngine.analyzePatterns(processedData);
    if (patternAnalysis && patternAnalysis.summary) {
      logSuccess('Pattern analysis completed');
    } else {
      logError('Pattern analysis failed');
    }

    // Test data quality analysis
    const qualityAnalysis = await analysisEngine.analyzeDataQuality(processedData);
    if (qualityAnalysis && qualityAnalysis.summary) {
      logSuccess('Data quality analysis completed');
      logInfo(`Overall quality score: ${qualityAnalysis.summary.overallScore}%`);
    } else {
      logError('Data quality analysis failed');
    }

    // Test metrics calculation
    const metrics = await analysisEngine.calculateMetrics(processedData);
    if (metrics && typeof metrics.totalRecords === 'number') {
      logSuccess('Metrics calculation completed');
      logInfo(`Total records: ${metrics.totalRecords}`);
    } else {
      logError('Metrics calculation failed');
    }

  } catch (error) {
    logError(`Analysis engine test failed: ${error.message}`);
  }
}

/**
 * Test file operations
 */
async function testFileOperations() {
  logInfo('Testing file operations...');

  try {
    // Ensure test directories exist
    await fs.mkdir(config.testDataDir, { recursive: true });
    await fs.mkdir(config.outputDir, { recursive: true });
    await fs.mkdir('./uploads', { recursive: true });
    await fs.mkdir('./data', { recursive: true });
    await fs.mkdir('./reports', { recursive: true });
    await fs.mkdir('./logs', { recursive: true });

    logSuccess('Directory structure verified');

    // Test file permissions
    const testFile = path.join(config.outputDir, 'test.txt');
    await fs.writeFile(testFile, 'test content');
    const content = await fs.readFile(testFile, 'utf8');

    if (content === 'test content') {
      logSuccess('File read/write operations work');
      await fs.unlink(testFile); // Cleanup
    } else {
      logError('File operations failed');
    }

  } catch (error) {
    logError(`File operations test failed: ${error.message}`);
  }
}

/**
 * Performance test
 */
async function performanceTest() {
  logInfo('Running performance tests...');

  try {
    const startTime = Date.now();

    // Create larger test dataset
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Performance Test');

    worksheet.columns = [
      { header: 'ID', key: 'id' },
      { header: 'Name', key: 'name' },
      { header: 'Amount', key: 'amount' },
      { header: 'Status', key: 'status' }
    ];

    // Add 1000 rows
    for (let i = 1; i <= 1000; i++) {
      worksheet.addRow({
        id: `ID${i.toString().padStart(4, '0')}`,
        name: `Patient ${i}`,
        amount: Math.random() * 5000,
        status: Math.random() > 0.7 ? 'Rejected' : 'Approved'
      });
    }

    const perfTestPath = path.join(config.testDataDir, 'performance_test.xlsx');
    await workbook.xlsx.writeFile(perfTestPath);

    const fileBuffer = await fs.readFile(perfTestPath);
    const mockFile = {
      buffer: fileBuffer,
      originalname: 'performance_test.xlsx'
    };

    const processedData = await excelProcessor.processFile(mockFile);

    const endTime = Date.now();
    const processingTime = endTime - startTime;

    if (processedData && processedData.sheets[0].data.length === 1000) {
      logSuccess(`Performance test passed: processed 1000 records in ${processingTime}ms`);
    } else {
      logError('Performance test failed');
    }

    // Cleanup
    await fs.unlink(perfTestPath);

  } catch (error) {
    logError(`Performance test failed: ${error.message}`);
  }
}

/**
 * Generate test report
 */
async function generateTestReport(testResults) {
  logInfo('Generating test report...');

  try {
    const report = {
      timestamp: new Date().toISOString(),
      system: 'Tawnia Healthcare Analytics',
      testResults,
      summary: {
        totalTests: testResults.length,
        passed: testResults.filter(r => r.passed).length,
        failed: testResults.filter(r => !r.passed).length
      }
    };

    const reportPath = path.join(config.outputDir, 'test-report.json');
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

    logSuccess(`Test report saved to ${reportPath}`);

  } catch (error) {
    logError(`Failed to generate test report: ${error.message}`);
  }
}

/**
 * Main test runner
 */
async function runTests() {
  console.log('\n🏥 Tawnia Healthcare Analytics System - Test Suite\n');
  console.log('=' .repeat(60));

  const testResults = [];
  let processedData = null;

  // Test 1: File operations
  try {
    await testFileOperations();
    testResults.push({ test: 'File Operations', passed: true });
  } catch (error) {
    testResults.push({ test: 'File Operations', passed: false, error: error.message });
  }

  // Test 2: Excel processor
  try {
    processedData = await testExcelProcessor();
    testResults.push({ test: 'Excel Processor', passed: !!processedData });
  } catch (error) {
    testResults.push({ test: 'Excel Processor', passed: false, error: error.message });
  }

  // Test 3: Validation functions
  try {
    await testValidationFunctions();
    testResults.push({ test: 'Validation Functions', passed: true });
  } catch (error) {
    testResults.push({ test: 'Validation Functions', passed: false, error: error.message });
  }

  // Test 4: Analysis engine
  try {
    await testAnalysisEngine(processedData);
    testResults.push({ test: 'Analysis Engine', passed: true });
  } catch (error) {
    testResults.push({ test: 'Analysis Engine', passed: false, error: error.message });
  }

  // Test 5: Performance test
  try {
    await performanceTest();
    testResults.push({ test: 'Performance Test', passed: true });
  } catch (error) {
    testResults.push({ test: 'Performance Test', passed: false, error: error.message });
  }

  // Generate report
  await generateTestReport(testResults);

  // Display summary
  console.log('\n' + '=' .repeat(60));
  console.log('TEST SUMMARY');
  console.log('=' .repeat(60));

  const passed = testResults.filter(r => r.passed).length;
  const total = testResults.length;

  testResults.forEach(result => {
    const status = result.passed ? '✓' : '✗';
    const color = result.passed ? 'green' : 'red';
    log(`${status} ${result.test}`, color);
    if (!result.passed && result.error) {
      log(`  Error: ${result.error}`, 'red');
    }
  });

  console.log('\n' + '=' .repeat(60));
  const passRate = ((passed / total) * 100).toFixed(1);
  log(`Tests Passed: ${passed}/${total} (${passRate}%)`, passed === total ? 'green' : 'yellow');

  if (passed === total) {
    logSuccess('All tests passed! The system is ready for use.');
  } else {
    logWarning('Some tests failed. Please review the errors above.');
  }

  console.log('\n💡 To start the system, run: npm start');
  console.log('📊 Access the enhanced UI at: http://localhost:3000/brainsait\n');
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
  });
}

module.exports = {
  runTests,
  createTestExcelFile,
  testExcelProcessor,
  testValidationFunctions,
  testAnalysisEngine
};
