/**
 * Enhanced Authentication and Authorization Middleware
 */

const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');

// JWT secret from environment or default (should be changed in production)
const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production';

/**
 * Verify JWT token
 */
const verifyToken = (req, res, next) => {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
        return res.status(401).json({
            success: false,
            error: 'Access denied',
            message: 'No token provided'
        });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded;
        next();
    } catch (error) {
        return res.status(403).json({
            success: false,
            error: 'Invalid token',
            message: 'Token verification failed'
        });
    }
};

/**
 * Check if user has required role
 */
const requireRole = (roles) => {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({
                success: false,
                error: 'Authentication required'
            });
        }

        const userRoles = req.user.roles || [];
        const hasRequiredRole = roles.some(role => userRoles.includes(role));

        if (!hasRequiredRole) {
            return res.status(403).json({
                success: false,
                error: 'Insufficient permissions',
                message: `Required roles: ${roles.join(', ')}`
            });
        }

        next();
    };
};

/**
 * Rate limiting middleware
 */
const createRateLimit = (windowMs = 15 * 60 * 1000, max = 100) => {
    return rateLimit({
        windowMs,
        max,
        message: {
            success: false,
            error: 'Too many requests',
            message: 'Rate limit exceeded. Please try again later.'
        },
        standardHeaders: true,
        legacyHeaders: false,
    });
};

/**
 * API key authentication for service-to-service calls
 */
const verifyApiKey = (req, res, next) => {
    const apiKey = req.headers['x-api-key'];
    const validApiKeys = process.env.VALID_API_KEYS ? process.env.VALID_API_KEYS.split(',') : [];

    if (!apiKey || !validApiKeys.includes(apiKey)) {
        return res.status(401).json({
            success: false,
            error: 'Invalid API key'
        });
    }

    next();
};

/**
 * Generate JWT token
 */
const generateToken = (user) => {
    return jwt.sign(
        {
            id: user.id,
            email: user.email,
            roles: user.roles || ['user']
        },
        JWT_SECRET,
        { expiresIn: '24h' }
    );
};

module.exports = {
    verifyToken,
    requireRole,
    createRateLimit,
    verifyApiKey,
    generateToken
};