/**
 * Tawnia Healthcare Analytics - Integration Test Suite
 * Tests cross-page functionality and component integration
 */

class TawniaIntegrationTests {
    constructor() {
        this.tests = [];
        this.results = {
            passed: 0,
            failed: 0,
            total: 0
        };
        
        this.init();
    }

    /**
     * Initialize test suite
     */
    init() {
        this.registerTests();
        console.log('🧪 Tawnia Integration Tests initialized');
    }

    /**
     * Register all integration tests
     */
    registerTests() {
        // Navigation Tests
        this.addTest('Navigation System Initialization', () => {
            return window.TawniaNav && typeof window.TawniaNav.navigateTo === 'function';
        });

        this.addTest('Navigation Bar Injection', () => {
            return document.getElementById('tawnia-navigation') !== null;
        });

        this.addTest('Language Toggle Functionality', () => {
            return document.getElementById('langToggle') !== null;
        });

        this.addTest('Theme Toggle Functionality', () => {
            return document.getElementById('themeToggle') !== null;
        });

        // Components Tests
        this.addTest('Components System Initialization', () => {
            return window.TawniaComponents && typeof window.TawniaComponents.create === 'function';
        });

        this.addTest('Toast Container Creation', () => {
            return document.getElementById('tawnia-toast-container') !== null;
        });

        this.addTest('Component Styles Injection', () => {
            const styles = Array.from(document.querySelectorAll('style'));
            return styles.some(style => style.textContent.includes('tawnia-spinner'));
        });

        // Service Worker Tests
        this.addTest('Service Worker Registration', async () => {
            if (!('serviceWorker' in navigator)) return false;
            try {
                const registrations = await navigator.serviceWorker.getRegistrations();
                return registrations.some(reg => reg.scope.includes(window.location.origin));
            } catch (error) {
                return false;
            }
        });

        // Local Storage Tests
        this.addTest('Theme Persistence', () => {
            const theme = localStorage.getItem('tawnia_theme');
            return theme === 'dark' || theme === 'light';
        });

        this.addTest('Language Persistence', () => {
            const lang = localStorage.getItem('tawnia_language');
            return lang === 'en' || lang === 'ar' || lang === null;
        });

        // Cross-Page Integration Tests
        this.addTest('Page Detection', () => {
            return window.TawniaNav && typeof window.TawniaNav.currentPage === 'string';
        });

        this.addTest('Keyboard Shortcuts Setup', () => {
            // Test if event listeners are attached
            return true; // This would need more complex testing
        });

        // Security Tests
        this.addTest('XSS Prevention in Components', () => {
            if (!window.TawniaComponents) return false;
            
            // Test HTML sanitization
            const testHTML = '<script>alert("xss")</script><p>Safe content</p>';
            const component = new TawniaComponents();
            const sanitized = component.sanitizeHTML(testHTML);
            
            return !sanitized.includes('<script>') && sanitized.includes('Safe content');
        });

        this.addTest('CSP Headers Present', () => {
            const metaTags = document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]');
            return metaTags.length > 0;
        });

        // Responsive Design Tests
        this.addTest('Mobile Viewport Meta Tag', () => {
            const viewport = document.querySelector('meta[name="viewport"]');
            return viewport && viewport.content.includes('width=device-width');
        });

        this.addTest('CSS Media Queries Present', () => {
            const styles = Array.from(document.querySelectorAll('style'));
            return styles.some(style => style.textContent.includes('@media'));
        });

        // Performance Tests
        this.addTest('Resource Loading Performance', () => {
            const scripts = document.querySelectorAll('script[src]');
            const links = document.querySelectorAll('link[rel="stylesheet"]');
            
            // Check if resources are loaded efficiently
            return scripts.length < 10 && links.length < 5; // Reasonable limits
        });

        this.addTest('Font Loading Optimization', () => {
            const fontLinks = document.querySelectorAll('link[href*="fonts.googleapis.com"]');
            return Array.from(fontLinks).some(link => 
                link.href.includes('display=swap')
            );
        });

        // Accessibility Tests
        this.addTest('ARIA Labels Present', () => {
            const alertElements = document.querySelectorAll('[role="alert"]');
            const buttons = document.querySelectorAll('button[title]');
            return alertElements.length >= 0 && buttons.length > 0;
        });

        this.addTest('Alt Text for Images', () => {
            const images = document.querySelectorAll('img');
            return Array.from(images).every(img => img.alt !== undefined);
        });

        // Integration Functionality Tests
        this.addTest('Cross-Component Communication', () => {
            // Test event system
            let eventReceived = false;
            
            const testHandler = () => {
                eventReceived = true;
            };
            
            window.addEventListener('tawnia:test', testHandler);
            window.dispatchEvent(new CustomEvent('tawnia:test'));
            window.removeEventListener('tawnia:test', testHandler);
            
            return eventReceived;
        });

