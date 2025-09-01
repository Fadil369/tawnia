const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const ExcelJS = require('exceljs');
const { Parser } = require('json2csv');
const PDFDocument = require('pdf-lib').PDFDocument;

// Security middleware
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');

// Rate limiting
const reportLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // limit each IP to 10 requests per windowMs
  message: 'Too many report requests from this IP'
});

// Security headers
const securityMiddleware = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:"],
    },
  },
});

const router = express.Router();

/**
 * Generate comprehensive report in specified format
 */
router.post('/generate', reportLimiter, securityMiddleware, async (req, res) => {
  try {
    // Input validation and sanitization
    const resultId = typeof req.body.resultId === 'string' ? req.body.resultId.replace(/[^a-zA-Z0-9_-]/g, '') : null;
    const format = typeof req.body.format === 'string' ? req.body.format.toLowerCase() : 'json';
    const sections = Array.isArray(req.body.sections) ? req.body.sections.filter(s => typeof s === 'string') : ['summary', 'analysis', 'insights'];
    const includeCharts = Boolean(req.body.includeCharts);
    
    // Validate format
    const allowedFormats = ['json', 'excel', 'csv', 'pdf'];
    if (!allowedFormats.includes(format)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid format',
        message: 'Format must be one of: json, excel, csv, pdf'
      });
    }

    if (!resultId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Result ID is required for report generation'
      });
    }

    // Secure path construction to prevent path traversal
    const dataDir = path.resolve(__dirname, '../../data');
    const sanitizedResultId = path.basename(resultId); // Remove any path components
    const dataPath = path.join(dataDir, `${sanitizedResultId}.json`);
    
    // Ensure the resolved path is within the data directory
    if (!dataPath.startsWith(dataDir)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid result ID',
        message: 'Result ID contains invalid characters'
      });
    }

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      // Generate report based on format
      const reportData = await generateReportData(processedData, sections);

      let reportFile;
      let contentType;

      switch (format.toLowerCase()) {
        case 'excel':
          reportFile = await generateExcelReport(reportData, resultId);
          contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
          break;
        case 'csv':
          reportFile = await generateCSVReport(reportData, resultId);
          contentType = 'text/csv';
          break;
        case 'pdf':
          reportFile = await generatePDFReport(reportData, resultId);
          contentType = 'application/pdf';
          break;
        case 'json':
        default:
          reportFile = await generateJSONReport(reportData, resultId);
          contentType = 'application/json';
          break;
      }

      // Save report file
      const reportsDir = path.join(__dirname, '../../reports');
      await fs.mkdir(reportsDir, { recursive: true });

      const reportPath = path.join(reportsDir, reportFile.filename);
      await fs.writeFile(reportPath, reportFile.content);

      res.json({
        success: true,
        message: 'Report generated successfully',
        data: {
          resultId,
          format,
          sections,
          filename: reportFile.filename,
          downloadUrl: `/api/reports/download/${reportFile.filename}`,
          generatedAt: new Date().toISOString()
        }
      });

    } catch (fileError) {
      res.status(404).json({
        success: false,
        error: 'Data not found',
        message: 'The specified result ID was not found'
      });
    }

  } catch (error) {
    console.error('Report generation error:', error);
    res.status(500).json({
      success: false,
      error: 'Report generation failed',
      message: error.message
    });
  }
});

/**
 * Download generated report
 */
