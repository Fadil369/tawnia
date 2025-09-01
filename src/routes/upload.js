const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const uuid = require('uuid');
const excelProcessor = require('../processors/excelProcessor');
const { verifyToken, requireRole, createRateLimit } = require('../middleware/auth');
const PathValidator = require('../utils/path_validator');

const router = express.Router();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../../uploads');
    try {
      await fs.mkdir(uploadDir, { recursive: true });
      cb(null, uploadDir);
    } catch (error) {
      cb(error);
    }
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = uuid.v4();
    const fileExtension = path.extname(file.originalname);
    const baseName = path.basename(file.originalname, fileExtension);
    cb(null, `${baseName}_${uniqueSuffix}${fileExtension}`);
  }
});

const fileFilter = (req, file, cb) => {
  const allowedExtensions = ['.xlsx', '.xls', '.csv'];
  const fileExtension = path.extname(file.originalname).toLowerCase();

  if (allowedExtensions.includes(fileExtension)) {
    cb(null, true);
  } else {
    cb(new Error(`Unsupported file format. Allowed formats: ${allowedExtensions.join(', ')}`), false);
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
    files: 10 // Maximum 10 files
  }
});

// Single file upload endpoint
router.post('/single', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        message: 'Please select a file to upload'
      });
    }

    const { originalname, filename, path: filePath, size } = req.file;

    // Process the uploaded file
    const processedData = await excelProcessor.processFile(filePath, originalname);

    // Store processing result
    const resultId = uuid.v4();
    const resultPath = path.join(__dirname, '../../data', `${resultId}.json`);

    await fs.mkdir(path.dirname(resultPath), { recursive: true });
    await fs.writeFile(resultPath, JSON.stringify(processedData, null, 2));

    // Clean up uploaded file (optional, based on requirements)
    // await fs.unlink(filePath);

    res.json({
      success: true,
      message: 'File processed successfully',
      data: {
        resultId,
        filename: originalname,
        fileSize: size,
        fileType: processedData.fileType,
        processedAt: processedData.processedAt,
        summary: processedData.summary,
        sheets: processedData.sheets.map(sheet => ({
          name: sheet.name,
          rowCount: sheet.rowCount,
          columnCount: sheet.columnCount,
          dataQuality: sheet.analysis.dataQuality
        }))
      }
    });

  } catch (error) {
    console.error('Upload processing error:', error);

    // Clean up file if processing failed
    if (req.file && req.file.path) {
      try {
        await fs.unlink(req.file.path);
      } catch (cleanupError) {
        console.error('Failed to clean up file:', cleanupError);
      }
    }

    res.status(500).json({
      success: false,
      error: 'Processing failed',
      message: error.message
    });
  }
});

// Multiple file upload endpoint
router.post('/multiple', upload.array('files', 10), async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No files uploaded',
        message: 'Please select files to upload'
      });
    }

    const results = [];
    const errors = [];

    // Process each file
    for (const file of req.files) {
      try {
        const { originalname, filename, path: filePath, size } = file;

        const processedData = await excelProcessor.processFile(filePath, originalname);

        // Store processing result
        const resultId = uuid.v4();
        const resultPath = path.join(__dirname, '../../data', `${resultId}.json`);

        await fs.mkdir(path.dirname(resultPath), { recursive: true });
        await fs.writeFile(resultPath, JSON.stringify(processedData, null, 2));

        results.push({
          resultId,
          filename: originalname,
          fileSize: size,
          fileType: processedData.fileType,
          processedAt: processedData.processedAt,
          summary: processedData.summary,
          status: 'success'
        });

      } catch (error) {
        errors.push({
          filename: file.originalname,
          error: error.message,
          status: 'failed'
        });

        // Clean up failed file
        try {
          await fs.unlink(file.path);
        } catch (cleanupError) {
          console.error('Failed to clean up file:', cleanupError);
        }
      }
    }

    res.json({
      success: results.length > 0,
      message: `Processed ${results.length} of ${req.files.length} files successfully`,
      data: {
        successful: results,
        failed: errors,
        summary: {
          totalFiles: req.files.length,
          successfulFiles: results.length,
          failedFiles: errors.length
        }
      }
    });

  } catch (error) {
    console.error('Multiple upload processing error:', error);

    // Clean up all files if batch processing failed
    if (req.files) {
      for (const file of req.files) {
        try {
          await fs.unlink(file.path);
        } catch (cleanupError) {
          console.error('Failed to clean up file:', cleanupError);
        }
      }
    }

    res.status(500).json({
      success: false,
      error: 'Batch processing failed',
      message: error.message
    });
  }
});

