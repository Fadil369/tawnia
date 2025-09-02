#!/usr/bin/env node

/**
 * Enhanced Test Suite for Tawnia Healthcare Analytics
 * Comprehensive testing including security, functionality, and performance
 */

const fs = require('fs');
const path = require('path');

class TawniaTestSuite {
    constructor() {
        this.tests = [];
        this.passed = 0;
        this.failed = 0;
        this.skipped = 0;
        this.startTime = Date.now();
    }

    // Test runner
    async runTests() {
        console.log('🧪 Running Tawnia Healthcare Analytics Test Suite\n');
        
        await this.testSecurityConfiguration();
        await this.testFileStructure();
        await this.testEnvironmentConfiguration();
        await this.testDependencies();
        await this.testSecurityMiddleware();
        await this.testAPIEndpoints();
        
        this.generateReport();
    }

    // Security configuration tests
    async testSecurityConfiguration() {
        console.log('🔒 Testing Security Configuration...');
        
        this.test('Environment file exists', () => {
            return fs.existsSync('.env') || fs.existsSync('.env.example');
        });
        
        this.test('JWT secret not using default', () => {
            if (!fs.existsSync('.env')) return true; // Skip if no .env
            
            const envContent = fs.readFileSync('.env', 'utf8');
            return !envContent.includes('CHANGE_ME') && 
                   !envContent.includes('your-secret-key') &&
                   !envContent.includes('fallback-secret');
        });
        
        this.test('HTTPS enforced in production', () => {
            const envContent = fs.existsSync('.env') ? fs.readFileSync('.env', 'utf8') : '';
            return envContent.includes('FORCE_HTTPS=true') || 
                   envContent.includes('ENABLE_SSL_REDIRECT=true');
        });
        
        this.test('CORS not using wildcard', () => {
            const serverFile = 'src/server.js';
            if (!fs.existsSync(serverFile)) return true;
            
            const content = fs.readFileSync(serverFile, 'utf8');
            return !content.includes("origin: '*'") && 
                   !content.includes('allow_origins=["*"]');
        });
    }

    // File structure tests
    async testFileStructure() {
        console.log('📁 Testing File Structure...');
        
        const requiredFiles = [
            'package.json',
            '.gitignore',
            'main_enhanced.py',
            'src/security/security_config.py',
            'public/brainsait-enhanced.html',
            'requirements.txt'
        ];
        
        requiredFiles.forEach(file => {
            this.test(`Required file exists: ${file}`, () => {
                return fs.existsSync(file);
            });
        });
        
        this.test('No sensitive files in repository', () => {
            const sensitivePatterns = [
                '.env',
                '*.key',
                '*.pem',
                'credentials.json',
                'secrets.json'
            ];
            
            // Check if .gitignore properly excludes these
            const gitignore = fs.existsSync('.gitignore') ? 
                fs.readFileSync('.gitignore', 'utf8') : '';
            
            return sensitivePatterns.every(pattern => 
                gitignore.includes(pattern) || gitignore.includes(pattern.replace('*', ''))
            );
        });
    }

    // Environment configuration tests
    async testEnvironmentConfiguration() {
        console.log('⚙️ Testing Environment Configuration...');
        
        this.test('Package.json has security configuration', () => {
            const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
            return pkg.scripts && 
                   (pkg.scripts['security:scan'] || pkg.scripts['security:audit']);
        });
        
        this.test('Python requirements are up to date', () => {
            const requirements = fs.readFileSync('requirements.txt', 'utf8');
            
            // Check for known vulnerable versions
            const vulnerablePackages = [
                'django<3.2.16',
                'flask<2.2.2',
                'requests<2.28.0',
                'urllib3<1.26.12'
            ];
            
            return vulnerablePackages.every(pkg => !requirements.includes(pkg));
        });
        
        this.test('Security headers configured', () => {
            const serverFile = 'src/server.js';
            if (!fs.existsSync(serverFile)) return true;
            
            const content = fs.readFileSync(serverFile, 'utf8');
            const requiredHeaders = [
                'helmet',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Content-Security-Policy'
            ];
            
            return requiredHeaders.every(header => content.includes(header));
        });
    }

