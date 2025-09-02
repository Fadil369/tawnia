/**
 * Tawnia Healthcare Analytics - Shared Navigation System
 * Provides unified navigation and integration across all application pages
 */

class TawniaNavigation {
    constructor() {
        this.pages = {
            'main': {
                title: 'Main Dashboard',
                titleAr: 'لوحة القيادة الرئيسية',
                url: 'brainsait-enhanced.html',
                icon: 'fas fa-tachometer-alt',
                description: 'Main analytics dashboard with comprehensive healthcare data insights'
            },
            'verification': {
                title: 'Insurance Verification',
                titleAr: 'التحقق من التأمين',
                url: 'insurance_verification.html',
                icon: 'fas fa-shield-alt',
                description: 'Nafath-integrated insurance eligibility verification system'
            },
            'index': {
                title: 'Portal Home',
                titleAr: 'الصفحة الرئيسية',
                url: 'index.html',
                icon: 'fas fa-home',
                description: 'Application entry point and navigation portal'
            }
        };
        
        this.currentPage = this.detectCurrentPage();
        this.language = localStorage.getItem('tawnia_language') || 'en';
        this.theme = localStorage.getItem('tawnia_theme') || 'dark';
        
        this.init();
    }

    /**
     * Initialize navigation system
     */
    init() {
        this.injectNavigationStyles();
        this.createNavigationBar();
        this.setupLanguageToggle();
        this.setupThemeToggle();
        this.setupKeyboardShortcuts();
        this.initializeServiceWorker();
        this.setupPageAnalytics();
    }

    /**
     * Detect current page based on URL
     */
    detectCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop() || 'index.html';
        
