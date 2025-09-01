/**
 * Path validation utilities to prevent path traversal attacks
 */

const path = require('path');

class PathValidator {
    /**
     * Validate that a file path is within the allowed directory
     */
    static validatePath(filePath, allowedDir) {
        const resolvedPath = path.resolve(filePath);
        const resolvedAllowedDir = path.resolve(allowedDir);
        
        return resolvedPath.startsWith(resolvedAllowedDir);
    }

    /**
     * Sanitize and validate result ID
     */
    static validateResultId(resultId) {
        if (!resultId || typeof resultId !== 'string') {
            return null;
        }
        
        // Remove any path traversal attempts and invalid characters
        const sanitized = resultId.replace(/[^a-zA-Z0-9_-]/g, '');
        
        // Ensure it's not empty after sanitization
        if (!sanitized || sanitized.length === 0) {
            return null;
        }
        
        return sanitized;
    }

    /**
     * Create safe data path with validation
     */
    static createSafeDataPath(baseDir, resultId) {
        const safeResultId = this.validateResultId(resultId);
        if (!safeResultId) {
            throw new Error('Invalid result ID format');
        }
        
        const dataPath = path.join(baseDir, `${safeResultId}.json`);
        
        if (!this.validatePath(dataPath, baseDir)) {
            throw new Error('Invalid file path');
        }
        
        return dataPath;
    }
}

module.exports = PathValidator;