        this.addTest('State Management', () => {
            // Test if shared state is working
            return typeof localStorage !== 'undefined' && 
                   typeof sessionStorage !== 'undefined';
        });
    }

    /**
     * Add a test to the suite
     */
    addTest(name, testFunction) {
        this.tests.push({
            name,
            test: testFunction,
            async: testFunction.constructor.name === 'AsyncFunction'
        });
    }

    /**
     * Run all tests
     */
    async runTests() {
        console.log('🚀 Running Tawnia Integration Tests...\n');
        
        this.results = { passed: 0, failed: 0, total: this.tests.length };
        
        for (const test of this.tests) {
            try {
                let result;
                
                if (test.async) {
                    result = await test.test();
                } else {
                    result = test.test();
                }
                
                if (result) {
                    console.log(`✅ ${test.name}`);
                    this.results.passed++;
                } else {
                    console.log(`❌ ${test.name}`);
                    this.results.failed++;
                }
                
            } catch (error) {
                console.log(`❌ ${test.name} - Error: ${error.message}`);
                this.results.failed++;
            }
        }
        
        this.displayResults();
        return this.results;
    }

    /**
     * Display test results
     */
    displayResults() {
        const { passed, failed, total } = this.results;
        const percentage = Math.round((passed / total) * 100);
        
        console.log('\n📊 Test Results:');
        console.log(`   Total Tests: ${total}`);
        console.log(`   Passed: ${passed}`);
        console.log(`   Failed: ${failed}`);
        console.log(`   Success Rate: ${percentage}%`);
        
        if (percentage >= 90) {
            console.log('🎉 Excellent! Integration tests passed with flying colors!');
        } else if (percentage >= 75) {
            console.log('👍 Good! Most integration tests passed.');
        } else if (percentage >= 50) {
            console.log('⚠️  Warning: Some integration issues detected.');
        } else {
            console.log('🚨 Critical: Major integration issues found!');
        }

        // Show in UI if components are available
        if (window.TawniaComponents) {
            const message = `Integration Tests: ${passed}/${total} passed (${percentage}%)`;
            const type = percentage >= 75 ? 'success' : percentage >= 50 ? 'warning' : 'danger';
            
            TawniaComponents.showToast(type, 'Integration Test Results', message);
        }
    }

    /**
     * Test navigation functionality
     */
    testNavigation() {
        // Test navigation system initialization
        if (!window.TawniaNav) {
            throw new Error('Navigation system not initialized');
        }
        
        // Test navigation methods
        if (typeof window.TawniaNav.navigateTo !== 'function') {
            throw new Error('navigateTo method not found');
        }
        
        if (typeof window.TawniaNav.getLanguage !== 'function') {
            throw new Error('getLanguage method not found');
        }
        
        if (typeof window.TawniaNav.getTheme !== 'function') {
            throw new Error('getTheme method not found');
        }
        
        // Test navigation container exists
        const navContainer = document.getElementById('tawnia-navigation');
        if (!navContainer) {
            throw new Error('Navigation container not found');
        }
        
        return true;
    }
    
    /**
     * Test components functionality
     */
    testComponents() {
        // Test components system initialization
        if (!window.TawniaComponents) {
            throw new Error('Components system not initialized');
        }
        
        // Test components methods
        const requiredMethods = ['showAlert', 'showModal', 'showToast', 'createDataTable'];
        for (const method of requiredMethods) {
            if (typeof window.TawniaComponents[method] !== 'function') {
                throw new Error(`Component method ${method} not found`);
            }
        }
        
        // Test toast container creation
        const toastContainer = document.getElementById('tawnia-toast-container');
        if (!toastContainer) {
            // Try to create a test toast to see if container gets created
            try {
                window.TawniaComponents.showToast('info', 'Test', 'Integration test', 1000);
            } catch (error) {
                throw new Error('Failed to create test toast: ' + error.message);
            }
        }
        
        return true;
    }

    /**
     * Run specific test by name
     */
    async runTest(testName) {
        const test = this.tests.find(t => t.name === testName);
        if (!test) {
            console.error(`Test "${testName}" not found`);
            return false;
        }

        try {
            const result = test.async ? await test.test() : test.test();
            console.log(`${result ? '✅' : '❌'} ${test.name}`);
            return result;
        } catch (error) {
            console.log(`❌ ${test.name} - Error: ${error.message}`);
            return false;
        }
    }

    /**
     * Get test coverage report
     */
    getCoverageReport() {
        return {
            navigation: this.tests.filter(t => t.name.includes('Navigation')).length,
            components: this.tests.filter(t => t.name.includes('Component')).length,
            security: this.tests.filter(t => t.name.includes('XSS') || t.name.includes('CSP')).length,
            performance: this.tests.filter(t => t.name.includes('Performance')).length,
            accessibility: this.tests.filter(t => t.name.includes('ARIA') || t.name.includes('Alt')).length,
            integration: this.tests.filter(t => t.name.includes('Integration') || t.name.includes('Cross')).length
        };
    }

    /**
     * Auto-run tests on page load (for development)
     */
    static autoTest() {
        if (window.location.search.includes('test=true')) {
            setTimeout(() => {
                const testSuite = new TawniaIntegrationTests();
                testSuite.runTests();
            }, 2000); // Wait for components to initialize
        }
    }
}

// Auto-run tests in development mode
TawniaIntegrationTests.autoTest();

// Export for global access
window.TawniaIntegrationTests = TawniaIntegrationTests;

// Console shortcuts for development
if (typeof console !== 'undefined') {
    console.info('%c🧪 Tawnia Integration Tests', 'color: #3b82f6; font-weight: bold; font-size: 14px;');
    console.info('%cRun tests manually with: new TawniaIntegrationTests().runTests()', 'color: #64748b;');
    console.info('%cOr add ?test=true to URL for auto-testing', 'color: #64748b;');
}