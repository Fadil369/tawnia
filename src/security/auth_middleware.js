/**
 * Production-ready authentication and authorization middleware
 * Enhanced security implementation with best practices
 */

const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const crypto = require('crypto');

// Secure JWT secret management with fallback error handling
const JWT_SECRET = process.env.JWT_SECRET || (() => {
    const fallbackSecret = crypto.randomBytes(32).toString('hex');
    console.error('CRITICAL SECURITY ERROR: JWT_SECRET environment variable not set!');
    console.error('Using temporary random secret. This will invalidate all existing tokens.');
    console.error('Set JWT_SECRET in production environment immediately!');
    return fallbackSecret;
})();

// Validate JWT secret strength
if (JWT_SECRET.length < 32) {
    console.error('SECURITY WARNING: JWT_SECRET is too short. Use at least 32 characters for production.');
}

// Token blacklist for revocation support
const revokedTokens = new Set();

// Rate limiting configuration factory
const createRateLimit = (windowMs, max, message) => rateLimit({
    windowMs,
    max,
    message: { 
        error: message,
        code: 'RATE_LIMIT_EXCEEDED',
        retryAfter: Math.ceil(windowMs / 1000)
    },
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => req.user?.id || req.ip,
    skip: (req) => req.path === '/health',
    onLimitReached: (req) => {
        console.warn(`Rate limit exceeded: ${req.ip} - User: ${req.user?.id || 'anonymous'} - Path: ${req.path}`);
    }
});

// Enhanced authentication middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ 
            error: 'Access token required',
            code: 'NO_TOKEN',
            message: 'Authorization header with Bearer token is required'
        });
    }

    // Check if token is revoked
    if (revokedTokens.has(token)) {
        return res.status(401).json({ 
            error: 'Token revoked',
            code: 'TOKEN_REVOKED',
            message: 'This token has been revoked and is no longer valid'
        });
    }

    jwt.verify(token, JWT_SECRET, {
        algorithms: ['HS256'],
        issuer: 'tawnia-healthcare-analytics',
        maxAge: '24h'
    }, (err, user) => {
        if (err) {
            let errorCode = 'INVALID_TOKEN';
            let errorMessage = 'Invalid or expired token';
            
            if (err.name === 'TokenExpiredError') {
                errorCode = 'TOKEN_EXPIRED';
                errorMessage = 'Token has expired';
            } else if (err.name === 'JsonWebTokenError') {
                errorCode = 'MALFORMED_TOKEN';
                errorMessage = 'Token format is invalid';
            }
            
            console.warn(`Authentication failed: ${errorMessage} - IP: ${req.ip}`);
            
            return res.status(403).json({ 
                error: errorMessage,
                code: errorCode,
                message: 'Authentication failed'
            });
        }
        
        // Add token metadata for security tracking
        req.user = {
            ...user,
            tokenHash: crypto.createHash('sha256').update(token).digest('hex').substring(0, 16),
            authTime: new Date(),
            ip: req.ip
        };
        
        console.log(`Authentication successful: User ${user.id || 'unknown'} from ${req.ip}`);
        next();
    });
};

// Authorization middleware
const authorize = (roles = []) => {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({ error: 'Authentication required' });
        }

        if (roles.length && !roles.includes(req.user.role)) {
            return res.status(403).json({ error: 'Insufficient permissions' });
        }

        next();
    };
};

// Security headers
const securityHeaders = helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"],
            scriptSrc: ["'self'", "https://cdn.jsdelivr.net"],
            fontSrc: ["'self'", "https://fonts.gstatic.com"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'"]
        }
    }
});

// Rate limits
const generalLimit = createRateLimit(15 * 60 * 1000, 100, 'Too many requests');
const uploadLimit = createRateLimit(60 * 60 * 1000, 10, 'Upload limit exceeded');
const authLimit = createRateLimit(15 * 60 * 1000, 5, 'Too many authentication attempts');

module.exports = {
    authenticateToken,
    authorize,
    securityHeaders,
    generalLimit,
    uploadLimit,
    authLimit
};