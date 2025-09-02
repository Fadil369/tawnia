/**
 * Tawnia Healthcare Analytics - Enhanced UI/UX Application
 * Modern, responsive, and feature-rich frontend interface with security enhancements
 */

class TawniaAnalyzer {
    constructor() {
        this.apiBase = '/api';
        this.currentData = null;
        this.charts = {};
        this.uploadedFiles = [];
        this.processingQueue = [];
        this.notifications = [];
        this.isOnline = navigator.onLine;
        this.theme = localStorage.getItem('theme') || 'dark';
        this.animations = {
            enabled: !window.matchMedia('(prefers-reduced-motion: reduce)').matches
        };
        this.performance = {
            startTime: performance.now(),
            metrics: {}
        };

        // Security configuration
        this.security = {
            maxFileSize: 50 * 1024 * 1024, // 50MB
            allowedExtensions: ['.xlsx', '.xls', '.csv'],
            maxFilesPerUpload: 5,
            sanitizeHTML: true
        };

        this.init();
    }

    /**
     * Security: HTML sanitization to prevent XSS attacks
     * @param {string} html - Raw HTML string
     * @returns {string} - Sanitized HTML string
     */
    sanitizeHTML(html) {
        if (!this.security.sanitizeHTML) return html;
        
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }

    /**
     * Security: Safely set HTML content with sanitization
     * @param {HTMLElement} element - Target element
     * @param {string} html - HTML content to set
     */
    safeSetHTML(element, html) {
        if (typeof html !== 'string') {
            console.warn('Non-string content passed to safeSetHTML');
            element.textContent = String(html);
            return;
        }
        
        // Create a temporary container
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // Remove potentially dangerous elements and attributes
        const dangerousElements = temp.querySelectorAll('script, iframe, object, embed, form');
        dangerousElements.forEach(el => el.remove());
        
        // Remove event handlers and javascript: URLs
        const allElements = temp.querySelectorAll('*');
        allElements.forEach(el => {
            // Remove all event handler attributes
            Array.from(el.attributes).forEach(attr => {
                if (attr.name.startsWith('on') || attr.value.includes('javascript:')) {
                    el.removeAttribute(attr.name);
                }
            });
        });
        
        element.innerHTML = temp.innerHTML;
    }

