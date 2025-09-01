const request = require('supertest');
const app = require('../src/server');
const fs = require('fs').promises;
const path = require('path');

describe('Tawnia Healthcare Analytics API Tests', () => {
  beforeAll(async () => {
    // Ensure test directories exist
    await fs.mkdir(path.join(__dirname, '../uploads'), { recursive: true });
    await fs.mkdir(path.join(__dirname, '../data'), { recursive: true });
    await fs.mkdir(path.join(__dirname, '../reports'), { recursive: true });
  });

  afterAll(async () => {
    // Cleanup test files
    try {
      const testFiles = await fs.readdir(path.join(__dirname, '../data'));
      for (const file of testFiles) {
        if (file.includes('test')) {
          await fs.unlink(path.join(__dirname, '../data', file));
        }
      }
    } catch (error) {
      console.log('Cleanup completed');
    }
  });

  describe('Health Check', () => {
    test('GET /health should return system status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('version');
    });
  });

  describe('File Upload', () => {
    test('POST /api/upload/single should handle valid Excel file', async () => {
      // Create a test Excel file buffer
      const testBuffer = await createTestExcelFile();

      const response = await request(app)
        .post('/api/upload/single')
        .attach('file', testBuffer, 'test_healthcare_data.xlsx')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('filename');
      expect(response.body.data).toHaveProperty('id');
    });

    test('POST /api/upload/single should reject invalid file type', async () => {
      const response = await request(app)
        .post('/api/upload/single')
        .attach('file', Buffer.from('invalid content'), 'test.txt')
        .expect(400);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
    });

    test('GET /api/upload/history should return upload history', async () => {
      const response = await request(app)
        .get('/api/upload/history')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('uploads');
      expect(Array.isArray(response.body.data.uploads)).toBe(true);
    });
  });

  describe('Analysis Endpoints', () => {
    let testResultId;

    beforeAll(async () => {
      // Upload a test file to get a result ID
      const testBuffer = await createTestExcelFile();
      const uploadResponse = await request(app)
        .post('/api/upload/single')
        .attach('file', testBuffer, 'test_analysis.xlsx');

      testResultId = uploadResponse.body.data.id;
    });

    test('POST /api/analyze/rejections should analyze rejections', async () => {
      const response = await request(app)
        .post('/api/analyze/rejections')
        .send({ resultId: testResultId })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('analysisType', 'rejections');
    });

    test('POST /api/analyze/trends should analyze trends', async () => {
      const response = await request(app)
        .post('/api/analyze/trends')
        .send({ resultId: testResultId })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('analysisType', 'trends');
    });

    test('POST /api/analyze/patterns should find patterns', async () => {
      const response = await request(app)
        .post('/api/analyze/patterns')
        .send({ resultId: testResultId })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('analysisType', 'patterns');
    });

    test('POST /api/analyze/quality should assess data quality', async () => {
      const response = await request(app)
        .post('/api/analyze/quality')
        .send({ resultId: testResultId })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('analysisType', 'quality');
    });
  });

  describe('AI Insights', () => {
    let testResultId;

    beforeAll(async () => {
      const testBuffer = await createTestExcelFile();
      const uploadResponse = await request(app)
        .post('/api/upload/single')
        .attach('file', testBuffer, 'test_insights.xlsx');

      testResultId = uploadResponse.body.data.id;
    });

    test('POST /api/insights/generate should generate AI insights', async () => {
      const response = await request(app)
        .post('/api/insights/generate')
        .send({ resultId: testResultId })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('insights');
      expect(Array.isArray(response.body.data.insights)).toBe(true);
    });
  });

  describe('Reports', () => {
    let testResultId;

    beforeAll(async () => {
      const testBuffer = await createTestExcelFile();
      const uploadResponse = await request(app)
        .post('/api/upload/single')
        .attach('file', testBuffer, 'test_reports.xlsx');

      testResultId = uploadResponse.body.data.id;
    });

    test('POST /api/reports/generate should generate JSON report', async () => {
      const response = await request(app)
        .post('/api/reports/generate')
        .send({
          resultId: testResultId,
          format: 'json',
          sections: ['summary', 'analysis']
        })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('filename');
      expect(response.body.data).toHaveProperty('downloadUrl');
    });

    test('POST /api/reports/generate should generate Excel report', async () => {
      const response = await request(app)
        .post('/api/reports/generate')
        .send({
          resultId: testResultId,
          format: 'excel',
          sections: ['summary', 'analysis', 'insights']
        })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data.filename).toMatch(/\.xlsx$/);
    });

    test('GET /api/reports/list should return reports list', async () => {
      const response = await request(app)
        .get('/api/reports/list')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('reports');
      expect(Array.isArray(response.body.data.reports)).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test('POST /api/analyze/rejections should handle missing resultId', async () => {
      const response = await request(app)
        .post('/api/analyze/rejections')
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
    });

    test('POST /api/analyze/rejections should handle invalid resultId', async () => {
      const response = await request(app)
        .post('/api/analyze/rejections')
        .send({ resultId: 'invalid-id' })
        .expect(404);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
    });

    test('GET /api/reports/download/nonexistent should return 404', async () => {
      const response = await request(app)
        .get('/api/reports/download/nonexistent.xlsx')
        .expect(404);

      expect(response.body).toHaveProperty('success', false);
    });
  });
});

// Helper function to create test Excel file
async function createTestExcelFile() {
  const ExcelJS = require('exceljs');
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('Test Healthcare Data');

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

  // Add sample data
  const sampleData = [
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
    }
  ];

  sampleData.forEach(row => {
    worksheet.addRow(row);
  });

  // Style the header row
  worksheet.getRow(1).font = { bold: true };
  worksheet.getRow(1).fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFE0E0E0' }
  };

  const buffer = await workbook.xlsx.writeBuffer();
  return buffer;
}

module.exports = { createTestExcelFile };