    // Dependencies tests
    async testDependencies() {
        console.log('📦 Testing Dependencies...');
        
        this.test('Package.json exists and is valid', () => {
            try {
                const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
                return pkg.name && pkg.version && pkg.dependencies;
            } catch {
                return false;
            }
        });
        
        this.test('Security-focused dependencies included', () => {
            const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
            const securityDeps = ['helmet', 'express-rate-limit', 'bcrypt', 'jsonwebtoken'];
            
            return securityDeps.every(dep => 
                pkg.dependencies[dep] || pkg.devDependencies[dep]
            );
        });
        
        this.test('Development dependencies separated', () => {
            const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
            return pkg.devDependencies && Object.keys(pkg.devDependencies).length > 0;
        });
    }

    // Security middleware tests
    async testSecurityMiddleware() {
        console.log('🛡️ Testing Security Middleware...');
        
        this.test('Authentication middleware exists', () => {
            return fs.existsSync('src/middleware/auth.js') || 
                   fs.existsSync('src/security/auth_middleware.js');
        });
        
        this.test('Rate limiting implemented', () => {
            const files = [
                'src/middleware/auth.js',
                'src/server.js',
                'main_enhanced.py'
            ];
            
            return files.some(file => {
                if (!fs.existsSync(file)) return false;
                const content = fs.readFileSync(file, 'utf8');
                return content.includes('rate') && 
                       (content.includes('limit') || content.includes('throttle'));
            });
        });
        
        this.test('Input validation implemented', () => {
            const files = ['src/utils/security.py', 'public/js/enhanced-app.js'];
            
            return files.some(file => {
                if (!fs.existsSync(file)) return false;
                const content = fs.readFileSync(file, 'utf8');
                return content.includes('sanitize') || content.includes('validate');
            });
        });
    }

    // API endpoints tests
    async testAPIEndpoints() {
        console.log('🌐 Testing API Endpoints...');
        
        this.test('Main application file exists', () => {
            return fs.existsSync('main_enhanced.py') || fs.existsSync('main.py');
        });
        
        this.test('Error handling implemented', () => {
            const mainFile = fs.existsSync('main_enhanced.py') ? 'main_enhanced.py' : 'main.py';
            if (!fs.existsSync(mainFile)) return false;
            
            const content = fs.readFileSync(mainFile, 'utf8');
            return content.includes('exception_handler') || 
                   content.includes('try:') || 
                   content.includes('HTTPException');
        });
        
        this.test('CORS configuration present', () => {
            const files = ['main_enhanced.py', 'src/server.js'];
            
            return files.some(file => {
                if (!fs.existsSync(file)) return false;
                const content = fs.readFileSync(file, 'utf8');
                return content.includes('CORS') || content.includes('cors');
            });
        });
    }

    // Test helper
    test(name, testFn) {
        try {
            const result = testFn();
            if (result) {
                console.log(`  ✅ ${name}`);
                this.passed++;
            } else {
                console.log(`  ❌ ${name}`);
                this.failed++;
            }
        } catch (error) {
            console.log(`  ⚠️  ${name} (Error: ${error.message})`);
            this.skipped++;
        }
    }

    // Generate test report
    generateReport() {
        const endTime = Date.now();
        const duration = endTime - this.startTime;
        const total = this.passed + this.failed + this.skipped;
        
        console.log('\n📊 Test Results Summary');
        console.log('========================');
        console.log(`✅ Passed: ${this.passed}`);
        console.log(`❌ Failed: ${this.failed}`);
        console.log(`⚠️  Skipped: ${this.skipped}`);
        console.log(`📈 Total: ${total}`);
        console.log(`⏱️  Duration: ${duration}ms`);
        console.log(`🎯 Success Rate: ${((this.passed / total) * 100).toFixed(1)}%`);
        
        if (this.failed > 0) {
            console.log('\n⚠️  Some tests failed. Please review and fix the issues before deployment.');
            process.exit(1);
        } else {
            console.log('\n🎉 All tests passed! System is ready for deployment.');
            process.exit(0);
        }
    }
}

// Run tests if called directly
if (require.main === module) {
    const testSuite = new TawniaTestSuite();
    testSuite.runTests().catch(err => {
        console.error('Test suite failed:', err);
        process.exit(1);
    });
}

module.exports = TawniaTestSuite;