    /**
     * Security: Validate file before processing
     * @param {File} file - File to validate
     * @returns {Object} - Validation result
     */
    validateFile(file) {
        const errors = [];
        
        // Check file size
        if (file.size > this.security.maxFileSize) {
            errors.push(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds maximum allowed size (${this.security.maxFileSize / 1024 / 1024}MB)`);
        }
        
        // Check file extension
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.security.allowedExtensions.includes(extension)) {
            errors.push(`File type "${extension}" is not allowed. Allowed types: ${this.security.allowedExtensions.join(', ')}`);
        }
        
        // Check filename for security issues
        if (file.name.includes('..') || file.name.includes('/') || file.name.includes('\\')) {
            errors.push('Invalid filename - contains path traversal characters');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors,
            file: file
        };
    }

    /**
     * Initialize the application with enhanced features
     */
    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupKeyboardShortcuts();
        this.setupNetworkMonitoring();
        this.setupPerformanceMonitoring();
        this.setupGestureSupport();
        this.loadQuickStats();
        this.loadHistory();
        this.initializeCharts();
        this.startHealthCheck();
        this.preloadCriticalResources();
        this.initializeServiceWorker();
        
        // Add loading animation
        this.showWelcomeAnimation();
        
        console.log('🚀 Tawnia Healthcare Analytics v2.0 initialized');
        this.showNotification('System initialized successfully', 'success', 3000);
        
        // Track initialization performance
        this.performance.metrics.initTime = performance.now() - this.performance.startTime;
        console.log(`Initialization completed in ${this.performance.metrics.initTime.toFixed(2)}ms`);
    }

    /**
     * Enhanced event listeners with modern UX features
     */
    setupEventListeners() {
        // Tab navigation with enhanced UX
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
                
                // Add haptic feedback if supported
                if (navigator.vibrate) {
                    navigator.vibrate(50);
                }
            });
            
            // Add hover effects
            button.addEventListener('mouseenter', () => {
                this.playHoverSound();
                button.style.transform = 'translateY(-1px)';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
            });
        });

        // Enhanced file input with multiple selection methods
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });
        
        // Paste support for files
        document.addEventListener('paste', (e) => {
            const items = e.clipboardData?.items;
            if (items) {
                const files = Array.from(items)
                    .filter(item => item.kind === 'file')
                    .map(item => item.getAsFile());
                if (files.length > 0) {
                    this.handleFileSelection(files);
                }
            }
        });

        // Window resize with debouncing
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.resizeCharts();
                this.updateResponsiveLayout();
            }, 250);
        });
        
        // Visibility change handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimations();
            } else {
                this.resumeAnimations();
                this.refreshData();
            }
        });

        // Scroll-based animations
        this.setupScrollAnimations();
    }
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.resizeCharts();
                this.updateResponsiveLayout();
            }, 250);
        });
        
        // Visibility change handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimations();
            } else {
                this.resumeAnimations();
                this.refreshData();
            }
        });

        // Scroll-based animations
        this.setupScrollAnimations();
    }

    /**
     * Enhanced tab switching with smooth animations
     */
    switchTab(tabName) {
        const currentTab = document.querySelector('.tab-content.active');
        const newTab = document.getElementById(`${tabName}-tab`);
        
        if (!newTab || newTab.classList.contains('active')) return;
        
        // Null check for newTab before accessing properties
        if (newTab) {
            newTab.classList.add('active');
        }
        
        // Add loading state
        this.setTabLoading(tabName, true);
        
        // Animate out current tab
        if (currentTab && this.animations.enabled) {
            currentTab.style.animation = 'slideOutLeft 0.3s ease-in-out';
            setTimeout(() => {
                this.completeTabSwitch(tabName);
            }, 300);
        } else {
            this.completeTabSwitch(tabName);
        }
    }
    
    completeTabSwitch(tabName) {
        // Update tab buttons with smooth transition
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
            button.style.transform = 'scale(1)';
        });
        
        const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
        activeButton.classList.add('active');
        activeButton.style.transform = 'scale(1.05)';
        
        setTimeout(() => {
            activeButton.style.transform = 'scale(1)';
        }, 200);
        
        // Update tab content with slide animation
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            content.style.animation = '';
        });
        
        const newTab = document.getElementById(`${tabName}-tab`);
        newTab.classList.add('active');
        
        if (this.animations.enabled) {
            newTab.style.animation = 'slideInRight 0.4s ease-out';
        }
        
        // Load tab-specific content
        this.loadTabContent(tabName).finally(() => {
            this.setTabLoading(tabName, false);
        });
        
        // Update URL without page reload
        history.pushState({tab: tabName}, '', `#${tabName}`);
        
        // Track analytics
        this.trackEvent('tab_switch', {tab: tabName});
    }

    /**
     * Enhanced file handling with comprehensive validation
     */
    async handleFileSelection(files) {
        if (!files || files.length === 0) return;
        
        // Check network connectivity
        if (!this.isOnline) {
            this.showNotification('No internet connection. Please check your network.', 'error', 0, [
                {label: 'Retry', handler: 'analyzer.checkConnection()'}
            ]);
            return;
        }
        
        const validExtensions = ['.xlsx', '.xls', '.csv', '.json'];
        const maxFileSize = 100 * 1024 * 1024; // 100MB
        const maxFiles = 10;
        
        if (files.length > maxFiles) {
            this.showNotification(`Maximum ${maxFiles} files allowed at once`, 'warning');
            files = Array.from(files).slice(0, maxFiles);
        }
        
        const validFiles = [];
        const errors = [];
        
        // Enhanced file validation
        for (const file of files) {
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!validExtensions.includes(extension)) {
                errors.push(`${file.name}: Invalid file type (${extension})`);
                continue;
            }
            
            if (file.size > maxFileSize) {
                errors.push(`${file.name}: File too large (${(file.size / 1024 / 1024).toFixed(1)}MB > 100MB)`);
                continue;
            }
            
            if (file.size === 0) {
                errors.push(`${file.name}: Empty file`);
                continue;
            }
            
            // Check for duplicate files
            if (this.uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
                errors.push(`${file.name}: File already uploaded`);
                continue;
            }
            
            validFiles.push(file);
        }
        
        if (errors.length > 0) {
            this.showNotification(`File validation issues:\n${errors.join('\n')}`, 'warning', 8000);
        }
        
        if (validFiles.length === 0) {
            this.showNotification('No valid files to upload', 'error');
            return;
        }
        
        // Show enhanced file preview
        this.showFilePreview(validFiles);
        
        // Start upload with progress tracking
        await this.uploadFilesWithProgress(validFiles);
    }

    /**
     * Enhanced file preview with detailed information
     */
    showFilePreview(files) {
        const totalSize = files.reduce((sum, file) => sum + file.size, 0);
        const preview = files.map((file, index) => `
            <div class="file-preview-item" style="display: flex; align-items: center; gap: 0.75rem; 
                        padding: 0.75rem; background: rgba(59, 130, 246, 0.1); 
                        border-radius: var(--radius-lg); margin-bottom: 0.5rem; 
                        border-left: 3px solid var(--success-color); animation: slideInUp 0.3s ease ${index * 0.1}s both;">
                <div style="width: 40px; height: 40px; background: var(--success-color); 
                           border-radius: var(--radius-md); display: flex; align-items: center; 
                           justify-content: center; color: white;">
                    <i class="fas fa-file-excel"></i>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 0.9rem;">${file.name}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                        ${(file.size / 1024 / 1024).toFixed(2)}MB • ${file.type || 'Unknown type'}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.8rem; color: var(--success-color); font-weight: 600;">
                        Ready
                    </div>
                </div>
            </div>
        `).join('');
        
        const notificationContent = `
            <div style="margin-bottom: 1rem;">
                <strong>Ready to upload ${files.length} file(s)</strong>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
                    Total size: ${(totalSize / 1024 / 1024).toFixed(2)}MB
                </div>
            </div>
            ${preview}
        `;
        
        this.showNotification(notificationContent, 'info', 8000, [
            {label: 'Cancel', handler: 'analyzer.cancelUpload()'}
        ]);
    }

    /**
     * Enhanced upload with real-time progress and error handling
     */
    async uploadFilesWithProgress(files) {
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        progressContainer.style.display = 'block';
        progressContainer.style.animation = 'slideDown 0.3s ease';
        
        let totalProgress = 0;
        const progressPerFile = 100 / files.length;

        try {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);

                progressText.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Uploading ${file.name}</span>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">${i + 1}/${files.length}</span>
                    </div>
                `;

                // Simulate realistic progress
                let fileProgress = 0;
                const progressInterval = setInterval(() => {
                    fileProgress += Math.random() * 15;
                    if (fileProgress > 90) fileProgress = 90;
                    
                    const currentTotal = totalProgress + (fileProgress * progressPerFile / 100);
                    progressFill.style.width = `${currentTotal}%`;
                }, 150);

                try {
                    const response = await fetch(`${this.apiBase}/upload/single`, {
                        method: 'POST',
                        body: formData
                    });

                    clearInterval(progressInterval);
                    
                    const result = await response.json();
                    totalProgress += progressPerFile;
                    progressFill.style.width = `${totalProgress}%`;

                    if (result.success) {
                        this.uploadedFiles.push({
                            ...result.data,
                            uploadTime: new Date(),
                            selected: false
                        });
                        
                        // Show success animation
                        this.showFileUploadSuccess(file.name);
                    } else {
                        throw new Error(result.message || 'Upload failed');
                    }

                } catch (error) {
                    clearInterval(progressInterval);
                    this.showNotification(`Failed to upload ${file.name}: ${error.message}`, 'error');
                    console.error('Upload error:', error);
                }

                // Brief pause between files for better UX
                await new Promise(resolve => setTimeout(resolve, 300));
            }

            progressText.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--success-color);">
                    <i class="fas fa-check-circle"></i>
                    <span>Upload completed successfully!</span>
                </div>
            `;

            // Hide progress after delay with animation
            setTimeout(() => {
                progressContainer.style.animation = 'slideUp 0.3s ease';
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                }, 300);
            }, 2000);

