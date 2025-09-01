const { createTestExcelFile } = require('./api.test');
const excelProcessor = require('../src/processors/excelProcessor');
const analysisEngine = require('../src/analysis/analysisEngine');

describe('Excel Processor Tests', () => {
  let testFileBuffer;
  let processedData;

  beforeAll(async () => {
    testFileBuffer = await createTestExcelFile();
  });

  test('should identify Excel file type correctly', async () => {
    const result = excelProcessor.identifyFileType('test.xlsx');
    expect(result).toBe('excel');
  });

  test('should process Excel file and extract data', async () => {
    const tempFile = {
      buffer: testFileBuffer,
      originalname: 'test_healthcare_data.xlsx'
    };

    processedData = await excelProcessor.processFile(tempFile);

    expect(processedData).toHaveProperty('filename');
    expect(processedData).toHaveProperty('fileType');
    expect(processedData).toHaveProperty('sheets');
    expect(Array.isArray(processedData.sheets)).toBe(true);
    expect(processedData.sheets.length).toBeGreaterThan(0);
  });

  test('should extract headers correctly', () => {
    const sheet = processedData.sheets[0];
    expect(sheet).toHaveProperty('headers');
    expect(sheet.headers).toContain('Claim ID');
    expect(sheet.headers).toContain('Patient Name');
    expect(sheet.headers).toContain('Insurance Provider');
  });

  test('should extract data rows correctly', () => {
    const sheet = processedData.sheets[0];
    expect(sheet).toHaveProperty('data');
    expect(Array.isArray(sheet.data)).toBe(true);
    expect(sheet.data.length).toBeGreaterThan(0);

    const firstRow = sheet.data[0];
    expect(firstRow).toHaveProperty('Claim ID');
    expect(firstRow).toHaveProperty('Status');
  });

  test('should perform data quality assessment', () => {
    const sheet = processedData.sheets[0];
    expect(sheet).toHaveProperty('analysis');
    expect(sheet.analysis).toHaveProperty('dataQuality');
    expect(sheet.analysis.dataQuality).toHaveProperty('score');
    expect(typeof sheet.analysis.dataQuality.score).toBe('number');
  });

  test('should handle missing values correctly', () => {
    const sheet = processedData.sheets[0];
    const qualityAnalysis = sheet.analysis.dataQuality;

    expect(qualityAnalysis).toHaveProperty('missingValues');
    expect(qualityAnalysis).toHaveProperty('completeness');
  });
});

describe('Analysis Engine Tests', () => {
  let testData;

  beforeAll(async () => {
    const testFileBuffer = await createTestExcelFile();
    const tempFile = {
      buffer: testFileBuffer,
      originalname: 'test_analysis.xlsx'
    };
    testData = await excelProcessor.processFile(tempFile);
  });

  test('should analyze rejections correctly', async () => {
    const rejectionAnalysis = await analysisEngine.analyzeRejections(testData);

    expect(rejectionAnalysis).toHaveProperty('summary');
    expect(rejectionAnalysis).toHaveProperty('details');
    expect(rejectionAnalysis.summary).toHaveProperty('totalRejections');
    expect(rejectionAnalysis.summary).toHaveProperty('rejectionRate');
  });

  test('should analyze trends correctly', async () => {
    const trendAnalysis = await analysisEngine.analyzeTrends(testData);

    expect(trendAnalysis).toHaveProperty('summary');
    expect(trendAnalysis).toHaveProperty('trends');
    expect(Array.isArray(trendAnalysis.trends)).toBe(true);
  });

  test('should find patterns correctly', async () => {
    const patternAnalysis = await analysisEngine.analyzePatterns(testData);

    expect(patternAnalysis).toHaveProperty('summary');
    expect(patternAnalysis).toHaveProperty('patterns');
    expect(Array.isArray(patternAnalysis.patterns)).toBe(true);
  });

  test('should assess data quality correctly', async () => {
    const qualityAnalysis = await analysisEngine.analyzeDataQuality(testData);

    expect(qualityAnalysis).toHaveProperty('summary');
    expect(qualityAnalysis.summary).toHaveProperty('overallScore');
    expect(qualityAnalysis.summary).toHaveProperty('issues');
    expect(typeof qualityAnalysis.summary.overallScore).toBe('number');
  });

  test('should calculate metrics correctly', async () => {
    const metrics = await analysisEngine.calculateMetrics(testData);

    expect(metrics).toHaveProperty('totalRecords');
    expect(metrics).toHaveProperty('rejectionRate');
    expect(metrics).toHaveProperty('averageClaimAmount');
    expect(typeof metrics.totalRecords).toBe('number');
    expect(typeof metrics.rejectionRate).toBe('number');
  });

  test('should perform comparative analysis', async () => {
    const comparison = await analysisEngine.performComparison([testData, testData]);

    expect(comparison).toHaveProperty('summary');
    expect(comparison).toHaveProperty('differences');
    expect(comparison).toHaveProperty('similarities');
  });
});

describe('Data Validation Tests', () => {
  test('should validate claim data structure', () => {
    const validClaim = {
      'Claim ID': 'CLM001',
      'Patient Name': 'Test Patient',
      'Insurance Provider': 'Tawuniya',
      'Claim Amount': 1000,
      'Status': 'Approved',
      'Date Submitted': '2025-07-01'
    };

    const isValid = excelProcessor.validateClaimData(validClaim);
    expect(isValid).toBe(true);
  });

  test('should reject invalid claim data', () => {
    const invalidClaim = {
      'Claim ID': '', // Empty claim ID
      'Patient Name': 'Test Patient',
      'Claim Amount': 'invalid', // Invalid amount
      'Status': 'Unknown Status' // Invalid status
    };

    const isValid = excelProcessor.validateClaimData(invalidClaim);
    expect(isValid).toBe(false);
  });

  test('should validate date formats', () => {
    const validDate = '2025-07-01';
    const invalidDate = 'invalid-date';

    expect(excelProcessor.isValidDate(validDate)).toBe(true);
    expect(excelProcessor.isValidDate(invalidDate)).toBe(false);
  });

  test('should validate claim amounts', () => {
    expect(excelProcessor.isValidAmount(1000)).toBe(true);
    expect(excelProcessor.isValidAmount('1000')).toBe(true);
    expect(excelProcessor.isValidAmount('1000.50')).toBe(true);
    expect(excelProcessor.isValidAmount('invalid')).toBe(false);
    expect(excelProcessor.isValidAmount(-100)).toBe(false);
  });
});
