/**
 * Tawnia Healthcare Analytics - Shared Components
 * Reusable UI components and utilities across all pages
 */

class TawniaComponents {
    constructor() {
        this.components = new Map();
        this.themes = {
            dark: {
                primary: '#3b82f6',
                secondary: '#64748b',
                success: '#10b981',
                warning: '#f59e0b',
                danger: '#ef4444',
                bg: '#0a0e1a',
                card: '#1a1f2e',
                text: '#f8fafc',
                muted: '#94a3b8'
            },
            light: {
                primary: '#2563eb',
                secondary: '#475569',
                success: '#059669',
                warning: '#d97706',
                danger: '#dc2626',
                bg: '#ffffff',
                card: '#f8fafc',
                text: '#0f172a',
                muted: '#64748b'
            }
        };
        
        this.init();
    }

    /**
     * Initialize shared components
     */
    init() {
        this.registerComponents();
        this.setupGlobalEventListeners();
        this.initializeTheme();
    }

    /**
     * Register reusable components
     */
    registerComponents() {
        // Loading Spinner Component
        this.components.set('spinner', {
            template: `
                <div class="tawnia-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-text">{{text}}</div>
                </div>
            `,
            styles: `
                .tawnia-spinner {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1rem;
                    padding: 2rem;
                }
                .spinner-ring {
                    width: 2.5rem;
                    height: 2.5rem;
                    border: 3px solid rgba(59, 130, 246, 0.2);
                    border-top: 3px solid #3b82f6;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                .spinner-text {
                    color: var(--text-muted);
                    font-size: 0.875rem;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `
        });

        // Alert Component
        this.components.set('alert', {
            template: `
                <div class="tawnia-alert tawnia-alert-{{type}}" role="alert">
                    <div class="alert-icon">
                        <i class="fas fa-{{icon}}"></i>
                    </div>
                    <div class="alert-content">
                        <div class="alert-title">{{title}}</div>
                        <div class="alert-message">{{message}}</div>
                    </div>
                    <button class="alert-close" onclick="this.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `,
            styles: `
                .tawnia-alert {
                    display: flex;
                    align-items: flex-start;
                    gap: 1rem;
                    padding: 1rem 1.5rem;
                    border-radius: 0.75rem;
                    border: 1px solid;
                    margin-bottom: 1rem;
                    animation: slideInDown 0.3s ease;
                }
                .tawnia-alert-success {
                    background: rgba(16, 185, 129, 0.1);
                    border-color: rgba(16, 185, 129, 0.3);
                    color: #10b981;
                }
                .tawnia-alert-warning {
                    background: rgba(245, 158, 11, 0.1);
                    border-color: rgba(245, 158, 11, 0.3);
                    color: #f59e0b;
                }
                .tawnia-alert-danger {
                    background: rgba(239, 68, 68, 0.1);
                    border-color: rgba(239, 68, 68, 0.3);
                    color: #ef4444;
                }
                .tawnia-alert-info {
                    background: rgba(59, 130, 246, 0.1);
                    border-color: rgba(59, 130, 246, 0.3);
                    color: #3b82f6;
                }
                .alert-icon {
                    font-size: 1.25rem;
                    margin-top: 0.125rem;
                }
                .alert-content {
                    flex: 1;
                }
                .alert-title {
                    font-weight: 600;
                    margin-bottom: 0.25rem;
                }
                .alert-message {
                    font-size: 0.875rem;
                    opacity: 0.9;
                }
                .alert-close {
                    background: none;
                    border: none;
                    color: currentColor;
                    cursor: pointer;
                    padding: 0.25rem;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                }
                .alert-close:hover {
                    opacity: 1;
                }
                @keyframes slideInDown {
                    from {
                        transform: translateY(-20px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            `
        });

        // Modal Component
        this.components.set('modal', {
            template: `
                <div class="tawnia-modal-overlay" onclick="TawniaComponents.closeModal('{{id}}')">
                    <div class="tawnia-modal" onclick="event.stopPropagation()">
                        <div class="modal-header">
                            <h3 class="modal-title">{{title}}</h3>
                            <button class="modal-close" onclick="TawniaComponents.closeModal('{{id}}')">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div class="modal-body">
                            {{content}}
                        </div>
                        <div class="modal-footer">
                            {{footer}}
                        </div>
                    </div>
                </div>
            `,
            styles: `
                .tawnia-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10000;
                    animation: fadeIn 0.3s ease;
                }
                .tawnia-modal {
                    background: var(--bg-card);
                    border-radius: 1rem;
                    max-width: 90vw;
                    max-height: 90vh;
                    overflow: hidden;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                    animation: scaleIn 0.3s ease;
                    border: 1px solid rgba(59, 130, 246, 0.3);
                }
                .modal-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 1.5rem;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
                }
                .modal-title {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                .modal-close {
                    background: none;
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                    padding: 0.5rem;
                    border-radius: 0.375rem;
                    transition: all 0.2s;
                }
                .modal-close:hover {
                    background: rgba(239, 68, 68, 0.1);
                    color: #ef4444;
                }
                .modal-body {
                    padding: 1.5rem;
                    overflow-y: auto;
                }
                .modal-footer {
                    padding: 1.5rem;
                    border-top: 1px solid rgba(148, 163, 184, 0.2);
                    display: flex;
                    gap: 1rem;
                    justify-content: flex-end;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes scaleIn {
                    from { transform: scale(0.9); opacity: 0; }
                    to { transform: scale(1); opacity: 1; }
                }
            `
        });

        // Notification Toast Component
        this.components.set('toast', {
            template: `
                <div class="tawnia-toast tawnia-toast-{{type}}" id="{{id}}">
                    <div class="toast-icon">
                        <i class="fas fa-{{icon}}"></i>
                    </div>
                    <div class="toast-content">
                        <div class="toast-title">{{title}}</div>
                        <div class="toast-message">{{message}}</div>
                    </div>
                    <div class="toast-progress"></div>
                </div>
            `,
            styles: `
                .tawnia-toast {
                    display: flex;
                    align-items: flex-start;
                    gap: 1rem;
                    padding: 1rem;
                    border-radius: 0.75rem;
                    margin-bottom: 0.5rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    position: relative;
                    overflow: hidden;
                    backdrop-filter: blur(10px);
                    animation: slideInRight 0.3s ease;
                    min-width: 300px;
                    max-width: 400px;
                }
                .tawnia-toast-success {
                    background: rgba(16, 185, 129, 0.9);
                    color: white;
                }
                .tawnia-toast-warning {
                    background: rgba(245, 158, 11, 0.9);
                    color: white;
                }
                .tawnia-toast-danger {
                    background: rgba(239, 68, 68, 0.9);
                    color: white;
                }
                .tawnia-toast-info {
                    background: rgba(59, 130, 246, 0.9);
                    color: white;
                }
                .toast-icon {
                    font-size: 1.25rem;
                    margin-top: 0.125rem;
                }
                .toast-content {
                    flex: 1;
                }
                .toast-title {
                    font-weight: 600;
                    margin-bottom: 0.25rem;
                }
                .toast-message {
                    font-size: 0.875rem;
                    opacity: 0.9;
                }
                .toast-progress {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    height: 3px;
                    background: rgba(255, 255, 255, 0.3);
                    animation: shrink 5s linear forwards;
                }
                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes shrink {
                    from { width: 100%; }
                    to { width: 0%; }
                }
            `
        });

        // Data Table Component
        this.components.set('datatable', {
            template: `
                <div class="tawnia-datatable">
                    <div class="datatable-header">
                        <div class="datatable-title">{{title}}</div>
                        <div class="datatable-controls">
                            <input type="text" class="datatable-search" placeholder="Search..." onkeyup="TawniaComponents.filterTable('{{id}}', this.value)">
                            <button class="btn btn-secondary" onclick="TawniaComponents.exportTable('{{id}}')">
                                <i class="fas fa-download"></i> Export
                            </button>
                        </div>
                    </div>
                    <div class="datatable-container">
                        <table class="datatable" id="{{id}}">
                            {{content}}
                        </table>
                    </div>
                </div>
            `,
            styles: `
                .tawnia-datatable {
                    background: var(--bg-card);
                    border-radius: 0.75rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    overflow: hidden;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }
                .datatable-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
                    background: rgba(45, 55, 72, 0.5);
                }
                .datatable-title {
                    font-size: 1.125rem;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                .datatable-controls {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                .datatable-search {
                    padding: 0.5rem 1rem;
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    border-radius: 0.375rem;
                    background: var(--bg-input);
                    color: var(--text-primary);
                    font-size: 0.875rem;
                }
                .datatable-container {
                    overflow-x: auto;
                    max-height: 60vh;
                }
                .datatable {
                    width: 100%;
                    border-collapse: collapse;
                }
                .datatable th,
                .datatable td {
                    padding: 0.75rem 1rem;
                    text-align: left;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
                }
                .datatable th {
                    background: rgba(45, 55, 72, 0.8);
                    font-weight: 600;
                    color: var(--text-primary);
                    position: sticky;
                    top: 0;
                    z-index: 10;
                }
                .datatable tbody tr:hover {
                    background: rgba(59, 130, 246, 0.05);
                }
                .datatable tbody tr.filtered {
                    display: none;
                }
            `
        });

        this.injectComponentStyles();
    }