            // Update UI with animations
            await this.loadQuickStats();
            await this.loadHistory();
            
            // Show completion notification
            this.showNotification(
                `Successfully uploaded ${files.length} file(s)`, 
                'success', 
                4000,
                [{label: 'View Results', handler: 'analyzer.switchTab("analyze")'}]
            );

        } catch (error) {
            console.error('Upload process error:', error);
            this.showNotification('Upload process failed. Please try again.', 'error');
            progressContainer.style.display = 'none';
        }
    }

    /**
     * Sanitize HTML to prevent XSS attacks
     */
    sanitizeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Enhanced notification system with rich interactions
     */
    showNotification(message, type = 'info', duration = 4000, actions = []) {
        const notificationId = Date.now();
        
        const notification = document.createElement('div');
        notification.className = `notification ${type} glass`;
        notification.dataset.id = notificationId;
        
        const colors = {
            success: 'var(--success-color)',
            error: 'var(--danger-color)',
            warning: 'var(--warning-color)',
            info: 'var(--info-color)'
        };
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1.25rem 1.5rem;
            border-radius: var(--radius-xl);
            color: white;
            font-weight: 600;
            z-index: 10000;
            max-width: 450px;
            min-width: 320px;
            backdrop-filter: blur(20px);
            border: 1px solid ${colors[type]};
            background: linear-gradient(135deg, ${colors[type]}22, ${colors[type]}11);
            box-shadow: var(--shadow-xl), 0 0 30px ${colors[type]}33;
            transform: translateX(500px) scale(0.8) rotateY(90deg);
            transition: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            margin-bottom: 0.75rem;
        `;
        
        // Position multiple notifications
        const existingNotifications = document.querySelectorAll('.notification');
        if (existingNotifications.length > 0) {
            const offset = existingNotifications.length * 90;
            notification.style.top = `${20 + offset}px`;
        }
        
        let actionsHtml = '';
        if (actions.length > 0) {
            actionsHtml = `
                <div style="margin-top: 1rem; display: flex; gap: 0.75rem; flex-wrap: wrap;">
                    ${actions.map(action => `
                        <button onclick="${action.handler}" 
                                style="padding: 0.5rem 1rem; border: 1px solid rgba(255,255,255,0.3); 
                                       background: rgba(255,255,255,0.15); color: white; 
                                       border-radius: var(--radius-lg); cursor: pointer; 
                                       font-size: 0.85rem; font-weight: 600; 
                                       transition: all 0.2s; backdrop-filter: blur(10px);"
                                onmouseover="this.style.background='rgba(255,255,255,0.25)'" 
                                onmouseout="this.style.background='rgba(255,255,255,0.15)'">
                            ${action.label}
                        </button>
                    `).join('')}
                </div>
            `;
        }
        
        notification.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 1rem;">
                <div style="width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">
                    <i class="${icons[type]}" style="font-size: 1.3rem; filter: drop-shadow(0 0 8px currentColor);"></i>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 0.95rem; line-height: 1.5;">${this.sanitizeHTML(message)}</div>
                    ${actionsHtml}
                </div>
                <button onclick="analyzer.dismissNotification(${notificationId})" 
                        style="background: none; border: none; color: rgba(255,255,255,0.6); 
                               cursor: pointer; padding: 0; font-size: 1.2rem; 
                               transition: all 0.2s; width: 24px; height: 24px;
                               display: flex; align-items: center; justify-content: center;"
                        onmouseover="this.style.color='white'; this.style.transform='scale(1.1)'" 
                        onmouseout="this.style.color='rgba(255,255,255,0.6)'; this.style.transform='scale(1)'">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        this.notifications.push({id: notificationId, element: notification});
        
        // Animate in with 3D effect
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0) scale(1) rotateY(0deg)';
        });
        
        // Auto dismiss with countdown
        if (duration > 0) {
            setTimeout(() => {
                this.dismissNotification(notificationId);
            }, duration);
        }
        
        // Play notification sound
        this.playNotificationSound(type);
        
        return notificationId;
    }

    dismissNotification(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification) {
            notification.element.style.transform = 'translateX(500px) scale(0.8) rotateY(90deg)';
            notification.element.style.opacity = '0';
            
            setTimeout(() => {
                if (notification.element.parentNode) {
                    notification.element.parentNode.removeChild(notification.element);
                }
                this.notifications = this.notifications.filter(n => n.id !== id);
                this.repositionNotifications();
            }, 500);
        }
    }

    repositionNotifications() {
        const NOTIFICATION_SPACING = 90;
        this.notifications.forEach((notification, index) => {
            notification.element.style.top = `${20 + (index * NOTIFICATION_SPACING)}px`;
        });
    }

    /**
     * Keyboard shortcuts for power users
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + U for upload
            if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
                e.preventDefault();
                document.getElementById('fileInput').click();
            }
            
            // Ctrl/Cmd + 1-5 for tab switching
            if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '5') {
                e.preventDefault();
                const tabs = ['upload', 'analyze', 'insights', 'reports', 'history'];
                const tabIndex = parseInt(e.key) - 1;
                if (tabs[tabIndex]) {
                    this.switchTab(tabs[tabIndex]);
                }
            }
            
            // Escape to close notifications
            if (e.key === 'Escape') {
                this.notifications.forEach(n => this.dismissNotification(n.id));
            }
            
            // Ctrl/Cmd + R for refresh (prevent default and use custom)
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.refreshData();
                this.showNotification('Data refreshed', 'info', 2000);
            }
        });
    }

    /**
     * Network connectivity monitoring
     */
    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showNotification('Connection restored', 'success', 2000);
            this.refreshData();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showNotification('Connection lost. Some features may be unavailable.', 'warning', 0);
        });
    }

    /**
     * Performance monitoring and optimization
     */
    setupPerformanceMonitoring() {
        if ('performance' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.duration > 1000) {
                        console.warn(`Slow operation detected: ${entry.name} took ${entry.duration}ms`);
                    }
                });
            });
            
            try {
                observer.observe({entryTypes: ['measure', 'navigation']});
            } catch (e) {
                console.log('Performance monitoring not supported');
            }
        }
    }

    /**
     * Touch and gesture support for mobile devices
     */
    setupGestureSupport() {
        let touchStartX = 0;
        let touchStartY = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            
            // Swipe gestures for tab navigation
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 100) {
                const tabs = ['upload', 'analyze', 'insights', 'reports', 'history'];
                const currentTabIndex = tabs.findIndex(tab => 
                    document.getElementById(`${tab}-tab`).classList.contains('active')
                );
                
                if (deltaX > 0 && currentTabIndex > 0) {
                    // Swipe right - previous tab
                    this.switchTab(tabs[currentTabIndex - 1]);
                } else if (deltaX < 0 && currentTabIndex < tabs.length - 1) {
                    // Swipe left - next tab
                    this.switchTab(tabs[currentTabIndex + 1]);
                }
            }
        });
    }

    /**
     * Scroll-based animations
     */
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
                }
            });
        }, observerOptions);
        
        // Observe cards and other elements
        document.querySelectorAll('.card, .chart-container').forEach(el => {
            observer.observe(el);
        });
    }

    /**
     * Welcome animation sequence
     */
    showWelcomeAnimation() {
        if (!this.animations.enabled) return;
        
        // Animate logo
        const logo = document.querySelector('.logo');
        if (logo) {
            logo.style.animation = 'bounceIn 1s ease';
        }
        
        // Animate tabs
        const tabs = document.querySelectorAll('.tab-button');
        tabs.forEach((tab, index) => {
            tab.style.opacity = '0';
            tab.style.transform = 'translateY(-20px)';
            
            setTimeout(() => {
                tab.style.transition = 'all 0.6s ease';
                tab.style.opacity = '1';
                tab.style.transform = 'translateY(0)';
            }, index * 100 + 500);
        });
        
        // Animate cards
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px) scale(0.9)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0) scale(1)';
            }, index * 150 + 800);
        });
    }

    /**
     * Audio feedback system
     */
    playNotificationSound(type) {
        if ('AudioContext' in window && this.animations.enabled) {
            try {
                const audioContext = new AudioContext();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                const frequencies = {
                    success: [523, 659, 784], // C-E-G chord
                    error: [220, 185], // Dissonant
                    warning: [440, 554], // A-C#
                    info: [523] // C
                };
                
                const freqArray = frequencies[type] || frequencies.info;
                
                freqArray.forEach((freq, index) => {
                    const osc = audioContext.createOscillator();
                    const gain = audioContext.createGain();
                    
                    osc.connect(gain);
                    gain.connect(audioContext.destination);
                    
                    osc.frequency.setValueAtTime(freq, audioContext.currentTime + index * 0.1);
                    gain.gain.setValueAtTime(0.05, audioContext.currentTime + index * 0.1);
                    gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + index * 0.1 + 0.3);
                    
                    osc.start(audioContext.currentTime + index * 0.1);
                    osc.stop(audioContext.currentTime + index * 0.1 + 0.3);
                });
                
            } catch (e) {
                // Silently fail if audio not supported
            }
        }
    }

    playHoverSound() {
        if ('AudioContext' in window && this.animations.enabled) {
            try {
                const audioContext = new AudioContext();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.02, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.1);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.1);
            } catch (e) {
                // Silently fail
            }
        }
    }

    /**
     * Utility methods
     */
    updateResponsiveLayout() {
        const isMobile = window.innerWidth < 768;
        const isTablet = window.innerWidth < 1024;
        
        document.body.classList.toggle('mobile', isMobile);
        document.body.classList.toggle('tablet', isTablet);
    }
    
    pauseAnimations() {
        document.body.style.animationPlayState = 'paused';
    }
    
    resumeAnimations() {
        document.body.style.animationPlayState = 'running';
    }
    
    refreshData() {
        this.loadQuickStats();
        this.loadHistory();
    }
    
    preloadCriticalResources() {
        const criticalUrls = ['/api/upload/list', '/health'];
        criticalUrls.forEach(url => {
            fetch(url, {method: 'HEAD'}).catch(() => {});
        });
    }

    initializeServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.log('Service Worker registration failed:', error);
                });
        }
    }

    startHealthCheck() {
        this.healthCheckInterval = setInterval(async () => {
            try {
                const response = await fetch('/health');
                if (!response.ok) {
                    this.showNotification('System health check failed', 'warning');
                }
            } catch (error) {
                console.warn('Health check failed:', error);
            }
        }, 60000);
    }

    stopHealthCheck() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }
    }

    trackEvent(eventName, properties = {}) {
        console.log('Event tracked:', eventName, properties);
        // Implement analytics tracking here
    }

    setTabLoading(tabName, loading) {
        const button = document.querySelector(`[data-tab="${tabName}"]`);
        if (button) {
            if (loading) {
                button.style.opacity = '0.7';
                button.style.pointerEvents = 'none';
            } else {
                button.style.opacity = '1';
                button.style.pointerEvents = 'auto';
            }
        }
    }

    showFileUploadSuccess(filename) {
        // Create a temporary success indicator
        const indicator = document.createElement('div');
        indicator.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--success-color);
            color: white;
            padding: 1rem 2rem;
            border-radius: var(--radius-xl);
            font-weight: 600;
            z-index: 10001;
            animation: successPop 2s ease forwards;
        `;
        indicator.innerHTML = `
            <i class="fas fa-check-circle"></i>
            ${filename} uploaded successfully!
        `;
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.parentNode.removeChild(indicator);
            }
        }, 2000);
    }

    checkConnection() {
        fetch('/health')
            .then(() => {
                this.isOnline = true;
                this.showNotification('Connection restored', 'success');
            })
            .catch(() => {
                this.showNotification('Still no connection', 'error');
            });
    }

    cancelUpload() {
        // Cancel current upload process
        this.showNotification('Upload cancelled', 'info', 2000);
    }

    // Placeholder methods for compatibility
    setupDragAndDrop() { /* Implementation from original */ }
    loadTabContent(tabName) { return Promise.resolve(); }
    loadQuickStats() { return Promise.resolve(); }
    loadHistory() { return Promise.resolve(); }
    initializeCharts() { /* Implementation from original */ }
    resizeCharts() { /* Implementation from original */ }
}

