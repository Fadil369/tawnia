const XLSX = require('xlsx');
const ExcelJS = require('exceljs');
const moment = require('moment');
const winston = require('winston');
const path = require('path');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/excel-processor.log' })
  ]
});

class ExcelProcessor {
  constructor() {
    this.supportedFormats = ['.xlsx', '.xls', '.csv'];
    this.fileTypes = {
      HEALTHCARE_ANALYTICS: 'Healthcare_Analytics_Report',
      HNH_STATEMENT: 'HNH_StatementOfAccount',
      TAWUNIYA_MEDICAL: 'TAWUNIYA_MEDICAL_INSURANCE'
    };
  }

  /**
   * Identify file type based on filename patterns
   */
  identifyFileType(filename) {
    const lowerFilename = filename.toLowerCase();

    if (lowerFilename.includes('healthcare_analytics')) {
      return this.fileTypes.HEALTHCARE_ANALYTICS;
    } else if (lowerFilename.includes('hnh_statementofaccount')) {
      return this.fileTypes.HNH_STATEMENT;
    } else if (lowerFilename.includes('tawuniya_medical_insurance')) {
      return this.fileTypes.TAWUNIYA_MEDICAL;
    }

    return 'UNKNOWN';
  }

  /**
   * Process Excel file based on its type
   */
  async processFile(filePath, filename) {
    try {
      logger.info(`Processing file: ${filename}`);

      const fileType = this.identifyFileType(filename);
      const workbook = XLSX.readFile(filePath);

      let processedData = {
        filename,
        fileType,
        processedAt: new Date().toISOString(),
        sheets: [],
        summary: {},
        metadata: {}
      };

      // Process each sheet in the workbook
      for (const sheetName of workbook.SheetNames) {
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
          raw: false,
          defval: null,
          header: 1
        });

        const processedSheet = await this.processSheet(jsonData, sheetName, fileType);
        processedData.sheets.push(processedSheet);
      }

      // Generate file summary
      processedData.summary = this.generateFileSummary(processedData.sheets, fileType);
      processedData.metadata = this.extractMetadata(workbook, filename);