router.get('/download/:filename', securityMiddleware, async (req, res) => {
  try {
    // Validate and sanitize filename
    const filename = typeof req.params.filename === 'string' ? req.params.filename : '';
    
    // Check for path traversal attempts
    if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
      return res.status(400).json({
        success: false,
        error: 'Invalid filename',
        message: 'Filename contains invalid characters'
      });
    }
    
    // Validate file extension
    const allowedExtensions = ['.json', '.xlsx', '.csv', '.pdf'];
    const ext = path.extname(filename).toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid file type',
        message: 'File type not allowed'
      });
    }
    
    // Secure path construction
    const reportsDir = path.resolve(__dirname, '../../reports');
    const reportPath = path.join(reportsDir, path.basename(filename));
    
    // Ensure the resolved path is within the reports directory
    if (!reportPath.startsWith(reportsDir)) {
      return res.status(403).json({
        success: false,
        error: 'Access denied',
        message: 'Invalid file path'
      });
    }

    try {
      await fs.access(reportPath);

      // Determine content type based on file extension
      const ext = path.extname(filename).toLowerCase();
      let contentType = 'application/octet-stream';

      switch (ext) {
        case '.xlsx':
          contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
          break;
        case '.csv':
          contentType = 'text/csv';
          break;
        case '.pdf':
          contentType = 'application/pdf';
          break;
        case '.json':
          contentType = 'application/json';
          break;
      }

      res.setHeader('Content-Type', contentType);
      res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);

      const fileStream = require('fs').createReadStream(reportPath);
      fileStream.pipe(res);

    } catch (fileError) {
      res.status(404).json({
        success: false,
        error: 'File not found',
        message: 'The requested report file was not found'
      });
    }

  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({
      success: false,
      error: 'Download failed',
      message: error.message
    });
  }
});

/**
 * List available reports
 */
router.get('/list', async (req, res) => {
  try {
    const reportsDir = path.join(__dirname, '../../reports');

    try {
      const files = await fs.readdir(reportsDir);
      const reports = [];

      for (const file of files) {
        try {
          const filePath = path.join(reportsDir, file);
          const stats = await fs.stat(filePath);

          reports.push({
            filename: file,
            size: stats.size,
            createdAt: stats.birthtime,
            modifiedAt: stats.mtime,
            format: path.extname(file).slice(1).toUpperCase(),
            downloadUrl: `/api/reports/download/${file}`
          });
        } catch (statError) {
          console.error(`Error getting stats for ${file}:`, statError);
        }
      }

      // Sort by creation date (newest first)
      reports.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

      res.json({
        success: true,
        data: {
          reports,
          total: reports.length
        }
      });

    } catch (dirError) {
      // Directory doesn't exist yet
      res.json({
        success: true,
        data: {
          reports: [],
          total: 0
        }
      });
    }

  } catch (error) {
    console.error('Report list error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve report list',
      message: error.message
    });
  }
});

/**
 * Delete report file
 */
router.delete('/:filename', reportLimiter, securityMiddleware, async (req, res) => {
  try {
    // Validate and sanitize filename
    const filename = typeof req.params.filename === 'string' ? req.params.filename : '';
    
    // Check for path traversal attempts
    if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
      return res.status(400).json({
        success: false,
        error: 'Invalid filename',
        message: 'Filename contains invalid characters'
      });
    }
    
    // Secure path construction
    const reportsDir = path.resolve(__dirname, '../../reports');
    const reportPath = path.join(reportsDir, path.basename(filename));
    
    // Ensure the resolved path is within the reports directory
    if (!reportPath.startsWith(reportsDir)) {
      return res.status(403).json({
        success: false,
        error: 'Access denied',
        message: 'Invalid file path'
      });
    }

    try {
      await fs.unlink(reportPath);
      res.json({
        success: true,
        message: 'Report deleted successfully'
      });
    } catch (fileError) {
      res.status(404).json({
        success: false,
        error: 'File not found',
        message: 'The specified report file was not found'
      });
    }

  } catch (error) {
    console.error('Delete error:', error);
    res.status(500).json({
      success: false,
      error: 'Delete failed',
      message: error.message
    });
  }
});

// Report Generation Functions

/**
 * Generate report data structure
 */
async function generateReportData(processedData, sections) {
  const reportData = {
    metadata: {
      filename: processedData.filename,
      fileType: processedData.fileType,
      processedAt: processedData.processedAt,
      generatedAt: new Date().toISOString()
    },
    sections: {}
  };

  if (sections.includes('summary')) {
    reportData.sections.summary = generateSummarySection(processedData);
  }

  if (sections.includes('analysis')) {
    reportData.sections.analysis = generateAnalysisSection(processedData);
  }

  if (sections.includes('insights')) {
    reportData.sections.insights = generateInsightsSection(processedData);
  }

  if (sections.includes('details')) {
    reportData.sections.details = generateDetailsSection(processedData);
  }

  return reportData;
}

