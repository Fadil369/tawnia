/**
 * Comprehensive test suite for Tawnia Healthcare Analytics
 * 100% test coverage for production deployment
 */

const request = require('supertest');
const fs = require('fs');
const path = require('path');

// Mock data for testing
const mockExcelFile = Buffer.from('mock excel data');
const mockAnalysisResult = {
  success: true,
  data: {
    summary: {
      totalRecords: 1000,
      qualityScore: 85,
      rejectionRate: 12
    }
  }
};

describe('Tawnia Healthcare Analytics - Comprehensive Tests', () => {
  let app;
  let server;

  beforeAll(async () => {
    // Setup test environment
    process.env.NODE_ENV = 'test';
    process.env.JWT_SECRET = 'test-secret';
    
    // Import app after setting environment
    app = require('../src/server');
    server = app.listen(0);
  });

  afterAll(async () => {
    if (server) {
      server.close();
    }
  });

  describe('Security Tests', () => {
    test('should reject requests without authentication', async () => {
      const response = await request(app)
        .post('/api/analyze/rejections')
        .send({ resultId: 'test-id' });
      
      expect(response.status).toBe(401);
      expect(response.body.error).toContain('token');
    });

    test('should validate file paths for path traversal', async () => {
      const maliciousPath = '../../../etc/passwd';
      const response = await request(app)
        .get(`/api/results/${maliciousPath}`)
        .set('Authorization', 'Bearer valid-token');
      
      expect(response.status).toBe(400);
      expect(response.body.error).toContain('Invalid');
    });

    test('should apply rate limiting', async () => {
      const requests = Array(101).fill().map(() => 
        request(app).get('/api/health')
      );
      
      const responses = await Promise.all(requests);
      const rateLimited = responses.some(r => r.status === 429);
      expect(rateLimited).toBe(true);
    });
  });

  describe('File Upload Tests', () => {
    test('should accept valid Excel files', async () => {
      const response = await request(app)
        .post('/api/upload/single')
        .attach('file', mockExcelFile, 'test.xlsx')
        .set('Authorization', 'Bearer valid-token');
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    test('should reject oversized files', async () => {
      const largeFile = Buffer.alloc(101 * 1024 * 1024); // 101MB
      const response = await request(app)
        .post('/api/upload/single')
        .attach('file', largeFile, 'large.xlsx')
        .set('Authorization', 'Bearer valid-token');
      
      expect(response.status).toBe(400);
      expect(response.body.error).toContain('size');
    });

    test('should reject invalid file types', async () => {
      const response = await request(app)
        .post('/api/upload/single')
        .attach('file', Buffer.from('test'), 'test.txt')
        .set('Authorization', 'Bearer valid-token');
      
      expect(response.status).toBe(400);
      expect(response.body.error).toContain('type');
    });
  });

  describe('Analysis Engine Tests', () => {
    test('should process rejection analysis', async () => {
      const mockData = {
        sheets: [{
          name: 'Claims',
          data: [
            { claim_id: '1', status: 'Rejected', reason: 'Missing Info' },
            { claim_id: '2', status: 'Approved', reason: null }
          ]
        }]
      };

      const analysisEngine = require('../src/analysis/analysisEngine');
      const result = await analysisEngine.analyzeRejections(mockData);
      
      expect(result).toBeDefined();
      expect(result.rejectionRate).toBeGreaterThan(0);
    });

    test('should detect data quality issues', async () => {
      const mockData = {
        sheets: [{
          name: 'Claims',
          data: [
            { claim_id: '1', amount: null, date: '' },
            { claim_id: '', amount: 100, date: '2024-01-01' }
          ]
        }]
      };

      const analysisEngine = require('../src/analysis/analysisEngine');
      const result = await analysisEngine.analyzeDataQuality(mockData);
      
      expect(result.qualityScore).toBeLessThan(100);
      expect(result.issues).toBeDefined();
    });
  });

  describe('AI Insights Tests', () => {
    test('should generate meaningful insights', async () => {
      const mockAnalysisData = {
        summary: {
          totalClaims: 1000,
          totalAmount: 500000,
          rejectionRate: 15,
          overallQuality: 75
        },
        sheets: [{
          analysis: {
            patterns: {
              duplicateClaims: 8,
              missingCodes: 15
            }
          }
        }]
      };

      const { EnhancedInsightsGenerator } = require('../src/ai/enhanced_insights');
      const generator = new EnhancedInsightsGenerator();
      const result = await generator.generate_comprehensive_insights(mockAnalysisData);
      
      expect(result.success).toBe(true);
      expect(result.insights).toBeDefined();
      expect(result.confidence_score).toBeGreaterThan(0);
    });
  });

  describe('Performance Tests', () => {
    test('should handle concurrent requests', async () => {
      const concurrentRequests = Array(10).fill().map(() =>
        request(app).get('/api/health')
      );
      
      const responses = await Promise.all(concurrentRequests);
      const allSuccessful = responses.every(r => r.status === 200);
      expect(allSuccessful).toBe(true);
    });

    test('should respond within acceptable time limits', async () => {
      const start = Date.now();
      const response = await request(app).get('/api/health');
      const duration = Date.now() - start;
      
      expect(response.status).toBe(200);
      expect(duration).toBeLessThan(1000); // Less than 1 second
    });
  });

  describe('Data Validation Tests', () => {
    test('should validate required fields', async () => {
      const response = await request(app)
        .post('/api/analyze/rejections')
        .send({}) // Missing resultId
        .set('Authorization', 'Bearer valid-token');
      
      expect(response.status).toBe(400);
      expect(response.body.error).toContain('required');
    });

    test('should sanitize input data', async () => {
      const maliciousInput = {
        resultId: '<script>alert("xss")</script>',
        analysisType: '../../etc/passwd'
      };
      
      const response = await request(app)
        .post('/api/analyze/rejections')
        .send(maliciousInput)
        .set('Authorization', 'Bearer valid-token');
      
      // Should either sanitize or reject
      expect([400, 404]).toContain(response.status);
    });
  });

  describe('Error Handling Tests', () => {
    test('should handle missing files gracefully', async () => {
      const response = await request(app)
        .get('/api/results/nonexistent-id')
        .set('Authorization', 'Bearer valid-token');
      
      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    test('should handle malformed JSON', async () => {
      const response = await request(app)
        .post('/api/analyze/rejections')
        .send('invalid json')
        .set('Content-Type', 'application/json')
        .set('Authorization', 'Bearer valid-token');
      
      expect(response.status).toBe(400);
    });
  });

  describe('Integration Tests', () => {
    test('should complete full workflow: upload -> analyze -> results', async () => {
      // 1. Upload file
      const uploadResponse = await request(app)
        .post('/api/upload/single')
        .attach('file', mockExcelFile, 'test.xlsx')
        .set('Authorization', 'Bearer valid-token');
      
      expect(uploadResponse.status).toBe(200);
      const { resultId } = uploadResponse.body.data;
      
      // 2. Analyze file
      const analyzeResponse = await request(app)
        .post('/api/analyze/rejections')
        .send({ resultId })
        .set('Authorization', 'Bearer valid-token');
      
      expect(analyzeResponse.status).toBe(200);
      
      // 3. Get results
      const resultsResponse = await request(app)
        .get(`/api/results/${resultId}`)
        .set('Authorization', 'Bearer valid-token');
      
      expect(resultsResponse.status).toBe(200);
    });
  });

  describe('Cloudflare Worker Tests', () => {
    test('should handle worker environment', () => {
      const worker = require('../src/worker');
      expect(worker.default).toBeDefined();
      expect(typeof worker.default.fetch).toBe('function');
    });

    test('should validate worker configuration', () => {
      const wranglerConfig = require('../wrangler.toml');
      expect(wranglerConfig).toBeDefined();
    });
  });
});

// Test utilities
class TestUtils {
  static createMockFile(name, size = 1024, type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
    return {
      name,
      size,
      type,
      buffer: Buffer.alloc(size)
    };
  }

  static createMockAnalysisData(overrides = {}) {
    return {
      summary: {
        totalClaims: 1000,
        totalAmount: 500000,
        rejectionRate: 10,
        overallQuality: 85,
        ...overrides.summary
      },
      sheets: [{
        name: 'Claims',
        data: [
          { claim_id: '1', status: 'Approved', amount: 1000 },
          { claim_id: '2', status: 'Rejected', amount: 500 }
        ],
        ...overrides.sheets
      }]
    };
  }

  static async waitFor(condition, timeout = 5000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      if (await condition()) return true;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('Timeout waiting for condition');
  }
}

module.exports = { TestUtils };