    /**
     * Inject component styles into the page
     */
    injectComponentStyles() {
        const styles = Array.from(this.components.values())
            .map(component => component.styles)
            .join('\n');

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    /**
     * Setup global event listeners
     */
    setupGlobalEventListeners() {
        // Listen for theme changes
        window.addEventListener('tawnia:themeChanged', (e) => {
            this.updateTheme(e.detail.theme);
        });

        // Listen for language changes
        window.addEventListener('tawnia:languageChanged', (e) => {
            this.updateLanguage(e.detail.language);
        });

        // Setup toast container
        this.createToastContainer();
    }

    /**
     * Initialize theme
     */
    initializeTheme() {
        const savedTheme = localStorage.getItem('tawnia_theme') || 'dark';
        this.updateTheme(savedTheme);
    }

    /**
     * Update theme
     */
    updateTheme(theme) {
        const themeColors = this.themes[theme] || this.themes.dark;
        const root = document.documentElement;

        Object.entries(themeColors).forEach(([key, value]) => {
            root.style.setProperty(`--theme-${key}`, value);
        });

        document.body.setAttribute('data-theme', theme);
    }

    /**
     * Update language
     */
    updateLanguage(language) {
        document.body.setAttribute('data-lang', language);
        document.body.setAttribute('dir', language === 'ar' ? 'rtl' : 'ltr');
    }

    /**
     * Create component instance
     */
    static create(componentName, props = {}) {
        const instance = window.TawniaComponents || new TawniaComponents();
        const component = instance.components.get(componentName);
        
        if (!component) {
            console.error(`Component '${componentName}' not found`);
            return null;
        }

        let html = component.template;
        
        // Replace template variables
        Object.entries(props).forEach(([key, value]) => {
            const regex = new RegExp(`{{${key}}}`, 'g');
            html = html.replace(regex, value);
        });

        return html;
    }

    /**
     * Show loading spinner
     */
    static showLoading(container, text = 'Loading...') {
        const element = typeof container === 'string' ? document.getElementById(container) : container;
        if (element) {
            element.innerHTML = TawniaComponents.create('spinner', { text });
        }
    }

    /**
     * Show alert
     */
    static showAlert(container, type, title, message, icon = null) {
        const icons = {
            success: 'check-circle',
            warning: 'exclamation-triangle',
            danger: 'times-circle',
            info: 'info-circle'
        };

        const alertIcon = icon || icons[type] || 'info-circle';
        const alertHtml = TawniaComponents.create('alert', {
            type,
            title,
            message,
            icon: alertIcon
        });

        const element = typeof container === 'string' ? document.getElementById(container) : container;
        if (element) {
            element.insertAdjacentHTML('beforeend', alertHtml);
        }
    }

    /**
     * Show modal
     */
    static showModal(id, title, content, footer = '') {
        const modalHtml = TawniaComponents.create('modal', {
            id,
            title,
            content,
            footer
        });

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    /**
     * Close modal
     */
    static closeModal(id) {
        const modal = document.querySelector(`[onclick*="${id}"]`);
        if (modal && modal.classList.contains('tawnia-modal-overlay')) {
            modal.remove();
        }
    }

    /**
     * Create toast container
     */
    createToastContainer() {
        if (!document.getElementById('tawnia-toast-container')) {
            const container = document.createElement('div');
            container.id = 'tawnia-toast-container';
            container.style.cssText = `
                position: fixed;
                top: 1rem;
                right: 1rem;
                z-index: 10001;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }
    }

    /**
     * Show toast notification
     */
    static showToast(type, title, message, duration = 5000) {
        const icons = {
            success: 'check-circle',
            warning: 'exclamation-triangle',
            danger: 'times-circle',
            info: 'info-circle'
        };

        const id = `toast-${Date.now()}`;
        const toastHtml = TawniaComponents.create('toast', {
            id,
            type,
            title,
            message,
            icon: icons[type] || 'info-circle'
        });

        const container = document.getElementById('tawnia-toast-container');
        if (container) {
            container.insertAdjacentHTML('beforeend', toastHtml);
            
            // Auto remove after duration
            setTimeout(() => {
                const toast = document.getElementById(id);
                if (toast) {
                    toast.style.animation = 'slideOutRight 0.3s ease forwards';
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }
    }

    /**
     * Create data table
     */
    static createDataTable(container, title, headers, data, id = null) {
        const tableId = id || `table-${Date.now()}`;
        
        // Build table content
        let tableContent = '<thead><tr>';
        headers.forEach(header => {
            tableContent += `<th>${header}</th>`;
        });
        tableContent += '</tr></thead><tbody>';
        
        data.forEach(row => {
            tableContent += '<tr>';
            row.forEach(cell => {
                tableContent += `<td>${cell}</td>`;
            });
            tableContent += '</tr>';
        });
        tableContent += '</tbody>';

        const tableHtml = TawniaComponents.create('datatable', {
            id: tableId,
            title,
            content: tableContent
        });

        const element = typeof container === 'string' ? document.getElementById(container) : container;
        if (element) {
            element.innerHTML = tableHtml;
        }

        return tableId;
    }

    /**
     * Filter table
     */
    static filterTable(tableId, query) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        const searchQuery = query.toLowerCase();

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchQuery)) {
                row.classList.remove('filtered');
            } else {
                row.classList.add('filtered');
            }
        });
    }

    /**
     * Export table to CSV
     */
    static exportTable(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const rows = Array.from(table.querySelectorAll('tr:not(.filtered)'));
        const csv = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('th, td'));
            return cells.map(cell => `"${cell.textContent}"`).join(',');
        }).join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${tableId}-export.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    /**
     * Format number with locale
     */
    static formatNumber(number, options = {}) {
        const defaults = {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        };
        
        return new Intl.NumberFormat('en-US', { ...defaults, ...options }).format(number);
    }

    /**
     * Format date with locale
     */
    static formatDate(date, options = {}) {
        const defaults = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        
        return new Intl.DateTimeFormat('en-US', { ...defaults, ...options }).format(new Date(date));
    }

    /**
     * Debounce function
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Copy to clipboard
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            TawniaComponents.showToast('success', 'Copied!', 'Text copied to clipboard');
        } catch (err) {
            console.error('Failed to copy:', err);
            TawniaComponents.showToast('danger', 'Error', 'Failed to copy to clipboard');
        }
    }
}

// Initialize components when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.TawniaComponents = new TawniaComponents();
    });
} else {
    window.TawniaComponents = new TawniaComponents();
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TawniaComponents;
}