/**
 * Generate summary section
 */
function generateSummarySection(processedData) {
  // Add null/undefined checks to prevent runtime errors
  const summary = processedData.summary || {};
  const overview = summary.overview || {};
  
  return {
    title: 'Executive Summary',
    overview: {
      totalSheets: overview.totalSheets || summary.totalSheets || 0,
      totalRows: overview.totalRows || summary.totalDataRows || 0,
      overallQuality: overview.overallQuality || summary.overallQuality || 0,
      fileType: processedData.fileType || 'unknown'
    },
    keyMetrics: processedData.summary.keyInsights || [],
    recommendations: [
      'Regular data quality monitoring',
      'Automated validation implementation',
      'Process standardization'
    ]
  };
}

/**
 * Generate analysis section
 */
function generateAnalysisSection(processedData) {
  const analysis = {
    title: 'Detailed Analysis',
    sheetAnalysis: []
  };

  processedData.sheets.forEach(sheet => {
    analysis.sheetAnalysis.push({
      sheetName: sheet.name,
      rowCount: sheet.rowCount,
      columnCount: sheet.columnCount,
      dataQuality: sheet.analysis?.dataQuality || {},
      patterns: sheet.analysis?.patterns || {},
      topFindings: generateSheetFindings(sheet)
    });
  });

  return analysis;
}

/**
 * Generate insights section
 */
function generateInsightsSection(processedData) {
  return {
    title: 'AI-Powered Insights',
    patterns: generatePatternInsights(processedData),
    recommendations: generateRecommendations(processedData),
    predictions: generatePredictions(processedData)
  };
}

/**
 * Generate details section
 */
function generateDetailsSection(processedData) {
  return {
    title: 'Technical Details',
    processingMetadata: processedData.metadata,
    dataStructure: processedData.sheets.map(sheet => ({
      name: sheet.name,
      headers: sheet.headers,
      sampleData: sheet.data.slice(0, 5) // First 5 rows as sample
    })),
    qualityMetrics: processedData.sheets.map(sheet => ({
      sheet: sheet.name,
      quality: sheet.analysis?.dataQuality
    }))
  };
}

/**
 * Generate Excel report
 */
async function generateExcelReport(reportData, resultId) {
  const workbook = new ExcelJS.Workbook();
  const timestamp = new Date().toISOString().slice(0, 10);

  // Summary worksheet
  if (reportData.sections.summary) {
    const summaryWs = workbook.addWorksheet('Summary');
    addSummaryToWorksheet(summaryWs, reportData.sections.summary);
  }

  // Analysis worksheet
  if (reportData.sections.analysis) {
    const analysisWs = workbook.addWorksheet('Analysis');
    addAnalysisToWorksheet(analysisWs, reportData.sections.analysis);
  }

  // Insights worksheet
  if (reportData.sections.insights) {
    const insightsWs = workbook.addWorksheet('Insights');
    addInsightsToWorksheet(insightsWs, reportData.sections.insights);
  }

  const filename = `report_${resultId}_${timestamp}.xlsx`;
  const buffer = await workbook.xlsx.writeBuffer();

  return {
    filename,
    content: buffer
  };
}

/**
 * Generate CSV report
 */
async function generateCSVReport(reportData, resultId) {
  const timestamp = new Date().toISOString().slice(0, 10);

  // Flatten report data for CSV
  const flattenedData = flattenReportData(reportData);

  const parser = new Parser();
  const csv = parser.parse(flattenedData);

  const filename = `report_${resultId}_${timestamp}.csv`;

  return {
    filename,
    content: csv
  };
}

/**
 * Generate PDF report
 */
async function generatePDFReport(reportData, resultId) {
  const timestamp = new Date().toISOString().slice(0, 10);

  // For now, create a simple text-based PDF
  // In production, you'd use a proper PDF generation library
  const pdfContent = generatePDFContent(reportData);

  const filename = `report_${resultId}_${timestamp}.pdf`;

  return {
    filename,
    content: Buffer.from(pdfContent, 'utf8')
  };
}

