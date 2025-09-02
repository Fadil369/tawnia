#!/usr/bin/env node

/**
 * Security Scanner for Tawnia Healthcare Analytics
 * Checks for common security vulnerabilities and best practices
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class SecurityScanner {
  constructor() {
    this.issues = [];
    this.warnings = [];
    this.passed = [];
  }

  // Check for hardcoded secrets
  checkHardcodedSecrets() {
    const patterns = [
      /(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]{3,}/i,
      /(?:secret|token|key)\s*[:=]\s*['"][^'"]{8,}/i,
      /(?:api_key|apikey)\s*[:=]\s*['"][^'"]{8,}/i,
      /-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----/,
      /sk_live_[a-zA-Z0-9]{24,}/,
      /pk_live_[a-zA-Z0-9]{24,}/
    ];

    const filesToCheck = this.getFilesToScan();
    
    filesToCheck.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');
        patterns.forEach((pattern, index) => {
          if (pattern.test(content)) {
            this.issues.push({
              type: 'HARDCODED_SECRET',
              severity: 'HIGH',
              file: file,
              description: `Potential hardcoded secret found (pattern ${index + 1})`,
              line: this.getLineNumber(content, pattern)
            });
          }
        });
      } catch (err) {
        // Skip files that can't be read
      }
    });
  }

  // Check environment configuration
  checkEnvironmentConfig() {
    const envFile = path.join(__dirname, '.env');
    const envExampleFile = path.join(__dirname, '.env.example');
    
    if (!fs.existsSync(envFile)) {
      this.warnings.push({
        type: 'MISSING_ENV',
        severity: 'MEDIUM',
        description: '.env file not found - ensure it exists in production'
      });
    } else {
      const envContent = fs.readFileSync(envFile, 'utf8');
      
      // Check for default values
      const defaultPatterns = [
        /JWT_SECRET.*=.*CHANGE.*ME/i,
        /SECRET_KEY.*=.*CHANGE.*ME/i,
        /password.*=.*password/i,
        /secret.*=.*secret/i
      ];
      
      defaultPatterns.forEach(pattern => {
        if (pattern.test(envContent)) {
          this.issues.push({
            type: 'DEFAULT_SECRET',
            severity: 'CRITICAL',
            file: '.env',
            description: 'Default or weak secret found in environment file'
          });
        }
      });
    }
  }

  // Check CORS configuration
  checkCORSConfig() {
    const serverFiles = [
      'src/server.js',
      'main_enhanced.py',
      'src/worker.ts'
    ];

    serverFiles.forEach(file => {
      const filePath = path.join(__dirname, file);
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf8');
        
        // Check for wildcard CORS
        if (content.includes("origin: '*'") || content.includes('allow_origins=["*"]')) {
          this.issues.push({
            type: 'WILDCARD_CORS',
            severity: 'HIGH',
            file: file,
            description: 'Wildcard CORS origin detected - restricts access in production'
          });
        }
        
        // Check for localhost in production
        if (content.includes('localhost') && process.env.NODE_ENV === 'production') {
          this.warnings.push({
            type: 'LOCALHOST_CORS',
            severity: 'MEDIUM',
            file: file,
            description: 'Localhost found in CORS config - remove for production'
          });
        }
      }
    });
  }

  // Check for SQL injection vulnerabilities
  checkSQLInjection() {
    const filesToCheck = this.getFilesToScan();
    
    filesToCheck.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');
        
        // Look for string concatenation in SQL queries
        const sqlPatterns = [
          /(?:SELECT|INSERT|UPDATE|DELETE).*\+.*['"`]/i,
          /(?:WHERE|SET).*\+.*['"`]/i,
          /f["'].*(?:SELECT|INSERT|UPDATE|DELETE)/i
        ];
        
        sqlPatterns.forEach(pattern => {
          if (pattern.test(content)) {
            this.warnings.push({
              type: 'POTENTIAL_SQL_INJECTION',
              severity: 'HIGH',
              file: file,
              description: 'Potential SQL injection vulnerability - use parameterized queries'
            });
          }
        });
      } catch (err) {
        // Skip files that can't be read
      }
    });
  }

  // Check for XSS vulnerabilities
  checkXSSVulnerabilities() {
    const filesToCheck = this.getFilesToScan();
    
    filesToCheck.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');
        
        // Look for innerHTML with variables
        const xssPatterns = [
          /innerHTML\s*=\s*[^'"]/,
          /document\.write\s*\(/,
          /eval\s*\(/,
          /Function\s*\(/
        ];
        
        xssPatterns.forEach(pattern => {
          if (pattern.test(content)) {
            this.warnings.push({
              type: 'POTENTIAL_XSS',
              severity: 'MEDIUM',
              file: file,
              description: 'Potential XSS vulnerability - sanitize user input'
            });
          }
        });
      } catch (err) {
        // Skip files that can't be read
      }
    });
  }

  // Check file permissions
  checkFilePermissions() {
    const sensitiveFiles = [
      '.env',
      'src/security/',
      'credentials/',
      'secrets/'
    ];
    
    sensitiveFiles.forEach(file => {
      const filePath = path.join(__dirname, file);
      if (fs.existsSync(filePath)) {
        try {
          const stats = fs.statSync(filePath);
          const mode = (stats.mode & parseInt('777', 8)).toString(8);
          
          if (mode > '600' && file.includes('.env')) {
            this.warnings.push({
              type: 'INSECURE_PERMISSIONS',
              severity: 'MEDIUM',
              file: file,
              description: `File permissions too permissive: ${mode}`
            });
          }
        } catch (err) {
          // Skip permission check on Windows or other errors
        }
      }
    });
  }

  // Helper methods
  getFilesToScan() {
    const files = [];
    const extensions = ['.js', '.py', '.ts', '.html', '.json'];
    
    const scanDirectory = (dir) => {
      try {
        const items = fs.readdirSync(dir);
        items.forEach(item => {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);
          
          if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
            scanDirectory(fullPath);
          } else if (extensions.some(ext => item.endsWith(ext))) {
            files.push(fullPath);
          }
        });
      } catch (err) {
        // Skip directories that can't be read
      }
    };
    
    scanDirectory(__dirname);
    return files;
  }

  getLineNumber(content, pattern) {
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (pattern.test(lines[i])) {
        return i + 1;
      }
    }
    return null;
  }

  // Run all security checks
  async runScan() {
    console.log('🔒 Starting Tawnia Security Scan...\n');
    
    this.checkHardcodedSecrets();
    this.checkEnvironmentConfig();
    this.checkCORSConfig();
    this.checkSQLInjection();
    this.checkXSSVulnerabilities();
    this.checkFilePermissions();
    
    // Generate report
    this.generateReport();
  }

  generateReport() {
    console.log('📋 Security Scan Results');
    console.log('========================\n');
    
    // Critical issues
    const criticalIssues = this.issues.filter(i => i.severity === 'CRITICAL');
    if (criticalIssues.length > 0) {
      console.log('🚨 CRITICAL ISSUES:');
      criticalIssues.forEach(issue => {
        console.log(`   ${issue.type}: ${issue.description}`);
        if (issue.file) console.log(`   File: ${issue.file}`);
        if (issue.line) console.log(`   Line: ${issue.line}`);
        console.log('');
      });
    }
    
    // High severity issues
    const highIssues = this.issues.filter(i => i.severity === 'HIGH');
    if (highIssues.length > 0) {
      console.log('⚠️  HIGH SEVERITY ISSUES:');
      highIssues.forEach(issue => {
        console.log(`   ${issue.type}: ${issue.description}`);
        if (issue.file) console.log(`   File: ${issue.file}`);
        if (issue.line) console.log(`   Line: ${issue.line}`);
        console.log('');
      });
    }
    
    // Warnings
    if (this.warnings.length > 0) {
      console.log('⚡ WARNINGS:');
      this.warnings.forEach(warning => {
        console.log(`   ${warning.type}: ${warning.description}`);
        if (warning.file) console.log(`   File: ${warning.file}`);
        console.log('');
      });
    }
    
    // Summary
    const totalIssues = this.issues.length + this.warnings.length;
    console.log(`📊 SUMMARY:`);
    console.log(`   Critical Issues: ${criticalIssues.length}`);
    console.log(`   High Severity: ${highIssues.length}`);
    console.log(`   Warnings: ${this.warnings.length}`);
    console.log(`   Total Issues: ${totalIssues}\n`);
    
    if (totalIssues === 0) {
      console.log('✅ No security issues found!');
      process.exit(0);
    } else if (criticalIssues.length > 0) {
      console.log('❌ Critical security issues found! Fix immediately before deployment.');
      process.exit(1);
    } else {
      console.log('⚠️  Security issues found. Review and fix before production deployment.');
      process.exit(0);
    }
  }
}

// Run the security scan
if (require.main === module) {
  const scanner = new SecurityScanner();
  scanner.runScan().catch(err => {
    console.error('Security scan failed:', err);
    process.exit(1);
  });
}

module.exports = SecurityScanner;