        for (const [key, page] of Object.entries(this.pages)) {
            if (filename === page.url || filename === '' && page.url === 'index.html') {
                return key;
            }
        }
        return 'main';
    }

    /**
     * Inject navigation styles
     */
    injectNavigationStyles() {
        const styles = `
            /* Tawnia Navigation Styles */
            .tawnia-nav {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: rgba(26, 31, 46, 0.98);
                backdrop-filter: blur(20px);
                border-bottom: 1px solid rgba(59, 130, 246, 0.3);
                z-index: 10000;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }

            .tawnia-nav.hidden {
                transform: translateY(-100%);
            }

            .nav-container {
                max-width: 1400px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.75rem 1.5rem;
            }

            .nav-brand {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-size: 1.25rem;
                font-weight: 700;
                color: #3b82f6;
                text-decoration: none;
                transition: all 0.3s ease;
            }

            .nav-brand:hover {
                color: #60a5fa;
                transform: scale(1.05);
            }

            .nav-brand i {
                font-size: 1.5rem;
                animation: pulse 2s infinite;
            }

            .nav-pages {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .nav-page-btn {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                background: transparent;
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 0.5rem;
                color: #e2e8f0;
                text-decoration: none;
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .nav-page-btn:hover {
                background: rgba(59, 130, 246, 0.1);
                border-color: #3b82f6;
                color: #60a5fa;
                transform: translateY(-1px);
            }

            .nav-page-btn.active {
                background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                border-color: #1d4ed8;
                color: white;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            }

            .nav-page-btn.active::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
                animation: shimmer 2s infinite;
            }

            .nav-controls {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .nav-toggle-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 2.5rem;
                height: 2.5rem;
                background: rgba(148, 163, 184, 0.1);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 0.5rem;
                color: #e2e8f0;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.875rem;
            }

            .nav-toggle-btn:hover {
                background: rgba(59, 130, 246, 0.1);
                border-color: #3b82f6;
                color: #60a5fa;
            }

            .nav-breadcrumb {
                background: rgba(45, 55, 72, 0.8);
                backdrop-filter: blur(10px);
                padding: 0.5rem 1.5rem;
                border-bottom: 1px solid rgba(148, 163, 184, 0.1);
                font-size: 0.875rem;
                color: #94a3b8;
            }

            .breadcrumb-path {
                max-width: 1400px;
                margin: 0 auto;
            }

            .breadcrumb-path a {
                color: #60a5fa;
                text-decoration: none;
                margin-right: 0.5rem;
            }

            .breadcrumb-path a:hover {
                text-decoration: underline;
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .nav-container {
                    padding: 0.5rem 1rem;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }

                .nav-pages {
                    order: 3;
                    flex-basis: 100%;
                    margin-top: 0.5rem;
                    justify-content: center;
                    gap: 0.5rem;
                }

                .nav-page-btn {
                    font-size: 0.8rem;
                    padding: 0.375rem 0.75rem;
                }
            }

            /* Animation keyframes */
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }

            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    /**
     * Create navigation bar
     */
    createNavigationBar() {
        // Create navigation container
        const nav = document.createElement('nav');
        nav.className = 'tawnia-nav';
        nav.id = 'tawnia-navigation';

        // Navigation content
        nav.innerHTML = `
            <div class="nav-container">
                <a href="index.html" class="nav-brand" title="Tawnia Healthcare Analytics">
                    <i class="fas fa-heartbeat"></i>
                    <span>Tawnia Analytics</span>
                    <div style="font-size: 0.6rem; font-weight: 400; color: #94a3b8; margin-left: 0.5rem;">v2.0</div>
                </a>

                <div class="nav-pages">
                    ${Object.entries(this.pages).map(([key, page]) => `
                        <a href="${page.url}" 
                           class="nav-page-btn ${key === this.currentPage ? 'active' : ''}" 
                           data-page="${key}"
                           title="${page.description}">
                            <i class="${page.icon}"></i>
                            <span class="page-title-en">${page.title}</span>
                            <span class="page-title-ar" style="display: none;">${page.titleAr}</span>
                        </a>
                    `).join('')}
                </div>

                <div class="nav-controls">
                    <button class="nav-toggle-btn" id="langToggle" title="Toggle Language / تبديل اللغة">
                        ${this.language === 'ar' ? 'EN' : 'ع'}
                    </button>
                    <button class="nav-toggle-btn" id="themeToggle" title="Toggle Theme">
                        <i class="fas ${this.theme === 'dark' ? 'fa-sun' : 'fa-moon'}"></i>
                    </button>
                    <button class="nav-toggle-btn" id="fullscreenToggle" title="Toggle Fullscreen">
                        <i class="fas fa-expand"></i>
                    </button>
                </div>
            </div>
        `;

        // Add breadcrumb
        const breadcrumb = document.createElement('div');
        breadcrumb.className = 'nav-breadcrumb';
        breadcrumb.innerHTML = `
            <div class="breadcrumb-path">
                <a href="index.html">Home</a> → 
                <span>${this.pages[this.currentPage].title}</span>
            </div>
        `;

        nav.appendChild(breadcrumb);

        // Insert at the beginning of body
        document.body.insertBefore(nav, document.body.firstChild);

        // Adjust body padding to account for fixed nav
        document.body.style.paddingTop = nav.offsetHeight + 'px';

        // Auto-hide on scroll
        this.setupAutoHide();
    }

    /**
     * Setup auto-hide navigation on scroll
     */
    setupAutoHide() {
        let lastScrollY = window.scrollY;
        let ticking = false;

        const updateNavVisibility = () => {
            const nav = document.getElementById('tawnia-navigation');
            const currentScrollY = window.scrollY;

            if (currentScrollY > lastScrollY && currentScrollY > 100) {
                nav.classList.add('hidden');
            } else {
                nav.classList.remove('hidden');
            }

            lastScrollY = currentScrollY;
            ticking = false;
        };

        const requestTick = () => {
            if (!ticking) {
                requestAnimationFrame(updateNavVisibility);
                ticking = true;
            }
        };

        window.addEventListener('scroll', requestTick);
    }

    /**
     * Setup language toggle functionality
     */
    setupLanguageToggle() {
        const langToggle = document.getElementById('langToggle');
        
        langToggle.addEventListener('click', () => {
            this.language = this.language === 'en' ? 'ar' : 'en';
            localStorage.setItem('tawnia_language', this.language);
            this.updateLanguageDisplay();
            this.notifyLanguageChange();
        });

        this.updateLanguageDisplay();
    }

    /**
     * Update language display
     */
    updateLanguageDisplay() {
        const langToggle = document.getElementById('langToggle');
        langToggle.textContent = this.language === 'ar' ? 'EN' : 'ع';

        // Update page titles
        document.querySelectorAll('.nav-page-btn').forEach(btn => {
            const enTitle = btn.querySelector('.page-title-en');
            const arTitle = btn.querySelector('.page-title-ar');
            
            if (this.language === 'ar') {
                enTitle.style.display = 'none';
                arTitle.style.display = 'inline';
                document.body.setAttribute('dir', 'rtl');
            } else {
                enTitle.style.display = 'inline';
                arTitle.style.display = 'none';
                document.body.setAttribute('dir', 'ltr');
            }
        });
    }

    /**
     * Setup theme toggle functionality
     */
    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        
        themeToggle.addEventListener('click', () => {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('tawnia_theme', this.theme);
            this.applyTheme();
            this.notifyThemeChange();
        });

        this.applyTheme();
    }

    /**
     * Apply theme
     */
    applyTheme() {
        const themeToggle = document.getElementById('themeToggle');
        const icon = themeToggle.querySelector('i');
        
        document.body.setAttribute('data-theme', this.theme);
        icon.className = `fas ${this.theme === 'dark' ? 'fa-sun' : 'fa-moon'}`;
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + number keys for page navigation
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                const pageKeys = {
                    '1': 'index',
                    '2': 'main', 
                    '3': 'verification'
                };
                
                if (pageKeys[e.key]) {
                    e.preventDefault();
                    window.location.href = this.pages[pageKeys[e.key]].url;
                }
            }

            // Ctrl + L for language toggle
            if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                document.getElementById('langToggle').click();
            }

            // Ctrl + T for theme toggle
            if (e.ctrlKey && e.key === 't') {
                e.preventDefault();
                document.getElementById('themeToggle').click();
            }

            // F11 for fullscreen
            if (e.key === 'F11') {
                e.preventDefault();
                document.getElementById('fullscreenToggle').click();
            }
        });

        // Setup fullscreen toggle
        document.getElementById('fullscreenToggle').addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        });
    }

    /**
     * Initialize service worker
     */
    initializeServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
    }

    /**
     * Setup page analytics
     */
    setupPageAnalytics() {
        // Track page view
        this.trackPageView();

        // Track navigation events
        document.querySelectorAll('.nav-page-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.trackNavigation(page);
            });
        });
    }

    /**
     * Track page view
     */
    trackPageView() {
        const analytics = {
            page: this.currentPage,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            language: this.language,
            theme: this.theme,
            screenSize: `${screen.width}x${screen.height}`,
            viewport: `${window.innerWidth}x${window.innerHeight}`
        };

        // Store in localStorage for demo purposes
        const pageViews = JSON.parse(localStorage.getItem('tawnia_analytics') || '[]');
        pageViews.push(analytics);
        
        // Keep only last 100 entries
        if (pageViews.length > 100) {
            pageViews.splice(0, pageViews.length - 100);
        }
        
        localStorage.setItem('tawnia_analytics', JSON.stringify(pageViews));
    }

    /**
     * Track navigation
     */
    trackNavigation(targetPage) {
        console.log(`Navigation: ${this.currentPage} → ${targetPage}`);
    }

    /**
     * Notify language change to other components
     */
    notifyLanguageChange() {
        window.dispatchEvent(new CustomEvent('tawnia:languageChanged', {
            detail: { language: this.language }
        }));
    }

    /**
     * Notify theme change to other components
     */
    notifyThemeChange() {
        window.dispatchEvent(new CustomEvent('tawnia:themeChanged', {
            detail: { theme: this.theme }
        }));
    }

    /**
     * Toggle language between English and Arabic
     */
    toggleLanguage() {
        const newLanguage = this.language === 'en' ? 'ar' : 'en';
        this.language = newLanguage;
        localStorage.setItem('tawnia_language', newLanguage);
        this.updateLanguageDisplay();
    }

    /**
     * Toggle theme between light and dark
     */
    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.theme = newTheme;
        localStorage.setItem('tawnia_theme', newTheme);
        this.applyTheme();
    }

    /**
     * Get current language
     */
    getLanguage() {
        return this.language;
    }

    /**
     * Get current theme
     */
    getTheme() {
        return this.theme;
    }

    /**
     * Navigate to specific page
     */
    navigateTo(pageKey) {
        if (this.pages[pageKey]) {
            window.location.href = this.pages[pageKey].url;
        }
    }
}

// Initialize navigation when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.TawniaNav = new TawniaNavigation();
    });
} else {
    window.TawniaNav = new TawniaNavigation();
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TawniaNavigation;
}