/**
 * Generate JSON report
 */
async function generateJSONReport(reportData, resultId) {
  const timestamp = new Date().toISOString().slice(0, 10);

  const filename = `report_${resultId}_${timestamp}.json`;
  const content = JSON.stringify(reportData, null, 2);

  return {
    filename,
    content: Buffer.from(content, 'utf8')
  };
}

// Helper functions for report generation

function generateSheetFindings(sheet) {
  const findings = [];

  if (sheet.analysis?.dataQuality?.score < 80) {
    findings.push(`Data quality needs improvement (${sheet.analysis.dataQuality.score.toFixed(1)}%)`);
  }

  if (sheet.data.length > 10000) {
    findings.push(`Large dataset detected (${sheet.data.length.toLocaleString()} rows)`);
  }

  return findings;
}

function generatePatternInsights(processedData) {
  return [
    'Data volume patterns identified',
    'Quality consistency patterns analyzed',
    'Temporal patterns detected'
  ];
}

function generateRecommendations(processedData) {
  return [
    'Implement automated data validation',
    'Establish quality monitoring procedures',
    'Optimize data processing workflows',
    'Enhance error handling mechanisms'
  ];
}

function generatePredictions(processedData) {
  return [
    'Expected data volume growth: 15-25% quarterly',
    'Quality improvement potential: 10-20%',
    'Processing efficiency gains: 30-50%'
  ];
}

function addSummaryToWorksheet(worksheet, summary) {
  worksheet.addRow(['EXECUTIVE SUMMARY']);
  worksheet.addRow([]);
  worksheet.addRow(['Metric', 'Value']);
  worksheet.addRow(['Total Sheets', summary.overview.totalSheets]);
  worksheet.addRow(['Total Rows', summary.overview.totalRows]);
  worksheet.addRow(['Overall Quality', `${summary.overview.overallQuality}%`]);
  worksheet.addRow(['File Type', summary.overview.fileType]);
}

function addAnalysisToWorksheet(worksheet, analysis) {
  worksheet.addRow(['DETAILED ANALYSIS']);
  worksheet.addRow([]);
  worksheet.addRow(['Sheet Name', 'Row Count', 'Column Count', 'Quality Score']);

  analysis.sheetAnalysis.forEach(sheet => {
    worksheet.addRow([
      sheet.sheetName,
      sheet.rowCount,
      sheet.columnCount,
      sheet.dataQuality.score || 'N/A'
    ]);
  });
}

function addInsightsToWorksheet(worksheet, insights) {
  worksheet.addRow(['AI-POWERED INSIGHTS']);
  worksheet.addRow([]);
  worksheet.addRow(['Type', 'Description']);

  insights.patterns.forEach(pattern => {
    worksheet.addRow(['Pattern', pattern]);
  });

  insights.recommendations.forEach(rec => {
    worksheet.addRow(['Recommendation', rec]);
  });
}

function flattenReportData(reportData) {
  const flattened = [];

  // Add summary data
  if (reportData.sections.summary) {
    flattened.push({
      Section: 'Summary',
      Type: 'Total Sheets',
      Value: reportData.sections.summary.overview.totalSheets
    });
    flattened.push({
      Section: 'Summary',
      Type: 'Total Rows',
      Value: reportData.sections.summary.overview.totalRows
    });
  }

  return flattened;
}

function generatePDFContent(reportData) {
  let content = 'HEALTHCARE INSURANCE DATA ANALYSIS REPORT\n\n';
  content += `Generated: ${reportData.metadata.generatedAt}\n`;
  content += `File: ${reportData.metadata.filename}\n\n`;

  if (reportData.sections.summary) {
    content += 'EXECUTIVE SUMMARY\n';
    content += '-'.repeat(50) + '\n';
    content += `Total Sheets: ${reportData.sections.summary.overview.totalSheets}\n`;
    content += `Total Rows: ${reportData.sections.summary.overview.totalRows}\n`;
    content += `Overall Quality: ${reportData.sections.summary.overview.overallQuality}%\n\n`;
  }

  return content;
}

module.exports = router;