// Get processing status endpoint
router.get('/status/:resultId', async (req, res) => {
  try {
    const { resultId } = req.params;
    const resultPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      const data = await fs.readFile(resultPath, 'utf8');
      const processedData = JSON.parse(data);

      res.json({
        success: true,
        data: {
          resultId,
          status: 'completed',
          filename: processedData.filename,
          fileType: processedData.fileType,
          processedAt: processedData.processedAt,
          summary: processedData.summary
        }
      });
    } catch (fileError) {
      res.status(404).json({
        success: false,
        error: 'Result not found',
        message: 'The specified result ID was not found'
      });
    }

  } catch (error) {
    console.error('Status check error:', error);
    res.status(500).json({
      success: false,
      error: 'Status check failed',
      message: error.message
    });
  }
});

// Get detailed results endpoint
router.get('/results/:resultId', async (req, res) => {
  try {
    const { resultId } = req.params;
    const resultPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      const data = await fs.readFile(resultPath, 'utf8');
      const processedData = JSON.parse(data);

      res.json({
        success: true,
        data: processedData
      });
    } catch (fileError) {
      res.status(404).json({
        success: false,
        error: 'Result not found',
        message: 'The specified result ID was not found'
      });
    }

  } catch (error) {
    console.error('Results retrieval error:', error);
    res.status(500).json({
      success: false,
      error: 'Results retrieval failed',
      message: error.message
    });
  }
});

// List all processed files endpoint
router.get('/list', async (req, res) => {
  try {
    const dataDir = path.join(__dirname, '../../data');

    try {
      const files = await fs.readdir(dataDir);
      const jsonFiles = files.filter(file => file.endsWith('.json'));

      const fileList = [];

      for (const file of jsonFiles) {
        try {
          const filePath = path.join(dataDir, file);
          const data = await fs.readFile(filePath, 'utf8');
          const processedData = JSON.parse(data);

          fileList.push({
            resultId: path.basename(file, '.json'),
            filename: processedData.filename,
            fileType: processedData.fileType,
            processedAt: processedData.processedAt,
            totalSheets: processedData.summary.totalSheets,
            totalRows: processedData.summary.totalDataRows,
            overallQuality: processedData.summary.overallQuality
          });
        } catch (parseError) {
          console.error(`Failed to parse file ${file}:`, parseError);
        }
      }

      // Sort by processed date (newest first)
      fileList.sort((a, b) => new Date(b.processedAt) - new Date(a.processedAt));

      res.json({
        success: true,
        data: {
          files: fileList,
          total: fileList.length
        }
      });

    } catch (dirError) {
      // Directory doesn't exist yet
      res.json({
        success: true,
        data: {
          files: [],
          total: 0
        }
      });
    }

  } catch (error) {
    console.error('File list error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve file list',
      message: error.message
    });
  }
});

// Delete processed result endpoint (requires admin role)
router.delete('/results/:resultId', verifyToken, requireRole(['admin']), async (req, res) => {
  try {
    const { resultId } = req.params;
    const resultPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      await fs.unlink(resultPath);
      res.json({
        success: true,
        message: 'Result deleted successfully'
      });
    } catch (fileError) {
      res.status(404).json({
        success: false,
        error: 'Result not found',
        message: 'The specified result ID was not found'
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

module.exports = router;
