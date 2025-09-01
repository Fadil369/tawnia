const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const analysisEngine = require('../analysis/analysisEngine');

const router = express.Router();

/**
 * Analyze rejection patterns in processed data
 */
router.post('/rejections', async (req, res) => {
  try {
    const { resultId, analysisType = 'comprehensive' } = req.body;

    if (!resultId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Result ID is required for analysis'
      });
    }

    // Load processed data
    const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      // Perform rejection analysis
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
 * Analyze trends in healthcare data
 */
router.post('/trends', async (req, res) => {
  try {
    const { resultId, timeframe = 'monthly', metrics = ['claims', 'rejections'] } = req.body;

    if (!resultId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Result ID is required for trend analysis'
      });
    }

    // Load processed data
    const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      // Perform trend analysis
      const trendAnalysis = await analysisEngine.analyzeTrends(processedData, timeframe, metrics);

      res.json({
        success: true,
        message: 'Trend analysis completed successfully',
        data: {
          resultId,
          timeframe,
          metrics,
          trendAnalysis,
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
    console.error('Trend analysis error:', error);
    res.status(500).json({
      success: false,
      error: 'Analysis failed',
      message: error.message
    });
  }
});

/**
 * Analyze patterns across multiple files
 */
router.post('/patterns', async (req, res) => {
  try {
    const { resultIds, patternTypes = ['claims', 'rejections', 'providers'] } = req.body;

    if (!resultIds || !Array.isArray(resultIds) || resultIds.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Array of result IDs is required for pattern analysis'
      });
    }

    const processedDatasets = [];
    const errors = [];

    // Load all specified datasets
    for (const resultId of resultIds) {
      try {
        const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);
        const rawData = await fs.readFile(dataPath, 'utf8');
        const processedData = JSON.parse(rawData);
        processedDatasets.push(processedData);
      } catch (fileError) {
        errors.push({
          resultId,
          error: 'File not found or corrupted'
        });
      }
    }

    if (processedDatasets.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'No valid data found',
        message: 'None of the specified result IDs could be loaded'
      });
    }

    // Perform cross-file pattern analysis
    const patternAnalysis = await analysisEngine.analyzePatterns(processedDatasets, patternTypes);

    res.json({
      success: true,
      message: 'Pattern analysis completed successfully',
      data: {
        resultIds,
        patternTypes,
        processedFiles: processedDatasets.length,
        errors,
        patternAnalysis,
        processedAt: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('Pattern analysis error:', error);
    res.status(500).json({
      success: false,
      error: 'Analysis failed',
      message: error.message
    });
  }
});

/**
 * Perform comprehensive data quality analysis
 */
router.post('/quality', async (req, res) => {
  try {
    const { resultId, includeRecommendations = true } = req.body;

    if (!resultId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Result ID is required for quality analysis'
      });
    }

    // Load processed data
    const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      // Perform quality analysis
      const qualityAnalysis = await analysisEngine.analyzeDataQuality(processedData, includeRecommendations);

      res.json({
        success: true,
        message: 'Data quality analysis completed successfully',
        data: {
          resultId,
          qualityAnalysis,
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
    console.error('Quality analysis error:', error);
    res.status(500).json({
      success: false,
      error: 'Analysis failed',
      message: error.message
    });
  }
});

/**
 * Generate comparative analysis between files
 */
router.post('/compare', async (req, res) => {
  try {
    const { resultIds, comparisonMetrics = ['volume', 'quality', 'rejections'] } = req.body;

    if (!resultIds || !Array.isArray(resultIds) || resultIds.length < 2) {
      return res.status(400).json({
        success: false,
        error: 'Invalid parameters',
        message: 'At least two result IDs are required for comparison'
      });
    }

    const processedDatasets = [];
    const errors = [];

    // Load all specified datasets
    for (const resultId of resultIds) {
      try {
        const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);
        const rawData = await fs.readFile(dataPath, 'utf8');
        const processedData = JSON.parse(rawData);
        processedDatasets.push({
          resultId,
          data: processedData
        });
      } catch (fileError) {
        errors.push({
          resultId,
          error: 'File not found or corrupted'
        });
      }
    }

    if (processedDatasets.length < 2) {
      return res.status(400).json({
        success: false,
        error: 'Insufficient data',
        message: 'At least two valid datasets are required for comparison'
      });
    }

    // Perform comparative analysis
    const comparisonAnalysis = await analysisEngine.compareDatasets(processedDatasets, comparisonMetrics);

    res.json({
      success: true,
      message: 'Comparative analysis completed successfully',
      data: {
        resultIds,
        comparisonMetrics,
        processedFiles: processedDatasets.length,
        errors,
        comparisonAnalysis,
        processedAt: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('Comparison analysis error:', error);
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
router.get('/metrics/:resultId', async (req, res) => {
  try {
    const { resultId } = req.params;

    // Load processed data
    const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      // Extract available metrics
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

/**
 * Run batch analysis on multiple files
 */
router.post('/batch', async (req, res) => {
  try {
    const { resultIds, analysisTypes = ['rejections', 'trends', 'quality'] } = req.body;

    if (!resultIds || !Array.isArray(resultIds) || resultIds.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Array of result IDs is required for batch analysis'
      });
    }

    const batchResults = [];
    const errors = [];

    // Process each file
    for (const resultId of resultIds) {
      try {
        const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);
        const rawData = await fs.readFile(dataPath, 'utf8');
        const processedData = JSON.parse(rawData);

        const fileAnalysis = {
          resultId,
          filename: processedData.filename,
          analyses: {}
        };

        // Run each requested analysis type
        for (const analysisType of analysisTypes) {
          try {
            switch (analysisType) {
              case 'rejections':
                fileAnalysis.analyses.rejections = await analysisEngine.analyzeRejections(processedData);
                break;
              case 'trends':
                fileAnalysis.analyses.trends = await analysisEngine.analyzeTrends(processedData);
                break;
              case 'quality':
                fileAnalysis.analyses.quality = await analysisEngine.analyzeDataQuality(processedData);
                break;
              case 'patterns':
                fileAnalysis.analyses.patterns = await analysisEngine.analyzePatterns([processedData]);
                break;
            }
          } catch (analysisError) {
            fileAnalysis.analyses[analysisType] = {
              error: analysisError.message
            };
          }
        }

        batchResults.push(fileAnalysis);

      } catch (fileError) {
        errors.push({
          resultId,
          error: 'File not found or corrupted'
        });
      }
    }

    res.json({
      success: true,
      message: `Batch analysis completed for ${batchResults.length} files`,
      data: {
        analysisTypes,
        results: batchResults,
        errors,
        summary: {
          totalRequested: resultIds.length,
          successful: batchResults.length,
          failed: errors.length
        },
        processedAt: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('Batch analysis error:', error);
    res.status(500).json({
      success: false,
      error: 'Batch analysis failed',
      message: error.message
    });
  }
});

module.exports = router;