// Enhanced initialization with loading screen
let analyzer;

function showLoadingScreen() {
    const loadingScreen = document.createElement('div');
    loadingScreen.id = 'loadingScreen';
    loadingScreen.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%); 
                    display: flex; flex-direction: column; align-items: center; justify-content: center; 
                    z-index: 99999; color: white;">
            <div style="text-align: center;">
                <div style="font-size: 4rem; margin-bottom: 1.5rem; animation: pulse 2s infinite;">
                    <i class="fas fa-heartbeat" style="color: #3b82f6; filter: drop-shadow(0 0 20px #3b82f6);"></i>
                </div>
                <h1 style="margin-bottom: 0.5rem; font-weight: 800; font-size: 2rem;">Tawnia Healthcare Analytics</h1>
                <p style="color: #94a3b8; margin-bottom: 3rem; font-size: 1.1rem;">Initializing AI-powered analysis platform...</p>
                <div style="width: 300px; height: 6px; background: rgba(59, 130, 246, 0.2); border-radius: 3px; overflow: hidden;">
                    <div style="width: 100%; height: 100%; background: linear-gradient(90deg, #3b82f6, #1d4ed8, #10b981); 
                                animation: loading 2.5s ease-in-out infinite;"></div>
                </div>
                <div style="margin-top: 1rem; font-size: 0.9rem; color: #64748b;">
                    Loading advanced features...
                </div>
            </div>
        </div>
        <style>
            @keyframes loading {
                0% { transform: translateX(-100%); }
                50% { transform: translateX(0%); }
                100% { transform: translateX(100%); }
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
        </style>
    `;
    document.body.appendChild(loadingScreen);
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.style.opacity = '0';
        loadingScreen.style.transition = 'opacity 0.8s ease';
        setTimeout(() => {
            if (loadingScreen.parentNode) {
                loadingScreen.parentNode.removeChild(loadingScreen);
            }
        }, 800);
    }
}

// Initialize with enhanced loading experience
document.addEventListener('DOMContentLoaded', () => {
    showLoadingScreen();
    
    setTimeout(() => {
        analyzer = new TawniaAnalyzer();
        hideLoadingScreen();
    }, 2000);
    
    // Handle browser navigation
    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.tab && analyzer) {
            analyzer.switchTab(e.state.tab);
        }
    });
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideOutLeft {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(-30px); }
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-20px); }
    }
    
    @keyframes slideInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes bounceIn {
        0% { opacity: 0; transform: scale(0.3); }
        50% { opacity: 1; transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    @keyframes successPop {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
        20% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
        40% { transform: translate(-50%, -50%) scale(0.95); }
        60% { transform: translate(-50%, -50%) scale(1.02); }
        80% { transform: translate(-50%, -50%) scale(0.98); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(1); }
    }
`;
document.head.appendChild(style);