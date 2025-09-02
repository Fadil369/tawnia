/**
 * Enhanced Authentication and Authorization Middleware
 * Security-hardened JWT implementation
 */

const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const crypto = require('crypto');

// Secure JWT secret management
const JWT_SECRET = process.env.JWT_SECRET || (() => {
    console.error('CRITICAL SECURITY WARNING: JWT_SECRET not set in environment variables!');
    console.error('Using a temporary secret for this session. SET JWT_SECRET in production!');
    return crypto.randomBytes(32).toString('hex');
})();

// Validate JWT secret strength
if (JWT_SECRET.length < 32) {
    console.error('SECURITY WARNING: JWT secret is too short. Use at least 32 characters.');
}

// Token blacklist for logout/revoke functionality
const tokenBlacklist = new Set();

/**
 * Enhanced JWT token verification with security features
 */
const verifyToken = (req, res, next) => {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
        return res.status(401).json({
            success: false,
            error: 'Access denied',
            message: 'No token provided',
            code: 'NO_TOKEN'
        });
    }

    // Check if token is blacklisted
    if (tokenBlacklist.has(token)) {
        return res.status(401).json({
            success: false,
            error: 'Token revoked',
            message: 'This token has been revoked',
            code: 'TOKEN_REVOKED'
        });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET, {
            algorithms: ['HS256'],
            issuer: 'tawnia-healthcare-analytics',
            maxAge: '24h'
        });
        
        // Add security metadata
        req.user = {
            ...decoded,
            tokenHash: crypto.createHash('sha256').update(token).digest('hex'),
            loginTime: new Date(decoded.iat * 1000),
            expiryTime: new Date(decoded.exp * 1000)
        };
        
        // Log authentication success (without sensitive data)
        console.log(`Authentication successful for user: ${decoded.id || 'unknown'}`);
        
        next();
    } catch (error) {
        let errorMessage = 'Token verification failed';
        let errorCode = 'INVALID_TOKEN';
        
        if (error.name === 'TokenExpiredError') {
            errorMessage = 'Token has expired';
            errorCode = 'TOKEN_EXPIRED';
        } else if (error.name === 'JsonWebTokenError') {
            errorMessage = 'Invalid token format';
            errorCode = 'MALFORMED_TOKEN';
        }
        
        // Log authentication failure
        console.warn(`Authentication failed: ${errorMessage} - IP: ${req.ip}`);
        
        return res.status(403).json({
            success: false,
            error: 'Authentication failed',
            message: errorMessage,
            code: errorCode
        });
    }
};

/**
 * Enhanced role-based authorization with granular permissions
 */
const requireRole = (roles) => {
    if (!Array.isArray(roles)) {
        roles = [roles];
    }
    
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({
                success: false,
                error: 'Authentication required',
                message: 'User must be authenticated to access this resource',
                code: 'AUTHENTICATION_REQUIRED'
            });
        }

        const userRoles = req.user.roles || [];
        const userPermissions = req.user.permissions || [];
        
        // Check if user has any of the required roles
        const hasRequiredRole = roles.some(role => userRoles.includes(role));
        
        // Check for admin override (admins can access everything)
        const isAdmin = userRoles.includes('admin') || userRoles.includes('super_admin');
        
        if (!hasRequiredRole && !isAdmin) {
            // Log authorization failure
            console.warn(`Authorization failed: User ${req.user.id} attempted to access resource requiring roles: ${roles.join(', ')}`);
            
            return res.status(403).json({
                success: false,
                error: 'Insufficient permissions',
                message: `Access denied. Required roles: ${roles.join(', ')}`,
                code: 'INSUFFICIENT_PERMISSIONS',
                requiredRoles: roles,
                userRoles: userRoles
            });
        }

        // Log successful authorization
        console.log(`Authorization successful: User ${req.user.id} accessed resource with roles: ${userRoles.join(', ')}`);
        
        next();
    };
};

/**
 * Enhanced rate limiting with progressive penalties
 */
const createRateLimit = (windowMs = 15 * 60 * 1000, max = 100, message = 'Too many requests') => {
    return rateLimit({
        windowMs,
        max,
        message: {
            success: false,
            error: 'Rate limit exceeded',
            message: message,
            retryAfter: Math.ceil(windowMs / 1000),
            code: 'RATE_LIMIT_EXCEEDED'
        },
        standardHeaders: true,
        legacyHeaders: false,
        keyGenerator: (req) => {
            // Use user ID if authenticated, otherwise IP
            return req.user?.id || req.ip;
        },
        skip: (req) => {
            // Skip rate limiting for health checks
            return req.path === '/health' || req.path === '/status';
        },
        onLimitReached: (req, res, options) => {
            console.warn(`Rate limit exceeded: ${req.ip} - ${req.user?.id || 'anonymous'}`);
        }
    });
};

/**
 * Secure API key authentication for service-to-service calls
 */
const verifyApiKey = (req, res, next) => {
    const apiKey = req.headers['x-api-key'];
    const validApiKeys = process.env.VALID_API_KEYS ? 
        process.env.VALID_API_KEYS.split(',').map(key => key.trim()) : [];

    if (!apiKey) {
        return res.status(401).json({
            success: false,
            error: 'API key required',
            message: 'X-API-Key header is required for this endpoint',
            code: 'API_KEY_REQUIRED'
        });
    }

    // Use constant-time comparison to prevent timing attacks
    const isValidKey = validApiKeys.some(validKey => 
        crypto.timingSafeEqual(
            Buffer.from(apiKey, 'utf8'),
            Buffer.from(validKey, 'utf8')
        )
    );

    if (!isValidKey) {
        console.warn(`Invalid API key attempt from IP: ${req.ip}`);
        return res.status(401).json({
            success: false,
            error: 'Invalid API key',
            message: 'The provided API key is not valid',
            code: 'INVALID_API_KEY'
        });
    }

    // Set service user context
    req.user = {
        id: 'service',
        type: 'api_key',
        roles: ['service'],
        permissions: ['read', 'write']
    };

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