      logger.info(`Successfully processed ${filename} - Type: ${fileType}`);
      return processedData;

    } catch (error) {
      logger.error(`Error processing file ${filename}:`, error);
      throw new Error(`Failed to process file: ${error.message}`);
    }
  }

  /**
   * Process individual sheet based on file type
   */
  async processSheet(jsonData, sheetName, fileType) {
    const sheet = {
      name: sheetName,
      rowCount: jsonData.length,
      columnCount: jsonData[0]?.length || 0,
      headers: [],
      data: [],
      analysis: {}
    };

    if (jsonData.length === 0) {
      return sheet;
    }

    // Extract headers (first non-empty row)
    let headerRowIndex = 0;
    while (headerRowIndex < jsonData.length &&
           (!jsonData[headerRowIndex] || jsonData[headerRowIndex].every(cell => !cell))) {
      headerRowIndex++;
    }

    if (headerRowIndex < jsonData.length) {
      sheet.headers = jsonData[headerRowIndex].map(header =>
        header ? String(header).trim() : ''
      );
    }

    // Process data rows
    const dataStartIndex = headerRowIndex + 1;
    for (let i = dataStartIndex; i < jsonData.length; i++) {
      const row = jsonData[i];
      if (row && row.some(cell => cell !== null && cell !== undefined && cell !== '')) {
        const rowData = {};
        sheet.headers.forEach((header, index) => {
          if (header) {
            rowData[header] = row[index] || null;
          }
        });
        sheet.data.push(rowData);
      }
    }

    // Perform type-specific analysis
    sheet.analysis = await this.analyzeSheetData(sheet, fileType);

    return sheet;
  }

  /**
   * Analyze sheet data based on file type
   */
  async analyzeSheetData(sheet, fileType) {
    const analysis = {
      dataQuality: this.assessDataQuality(sheet),
      patterns: {},
      insights: []
    };

    switch (fileType) {
      case this.fileTypes.HEALTHCARE_ANALYTICS:
        analysis.patterns = this.analyzeHealthcarePatterns(sheet);
        break;
      case this.fileTypes.HNH_STATEMENT:
        analysis.patterns = this.analyzeStatementPatterns(sheet);
        break;
      case this.fileTypes.TAWUNIYA_MEDICAL:
        analysis.patterns = this.analyzeTawuniyaPatterns(sheet);
        break;
      default:
        analysis.patterns = this.analyzeGenericPatterns(sheet);
    }

    return analysis;
  }

  /**
   * Analyze Healthcare Analytics Report patterns
   */
  analyzeHealthcarePatterns(sheet) {
    const patterns = {
      claimTypes: {},
      rejectionReasons: {},
      monthlyTrends: {},
      providerAnalysis: {},
      amountDistribution: {}
    };

    sheet.data.forEach(row => {
      // Analyze claim types
      const claimType = this.findFieldValue(row, ['claim_type', 'type', 'service_type']);
      if (claimType) {
        patterns.claimTypes[claimType] = (patterns.claimTypes[claimType] || 0) + 1;
      }

      // Analyze rejection reasons
      const rejectionReason = this.findFieldValue(row, ['rejection_reason', 'denial_reason', 'status']);
      if (rejectionReason && rejectionReason.toLowerCase().includes('reject')) {
        patterns.rejectionReasons[rejectionReason] = (patterns.rejectionReasons[rejectionReason] || 0) + 1;
      }

      // Analyze amounts
      const amount = this.findFieldValue(row, ['amount', 'claim_amount', 'total_amount']);
      if (amount && !isNaN(parseFloat(amount))) {
        const amountValue = parseFloat(amount);
        const range = this.getAmountRange(amountValue);
        patterns.amountDistribution[range] = (patterns.amountDistribution[range] || 0) + 1;
      }

      // Analyze dates for trends
      const date = this.findFieldValue(row, ['date', 'claim_date', 'service_date']);
      if (date) {
        const monthYear = moment(date).format('YYYY-MM');
        patterns.monthlyTrends[monthYear] = (patterns.monthlyTrends[monthYear] || 0) + 1;
      }
    });

    return patterns;
  }

  /**
   * Analyze Statement of Account patterns
   */
  analyzeStatementPatterns(sheet) {
    const patterns = {
      transactions: {},
      balances: {},
      paymentMethods: {},
      categories: {}
    };

    sheet.data.forEach(row => {
      // Analyze transaction types
      const transactionType = this.findFieldValue(row, ['transaction_type', 'type', 'description']);
      if (transactionType) {
        patterns.transactions[transactionType] = (patterns.transactions[transactionType] || 0) + 1;
      }

      // Analyze payment methods
      const paymentMethod = this.findFieldValue(row, ['payment_method', 'method', 'channel']);
      if (paymentMethod) {
        patterns.paymentMethods[paymentMethod] = (patterns.paymentMethods[paymentMethod] || 0) + 1;
      }
    });

    return patterns;
  }

  /**
   * Analyze Tawuniya Medical Insurance patterns
   */
  analyzeTawuniyaPatterns(sheet) {
    const patterns = {
      policyTypes: {},
      claimStatus: {},
      beneficiaryAnalysis: {},
      providerNetworks: {},
      specialties: {}
    };

    sheet.data.forEach(row => {
      // Analyze policy types
      const policyType = this.findFieldValue(row, ['policy_type', 'plan_type', 'coverage_type']);
      if (policyType) {
        patterns.policyTypes[policyType] = (patterns.policyTypes[policyType] || 0) + 1;
      }

      // Analyze claim status
      const status = this.findFieldValue(row, ['status', 'claim_status', 'approval_status']);
      if (status) {
        patterns.claimStatus[status] = (patterns.claimStatus[status] || 0) + 1;
      }

      // Analyze medical specialties
      const specialty = this.findFieldValue(row, ['specialty', 'medical_specialty', 'department']);
      if (specialty) {
        patterns.specialties[specialty] = (patterns.specialties[specialty] || 0) + 1;
      }
    });

    return patterns;
  }

  /**
   * Generic pattern analysis for unknown file types
   */
  analyzeGenericPatterns(sheet) {
    const patterns = {
      columnAnalysis: {},
      dataTypes: {},
      nullValues: {}
    };

    sheet.headers.forEach(header => {
      const columnData = sheet.data.map(row => row[header]).filter(val => val !== null && val !== undefined);

      patterns.columnAnalysis[header] = {
        totalValues: columnData.length,
        uniqueValues: new Set(columnData).size,
        dataType: this.inferDataType(columnData)
      };
    });

    return patterns;
  }

  /**
   * Helper function to find field value with multiple possible field names
   */
  findFieldValue(row, fieldNames) {
    for (const fieldName of fieldNames) {
      // Try exact match first
      if (row[fieldName] !== undefined && row[fieldName] !== null) {
        return row[fieldName];
      }

      // Try case-insensitive match
      const keys = Object.keys(row);
      const matchingKey = keys.find(key =>
        key.toLowerCase().includes(fieldName.toLowerCase()) ||
        fieldName.toLowerCase().includes(key.toLowerCase())
      );

      if (matchingKey && row[matchingKey] !== undefined && row[matchingKey] !== null) {
        return row[matchingKey];
      }
    }
    return null;
  }

  /**
   * Categorize amount into ranges
   */
  getAmountRange(amount) {
    if (amount < 100) return '0-100';
    if (amount < 500) return '100-500';
    if (amount < 1000) return '500-1K';
    if (amount < 5000) return '1K-5K';
    if (amount < 10000) return '5K-10K';
    return '10K+';
  }

  /**
   * Assess data quality of a sheet
   */
  assessDataQuality(sheet) {
    const quality = {
      completeness: 0,
      consistency: 0,
      validity: 0,
      score: 0
    };

    if (sheet.data.length === 0) {
      return quality;
    }

    let totalFields = 0;
    let filledFields = 0;
    let validFields = 0;

    sheet.data.forEach(row => {
      sheet.headers.forEach(header => {
        totalFields++;
        const value = row[header];

        if (value !== null && value !== undefined && value !== '') {
          filledFields++;

          // Basic validity checks
          if (this.isValidValue(value, header)) {
            validFields++;
          }
        }
      });
    });

    quality.completeness = totalFields > 0 ? (filledFields / totalFields) * 100 : 0;
    quality.validity = totalFields > 0 ? (validFields / totalFields) * 100 : 0;
    quality.consistency = this.calculateConsistency(sheet);
    quality.score = (quality.completeness + quality.validity + quality.consistency) / 3;

    return quality;
  }

  /**
   * Calculate data consistency score
   */
  calculateConsistency(sheet) {
    // Simple consistency check based on data type consistency within columns
    let consistentColumns = 0;

    sheet.headers.forEach(header => {
      const columnValues = sheet.data
        .map(row => row[header])
        .filter(val => val !== null && val !== undefined && val !== '');

      if (columnValues.length > 0) {
        const dataType = this.inferDataType(columnValues);
        const consistentValues = columnValues.filter(val =>
          this.matchesDataType(val, dataType)
        );

        if (consistentValues.length / columnValues.length > 0.8) {
          consistentColumns++;
        }
      }
    });

    return sheet.headers.length > 0 ? (consistentColumns / sheet.headers.length) * 100 : 0;
  }

  /**
   * Infer data type from array of values
   */
  inferDataType(values) {
    if (values.length === 0) return 'unknown';

    const sample = values.slice(0, Math.min(100, values.length));
    let numbers = 0;
    let dates = 0;
    let booleans = 0;

    sample.forEach(val => {
      if (!isNaN(parseFloat(val)) && isFinite(val)) numbers++;
      else if (moment(val, moment.ISO_8601, true).isValid()) dates++;
      else if (['true', 'false', '1', '0', 'yes', 'no'].includes(String(val).toLowerCase())) booleans++;
    });

    const total = sample.length;
    if (numbers / total > 0.8) return 'number';
    if (dates / total > 0.6) return 'date';
    if (booleans / total > 0.8) return 'boolean';
    return 'text';
  }

  /**
   * Check if value matches expected data type
   */
  matchesDataType(value, dataType) {
    switch (dataType) {
      case 'number':
        return !isNaN(parseFloat(value)) && isFinite(value);
      case 'date':
        return moment(value, moment.ISO_8601, true).isValid();
      case 'boolean':
        return ['true', 'false', '1', '0', 'yes', 'no'].includes(String(value).toLowerCase());
      default:
        return true;
    }
  }

  /**
   * Basic value validation
   */
  isValidValue(value, fieldName) {
    const strValue = String(value).trim();
    if (strValue === '') return false;

    // Field-specific validations
    if (fieldName.toLowerCase().includes('email')) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(strValue);
    }

    if (fieldName.toLowerCase().includes('phone')) {
      return /^[\+]?[\d\s\-\(\)]{7,}$/.test(strValue);
    }

    if (fieldName.toLowerCase().includes('amount') || fieldName.toLowerCase().includes('price')) {
      return !isNaN(parseFloat(strValue));
    }

    return true;
  }

  /**
   * Generate file summary
   */
  generateFileSummary(sheets, fileType) {
    const summary = {
      totalSheets: sheets.length,
      totalRows: sheets.reduce((sum, sheet) => sum + sheet.rowCount, 0),
      totalDataRows: sheets.reduce((sum, sheet) => sum + sheet.data.length, 0),
      fileType,
      overallQuality: 0,
      keyInsights: []
    };

    // Calculate overall quality score
    const qualityScores = sheets
      .map(sheet => sheet.analysis.dataQuality.score)
      .filter(score => score > 0);

    if (qualityScores.length > 0) {
      summary.overallQuality = qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length;
    }

    // Generate key insights
    summary.keyInsights = this.generateKeyInsights(sheets, fileType);

    return summary;
  }

  /**
   * Generate key insights from processed data
   */
  generateKeyInsights(sheets, fileType) {
    const insights = [];

    sheets.forEach(sheet => {
      const patterns = sheet.analysis.patterns;

      // Quality insights
      if (sheet.analysis.dataQuality.score < 70) {
        insights.push(`Low data quality detected in sheet "${sheet.name}" (${sheet.analysis.dataQuality.score.toFixed(1)}% score)`);
      }

      // Pattern insights based on file type
      if (fileType === this.fileTypes.HEALTHCARE_ANALYTICS) {
        if (patterns.rejectionReasons && Object.keys(patterns.rejectionReasons).length > 0) {
          const topRejection = Object.entries(patterns.rejectionReasons)
            .sort(([,a], [,b]) => b - a)[0];
          insights.push(`Top rejection reason: ${topRejection[0]} (${topRejection[1]} cases)`);
        }
      }

      if (patterns.claimTypes && Object.keys(patterns.claimTypes).length > 0) {
        const topClaimType = Object.entries(patterns.claimTypes)
          .sort(([,a], [,b]) => b - a)[0];
        insights.push(`Most common claim type: ${topClaimType[0]} (${topClaimType[1]} claims)`);
      }
    });

    return insights;
  }

  /**
   * Extract metadata from workbook
   */
  extractMetadata(workbook, filename) {
    const metadata = {
      filename,
      sheetNames: workbook.SheetNames,
      createdAt: new Date().toISOString(),
      fileSize: null, // Could be added if file stats are available
      lastModified: null,
      creator: null
    };

    // Try to extract additional metadata if available
    if (workbook.Props) {
      metadata.creator = workbook.Props.Author || null;
      metadata.lastModified = workbook.Props.ModifiedDate || null;
    }

    return metadata;
  }

  /**
   * Validate claim data structure and values
   */
  validateClaimData(claim) {
    try {
      // Check for required fields
      const requiredFields = ['Claim ID', 'Patient Name', 'Insurance Provider', 'Claim Amount', 'Status'];
      for (const field of requiredFields) {
        if (!claim[field] || claim[field].toString().trim() === '') {
          return false;
        }
      }

      // Validate claim amount
      if (!this.isValidAmount(claim['Claim Amount'])) {
        return false;
      }

      // Validate status
      const validStatuses = ['Approved', 'Rejected', 'Pending', 'Under Review'];
      if (!validStatuses.includes(claim['Status'])) {
        return false;
      }

      // Validate date if present
      if (claim['Date Submitted'] && !this.isValidDate(claim['Date Submitted'])) {
        return false;
      }

      return true;
    } catch (error) {
      logger.error('Error validating claim data:', error);
      return false;
    }
  }

  /**
   * Validate if a value is a valid date
   */
  isValidDate(dateValue) {
    if (!dateValue) return false;

    // Try parsing with moment
    const date = moment(dateValue, ['YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY/MM/DD'], true);
    return date.isValid();
  }

  /**
   * Validate if a value is a valid amount
   */
  isValidAmount(amount) {
    if (amount === null || amount === undefined) return false;

    const numAmount = parseFloat(amount);
    return !isNaN(numAmount) && numAmount >= 0;
  }

  /**
   * Validate insurance provider
   */
  isValidInsuranceProvider(provider) {
    if (!provider) return false;

    const validProviders = [
      'Tawuniya', 'Bupa Arabia', 'Malath Insurance', 'Walaa Insurance',
      'Allied Cooperative Insurance', 'Buruj Cooperative Insurance',
      'Solidarity Saudi Takaful', 'Sanad Cooperative Insurance'
    ];

    return validProviders.some(valid =>
      provider.toLowerCase().includes(valid.toLowerCase())
    );
  }
}

module.exports = new ExcelProcessor();
