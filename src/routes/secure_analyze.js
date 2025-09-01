const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const analysisEngine = require('../analysis/analysisEngine');
const { authenticateToken, authorize } = require('../security/auth_middleware');

const router = express.Router();

// Secure path validation helper
const validateAndSanitizePath = (resultId, baseDir = '../../data') => {
  const sanitizedId = resultId.replace(/[^a-zA-Z0-9_-]/g, '');
  const dataPath = path.resolve(__dirname, baseDir, `${sanitizedId}.json`);
  const expectedDir = path.resolve(__dirname, baseDir);
  
  if (!dataPath.startsWith(expectedDir)) {
    throw new Error('Invalid file path');
  }
  
  return dataPath;
};

/**
 * Analyze rejection patterns in processed data
 */
router.post('/rejections', authenticateToken, authorize(['admin', 'analyst']), async (req, res) => {
  try {
    const { resultId, analysisType = 'comprehensive' } = req.body;

    if (!resultId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Result ID is required for analysis'
      });
    }

    const dataPath = validateAndSanitizePath(resultId);

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      const rejectionAnalysis = await analysisEngine.analyzeRejections(processedData, analysisType);

      res.json({
        success: true,
        message: 'Rejection analysis completed successfully',
        data: {
          resultId,
          analysisType,
          rejectionAnalysis,
          processedAt: new Date().toISOString()
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
    console.error('Rejection analysis error:', error);
    res.status(500).json({
      success: false,
      error: 'Analysis failed',
      message: error.message
    });
  }
});

/**
 * Get available analysis metrics for a file
 */
router.get('/metrics/:resultId', authenticateToken, async (req, res) => {
  try {
    const { resultId } = req.params;
    const dataPath = validateAndSanitizePath(resultId);

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      const availableMetrics = analysisEngine.getAvailableMetrics(processedData);

      res.json({
        success: true,
        data: {
          resultId,
          availableMetrics,
          recommendedAnalyses: analysisEngine.getRecommendedAnalyses(processedData)
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
    console.error('Metrics retrieval error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve metrics',
      message: error.message
    });
  }
});

module.exports = router;