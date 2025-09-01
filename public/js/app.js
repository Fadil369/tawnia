/**
 * BrainSAIT Enhanced - Tawuniya Healthcare Insurance Analyzer
 * Main Application JavaScript
 */

class TawniaAnalyzer {
    constructor() {
        this.apiBase = '/api';
        this.currentData = null;
        this.charts = {};
        this.uploadedFiles = [];
        this.processingQueue = [];

        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.loadQuickStats();
        this.loadHistory();

        // Initialize charts
        this.initializeCharts();

        console.log('🚀 BrainSAIT Enhanced Analyzer initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // File input change
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });

        // Window resize for responsive charts
        window.addEventListener('resize', () => {
            this.resizeCharts();
        });
    }

    /**
     * Setup drag and drop functionality
     */
    setupDragAndDrop() {
        const uploadArea = document.querySelector('.upload-area');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFileSelection(files);
        }, false);
    }

    /**
     * Prevent default drag behaviors
     */
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    /**
     * Switch between tabs
     */
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load tab-specific content
        this.loadTabContent(tabName);
    }

    /**
     * Load content for specific tab
     */
    async loadTabContent(tabName) {
        switch (tabName) {
            case 'analyze':
                await this.loadAnalysisData();
                break;
            case 'insights':
                await this.loadAIInsights();
                break;
            case 'reports':
                this.loadReportsData();
                break;
            case 'history':
                await this.loadHistory();
                break;
        }
    }

    /**
     * Handle file selection
     */
    async handleFileSelection(files) {
        if (!files || files.length === 0) return;

        const validFiles = Array.from(files).filter(file => {
            const validExtensions = ['.xlsx', '.xls', '.csv'];
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            return validExtensions.includes(extension);
        });

        if (validFiles.length === 0) {
            this.showNotification('Please select valid Excel or CSV files', 'error');
            return;
        }

        if (validFiles.length !== files.length) {
            this.showNotification(`${files.length - validFiles.length} files were skipped (invalid format)`, 'warning');
        }

        await this.uploadFiles(validFiles);
    }

    /**
     * Upload files to server
     */
    async uploadFiles(files) {
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        progressContainer.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = 'Preparing upload...';

        try {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);

                progressText.textContent = `Uploading ${file.name} (${i + 1}/${files.length})`;

                // Simulate progress for better UX
                let progress = 0;
                const progressInterval = setInterval(() => {
                    progress += Math.random() * 15;
                    if (progress > 90) progress = 90;
                    progressFill.style.width = `${progress}%`;
                }, 200);

                const response = await fetch(`${this.apiBase}/upload/single`, {
                    method: 'POST',
                    body: formData
                });

                clearInterval(progressInterval);
                progressFill.style.width = '100%';

                const result = await response.json();

                if (result.success) {
                    this.uploadedFiles.push(result.data);
                    this.showNotification(`Successfully processed ${file.name}`, 'success');
                } else {
                    this.showNotification(`Failed to process ${file.name}: ${result.message}`, 'error');
                }

                // Brief pause between files
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            progressText.textContent = 'Upload completed!';

            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000);

            // Update UI
            await this.loadQuickStats();
            await this.loadHistory();

        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification('Upload failed. Please try again.', 'error');
            progressContainer.style.display = 'none';
        }
    }

    /**
     * Load quick stats for dashboard
     */
    async loadQuickStats() {
        try {
            const response = await fetch(`${this.apiBase}/upload/list`);
            const result = await response.json();

            if (result.success) {
                const files = result.data.files;
                const totalFiles = files.length;
                const successfulFiles = files.filter(f => f.overallQuality > 0).length;
                const successRate = totalFiles > 0 ? Math.round((successfulFiles / totalFiles) * 100) : 0;
                const avgQuality = files.length > 0
                    ? Math.round(files.reduce((sum, f) => sum + (f.overallQuality || 0), 0) / files.length)
                    : 0;

                document.getElementById('totalFiles').textContent = totalFiles;
                document.getElementById('successRate').textContent = `${successRate}%`;
                document.getElementById('dataQuality').textContent = avgQuality > 0 ? `${avgQuality}%` : 'N/A';
            }
        } catch (error) {
            console.error('Failed to load quick stats:', error);
        }
    }

    /**
     * Load analysis data
     */
    async loadAnalysisData() {
        const loading = document.getElementById('analysisLoading');
        const content = document.getElementById('analysisContent');

        loading.classList.remove('hidden');
        content.classList.add('hidden');

        try {
            // Get all processed files
            const response = await fetch(`${this.apiBase}/upload/list`);
            const result = await response.json();

            if (result.success && result.data.files.length > 0) {
                // Analyze the most recent file or aggregate data
                const latestFile = result.data.files[0];
                await this.analyzeFileData(latestFile.resultId);
            } else {
                this.showEmptyAnalysis();
            }

        } catch (error) {
            console.error('Failed to load analysis data:', error);
            this.showNotification('Failed to load analysis data', 'error');
        } finally {
            loading.classList.add('hidden');
            content.classList.remove('hidden');
        }
    }

    /**
     * Analyze specific file data
     */
    async analyzeFileData(resultId) {
        try {
            const response = await fetch(`${this.apiBase}/upload/results/${resultId}`);
            const result = await response.json();

            if (result.success) {
                this.currentData = result.data;
                this.updateAnalysisCharts();
                this.updateAnalysisMetrics();
            }
        } catch (error) {
            console.error('Failed to analyze file data:', error);
        }
    }

    /**
     * Update analysis charts
     */
    updateAnalysisCharts() {
        if (!this.currentData) return;

        // Update rejection chart
        this.updateRejectionChart();

        // Update trends chart
        this.updateTrendsChart();
    }

    /**
     * Update rejection analysis chart
     */
    updateRejectionChart() {
        const ctx = document.getElementById('rejectionChart').getContext('2d');

        // Aggregate rejection data from all sheets
        const rejectionData = {};

        this.currentData.sheets.forEach(sheet => {
            if (sheet.analysis && sheet.analysis.patterns && sheet.analysis.patterns.rejectionReasons) {
                Object.entries(sheet.analysis.patterns.rejectionReasons).forEach(([reason, count]) => {
                    rejectionData[reason] = (rejectionData[reason] || 0) + count;
                });
            }
        });

        const labels = Object.keys(rejectionData);
        const data = Object.values(rejectionData);
        const colors = this.generateColors(labels.length);

        if (this.charts.rejectionChart) {
            this.charts.rejectionChart.destroy();
        }

        this.charts.rejectionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#1e293b',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#f1f5f9',
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#f1f5f9',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                }
            }
        });
    }

    /**
     * Update trends chart
     */
    updateTrendsChart() {
        const ctx = document.getElementById('trendsChart').getContext('2d');

        // Aggregate trends data from all sheets
        const trendsData = {};

        this.currentData.sheets.forEach(sheet => {
            if (sheet.analysis && sheet.analysis.patterns && sheet.analysis.patterns.monthlyTrends) {
                Object.entries(sheet.analysis.patterns.monthlyTrends).forEach(([month, count]) => {
                    trendsData[month] = (trendsData[month] || 0) + count;
                });
            }
        });

        const sortedMonths = Object.keys(trendsData).sort();
        const labels = sortedMonths;
        const data = sortedMonths.map(month => trendsData[month]);

        if (this.charts.trendsChart) {
            this.charts.trendsChart.destroy();
        }

        this.charts.trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Claims Count',
                    data: data,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#2563eb',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f1f5f9'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#f1f5f9',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        });
    }

    /**
     * Update analysis metrics
     */
    updateAnalysisMetrics() {
        if (!this.currentData) return;

        // Calculate rejection rate
        let totalClaims = 0;
        let rejectedClaims = 0;
        let topRejectionReason = '';
        let topRejectionCount = 0;

        this.currentData.sheets.forEach(sheet => {
            totalClaims += sheet.data.length;

            if (sheet.analysis && sheet.analysis.patterns && sheet.analysis.patterns.rejectionReasons) {
                Object.entries(sheet.analysis.patterns.rejectionReasons).forEach(([reason, count]) => {
                    rejectedClaims += count;
                    if (count > topRejectionCount) {
                        topRejectionReason = reason;
                        topRejectionCount = count;
                    }
                });
            }
        });

        const rejectionRate = totalClaims > 0 ? Math.round((rejectedClaims / totalClaims) * 100) : 0;

        document.getElementById('rejectionRate').textContent = `${rejectionRate}%`;
        document.getElementById('topRejectionReason').textContent = topRejectionReason || 'No rejection data available';
    }

    /**
     * Load AI insights
     */
    async loadAIInsights() {
        const loading = document.getElementById('insightsLoading');
        const content = document.getElementById('insightsContent');

        loading.classList.remove('hidden');
        content.classList.add('hidden');

        try {
            if (!this.currentData) {
                // Get the latest processed file
                const response = await fetch(`${this.apiBase}/upload/list`);
                const result = await response.json();

                if (result.success && result.data.files.length > 0) {
                    const latestFile = result.data.files[0];
                    const fileResponse = await fetch(`${this.apiBase}/upload/results/${latestFile.resultId}`);
                    const fileResult = await fileResponse.json();

                    if (fileResult.success) {
                        this.currentData = fileResult.data;
                    }
                }
            }

            if (this.currentData) {
                await this.generateAIInsights();
            } else {
                this.showEmptyInsights();
            }

        } catch (error) {
            console.error('Failed to load AI insights:', error);
            this.showNotification('Failed to load AI insights', 'error');
        } finally {
            loading.classList.add('hidden');
            content.classList.remove('hidden');
        }
    }

    /**
     * Generate AI insights
     */
    async generateAIInsights() {
        const insightsContainer = document.getElementById('aiInsightsContent');

        try {
            // For now, generate insights based on the processed data
            // In a full implementation, this would call an AI service
            const insights = this.generateStatisticalInsights();

            insightsContainer.innerHTML = `
                <div class="mb-4">
                    <h4 style="color: var(--primary-color); margin-bottom: 1rem;">
                        <i class="fas fa-brain"></i> Statistical Analysis
                    </h4>
                    ${insights.map(insight => `
                        <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 0.5rem; border-left: 4px solid var(--primary-color);">
                            <strong>${insight.title}:</strong> ${insight.description}
                        </div>
                    `).join('')}
                </div>

                <div class="mb-4">
                    <h4 style="color: var(--success-color); margin-bottom: 1rem;">
                        <i class="fas fa-lightbulb"></i> Recommendations
                    </h4>
                    ${this.generateRecommendations().map(rec => `
                        <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 0.5rem; border-left: 4px solid var(--success-color);">
                            <strong>${rec.title}:</strong> ${rec.description}
                        </div>
                    `).join('')}
                </div>
            `;

        } catch (error) {
            console.error('Failed to generate AI insights:', error);
            insightsContainer.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>Failed to generate insights. Please try again later.</p>
                </div>
            `;
        }
    }

    /**
     * Generate statistical insights from data
     */
    generateStatisticalInsights() {
        if (!this.currentData) return [];

        const insights = [];

        // Data quality insight
        const avgQuality = this.currentData.summary.overallQuality;
        if (avgQuality < 70) {
            insights.push({
                title: 'Data Quality Alert',
                description: `Average data quality is ${avgQuality.toFixed(1)}%, which is below optimal threshold. Consider data cleaning procedures.`
            });
        } else if (avgQuality > 90) {
            insights.push({
                title: 'Excellent Data Quality',
                description: `Your data quality score of ${avgQuality.toFixed(1)}% indicates well-structured and complete datasets.`
            });
        }

        // Volume insights
        const totalRows = this.currentData.summary.totalDataRows;
        if (totalRows > 10000) {
            insights.push({
                title: 'Large Dataset Detected',
                description: `Processing ${totalRows.toLocaleString()} records. Consider implementing batch processing for better performance.`
            });
        }

        // File type insights
        const fileType = this.currentData.fileType;
        insights.push({
            title: 'File Type Analysis',
            description: `Detected ${fileType} format. Optimized processing rules have been applied for this data structure.`
        });

        // Sheet analysis
        const sheetCount = this.currentData.sheets.length;
        if (sheetCount > 5) {
            insights.push({
                title: 'Multi-Sheet Analysis',
                description: `File contains ${sheetCount} sheets. Cross-sheet correlation analysis is recommended for comprehensive insights.`
            });
        }

        return insights;
    }

    /**
     * Generate recommendations
     */
    generateRecommendations() {
        const recommendations = [
            {
                title: 'Regular Data Validation',
                description: 'Implement automated data validation checks to maintain high data quality standards.'
            },
            {
                title: 'Trend Monitoring',
                description: 'Set up monthly trend analysis to identify patterns and anomalies early.'
            },
            {
                title: 'Rejection Prevention',
                description: 'Focus on addressing the top rejection reasons to improve claim approval rates.'
            },
            {
                title: 'Process Optimization',
                description: 'Consider automating routine analysis tasks to improve efficiency and reduce manual errors.'
            }
        ];

        return recommendations;
    }

    /**
     * Show empty analysis state
     */
    showEmptyAnalysis() {
        const content = document.getElementById('analysisContent');
        content.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); padding: 4rem 2rem;">
                <i class="fas fa-chart-line" style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h3 style="margin-bottom: 1rem;">No Data Available</h3>
                <p>Upload Excel files to begin analysis</p>
                <button class="btn btn-primary" onclick="analyzer.switchTab('upload')" style="margin-top: 1rem;">
                    <i class="fas fa-upload"></i>
                    Upload Files
                </button>
            </div>
        `;
    }

    /**
     * Show empty insights state
     */
    showEmptyInsights() {
        const content = document.getElementById('insightsContent');
        content.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); padding: 4rem 2rem;">
                <i class="fas fa-lightbulb" style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h3 style="margin-bottom: 1rem;">No Insights Available</h3>
                <p>Process some data files to generate AI-powered insights</p>
                <button class="btn btn-primary" onclick="analyzer.switchTab('upload')" style="margin-top: 1rem;">
                    <i class="fas fa-upload"></i>
                    Upload Files
                </button>
            </div>
        `;
    }

    /**
     * Load processing history
     */
    async loadHistory() {
        try {
            const response = await fetch(`${this.apiBase}/upload/list`);
            const result = await response.json();

            const tableBody = document.getElementById('historyTableBody');

            if (result.success && result.data.files.length > 0) {
                tableBody.innerHTML = result.data.files.map(file => `
                    <tr>
                        <td>${file.filename}</td>
                        <td>
                            <span class="status info">
                                ${this.formatFileType(file.fileType)}
                            </span>
                        </td>
                        <td>${new Date(file.processedAt).toLocaleString()}</td>
                        <td>
                            <span class="status ${this.getQualityStatus(file.overallQuality)}">
                                ${file.overallQuality ? `${file.overallQuality.toFixed(1)}%` : 'N/A'}
                            </span>
                        </td>
                        <td>
                            <span class="status success">
                                <i class="fas fa-check-circle"></i>
                                Completed
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-secondary" onclick="analyzer.viewFile('${file.resultId}')" style="margin-right: 0.5rem;">
                                <i class="fas fa-eye"></i>
                                View
                            </button>
                            <button class="btn btn-danger" onclick="analyzer.deleteFile('${file.resultId}')">
                                <i class="fas fa-trash"></i>
                                Delete
                            </button>
                        </td>
                    </tr>
                `).join('');
            } else {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                            <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 1rem; display: block; opacity: 0.5;"></i>
                            No files processed yet
                        </td>
                    </tr>
                `;
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    /**
     * Initialize charts
     */
    initializeCharts() {
        Chart.defaults.color = '#cbd5e1';
        Chart.defaults.backgroundColor = '#1e293b';
        Chart.defaults.borderColor = '#334155';
    }

    /**
     * Resize charts on window resize
     */
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }

    /**
     * Generate colors for charts
     */
    generateColors(count) {
        const baseColors = [
            '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#06b6d4',
            '#8b5cf6', '#f97316', '#84cc16', '#ec4899', '#6366f1'
        ];

        const colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }

        return colors;
    }

    /**
     * Format file type for display
     */
    formatFileType(fileType) {
        const typeMap = {
            'Healthcare_Analytics_Report': 'Healthcare Analytics',
            'HNH_StatementOfAccount': 'HNH Statement',
            'TAWUNIYA_MEDICAL_INSURANCE': 'Tawuniya Medical',
            'UNKNOWN': 'Unknown Format'
        };

        return typeMap[fileType] || fileType;
    }

    /**
     * Get quality status class
     */
    getQualityStatus(quality) {
        if (!quality) return 'info';
        if (quality >= 90) return 'success';
        if (quality >= 70) return 'warning';
        return 'danger';
    }

    /**
     * View specific file details
     */
    async viewFile(resultId) {
        try {
            const response = await fetch(`${this.apiBase}/upload/results/${resultId}`);
            const result = await response.json();

            if (result.success) {
                this.currentData = result.data;
                this.switchTab('analyze');
            } else {
                this.showNotification('Failed to load file details', 'error');
            }
        } catch (error) {
            console.error('Failed to view file:', error);
            this.showNotification('Failed to load file details', 'error');
        }
    }

    /**
     * Delete specific file
     */
    async deleteFile(resultId) {
        if (!confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/upload/results/${resultId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('File deleted successfully', 'success');
                await this.loadHistory();
                await this.loadQuickStats();
            } else {
                this.showNotification('Failed to delete file', 'error');
            }
        } catch (error) {
            console.error('Failed to delete file:', error);
            this.showNotification('Failed to delete file', 'error');
        }
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: var(--radius-md);
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 400px;
            box-shadow: var(--shadow-lg);
            transform: translateX(400px);
            transition: transform 0.3s ease;
        `;

        // Set background color based on type
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#06b6d4'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        // Add icon
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i class="${icons[type] || icons.info}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 4000);
    }
}

// Global functions for HTML onclick handlers
function downloadTemplate() {
    // Implementation for downloading Excel template
    console.log('Downloading template...');
}

function showHelp() {
    // Implementation for showing help modal
    console.log('Showing help...');
}

function refreshChart(chartId) {
    // Implementation for refreshing specific chart
    if (analyzer.charts[chartId]) {
        analyzer.charts[chartId].update();
    }
}

function generateReport(format) {
    // Get selected file for report generation
    const selectedFile = analyzer.uploadedFiles.find(file => file.selected);
    if (!selectedFile) {
        analyzer.showNotification('Please select a processed file first', 'error');
        return;
    }

    // Generate report using the comprehensive backend API
    generateReportAdvanced(selectedFile.id, format);
}

async function generateReportAdvanced(resultId, format = 'json') {
    try {
        analyzer.showNotification(`Generating ${format.toUpperCase()} report...`, 'info');

        const response = await fetch('/api/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                resultId: resultId,
                format: format,
                sections: ['summary', 'analysis', 'insights']
            })
        });

        if (response.ok) {
            const result = await response.json();

            // Auto-download the report
            window.open(result.data.downloadUrl, '_blank');

            analyzer.showNotification(`${format.toUpperCase()} report generated and downloaded!`, 'success');

            // Refresh reports list if on reports tab
            if (document.getElementById('reportsTab').classList.contains('active')) {
                loadReportsList();
            }
        } else {
            throw new Error('Report generation failed');
        }
    } catch (error) {
        console.error('Report generation error:', error);
        analyzer.showNotification(`Failed to generate ${format.toUpperCase()} report`, 'error');
    }
}

async function analyzeRejections(resultId) {
    if (!resultId) {
        analyzer.showNotification('Please select a processed file first', 'error');
        return;
    }

    try {
        analyzer.showNotification('Analyzing rejections...', 'info');
        const response = await fetch('/api/analyze/rejections', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resultId })
        });

        if (response.ok) {
            const result = await response.json();
            displayAnalysisResults('rejections', result.data);
            analyzer.showNotification('Rejection analysis completed!', 'success');
        } else {
            throw new Error('Analysis failed');
        }
    } catch (error) {
        console.error('Rejection analysis error:', error);
        analyzer.showNotification('Failed to analyze rejections', 'error');
    }
}

async function analyzeTrends(resultId) {
    if (!resultId) {
        analyzer.showNotification('Please select a processed file first', 'error');
        return;
    }

    try {
        analyzer.showNotification('Analyzing trends...', 'info');
        const response = await fetch('/api/analyze/trends', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resultId })
        });

        if (response.ok) {
            const result = await response.json();
            displayAnalysisResults('trends', result.data);
            analyzer.showNotification('Trend analysis completed!', 'success');
        } else {
            throw new Error('Trend analysis failed');
        }
    } catch (error) {
        console.error('Trend analysis error:', error);
        analyzer.showNotification('Failed to analyze trends', 'error');
    }
}

async function generateInsights(resultId) {
    if (!resultId) {
        analyzer.showNotification('Please select a processed file first', 'error');
        return;
    }

    try {
        analyzer.showNotification('Generating AI insights...', 'info');
        const response = await fetch('/api/insights/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resultId })
        });

        if (response.ok) {
            const result = await response.json();
            displayInsights(result.data);
            analyzer.showNotification('AI insights generated!', 'success');
        } else {
            throw new Error('Insights generation failed');
        }
    } catch (error) {
        console.error('Insights generation error:', error);
        analyzer.showNotification('Failed to generate insights', 'error');
    }
}

async function loadReportsList() {
    try {
        const response = await fetch('/api/reports/list');
        if (response.ok) {
            const result = await response.json();
            displayReportsList(result.data.reports);
        }
    } catch (error) {
        console.error('Failed to load reports list:', error);
    }
}

async function deleteReport(filename) {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/reports/${filename}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            analyzer.showNotification('Report deleted successfully', 'success');
            loadReportsList();
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        analyzer.showNotification('Failed to delete report', 'error');
    }
}

function displayAnalysisResults(type, data) {
    const resultsContainer = document.getElementById('analysisResults') || createAnalysisResultsContainer();

    let html = `<div class="analysis-section">
        <h3>${type.charAt(0).toUpperCase() + type.slice(1)} Analysis Results</h3>`;

    if (data.summary) {
        html += `<div class="summary-stats">
            <h4>Summary</h4>
            ${Object.entries(data.summary).map(([key, value]) =>
                `<div class="stat-item"><strong>${key}:</strong> ${value}</div>`
            ).join('')}
        </div>`;
    }

    if (data.details) {
        html += `<div class="analysis-details">
            <h4>Details</h4>
            <pre>${JSON.stringify(data.details, null, 2)}</pre>
        </div>`;
    }

    html += '</div>';
    resultsContainer.innerHTML = html;
}

function displayInsights(data) {
    const insightsContainer = document.getElementById('insightsResults') || createInsightsContainer();

    let html = `<div class="insights-section">
        <h3>AI-Powered Insights</h3>`;

    if (data.insights) {
        html += `<div class="insights-list">
            ${data.insights.map(insight =>
                `<div class="insight-item">
                    <strong>${insight.category}:</strong> ${insight.description}
                    <span class="confidence">Confidence: ${(insight.confidence * 100).toFixed(1)}%</span>
                </div>`
            ).join('')}
        </div>`;
    }

    if (data.recommendations) {
        html += `<div class="recommendations">
            <h4>Recommendations</h4>
            <ul>
                ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>`;
    }

    html += '</div>';
    insightsContainer.innerHTML = html;
}

function displayReportsList(reports) {
    const reportsContainer = document.getElementById('reportsList') || createReportsListContainer();

    if (reports.length === 0) {
        reportsContainer.innerHTML = '<p>No reports available</p>';
        return;
    }

    let html = '<div class="reports-grid">';
    reports.forEach(report => {
        html += `<div class="report-item">
            <div class="report-info">
                <strong>${report.filename}</strong>
                <div class="report-meta">
                    Format: ${report.format} | Size: ${(report.size / 1024).toFixed(1)} KB
                    <br>Created: ${new Date(report.createdAt).toLocaleString()}
                </div>
            </div>
            <div class="report-actions">
                <a href="${report.downloadUrl}" download class="btn btn-primary btn-sm">Download</a>
                <button onclick="deleteReport('${report.filename}')" class="btn btn-danger btn-sm">Delete</button>
            </div>
        </div>`;
    });
    html += '</div>';

    reportsContainer.innerHTML = html;
}

function createAnalysisResultsContainer() {
    const container = document.createElement('div');
    container.id = 'analysisResults';
    container.className = 'analysis-results';
    document.getElementById('analysisContent').appendChild(container);
    return container;
}

function createInsightsContainer() {
    const container = document.createElement('div');
    container.id = 'insightsResults';
    container.className = 'insights-results';
    document.getElementById('insightsContent').appendChild(container);
    return container;
}

function createReportsListContainer() {
    const container = document.createElement('div');
    container.id = 'reportsList';
    container.className = 'reports-list';
    document.getElementById('reportsContent').appendChild(container);
    return container;
}

function refreshHistory() {
    analyzer.loadHistory();
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all processing history? This action cannot be undone.')) {
        // Implementation for clearing history
        console.log('Clearing history...');
    }
}

// New analysis function to handle different analysis types
async function runSelectedAnalysis(type) {
    const selectedFile = analyzer.uploadedFiles.find(file => file.selected);
    if (!selectedFile) {
        analyzer.showNotification('Please select a processed file first', 'error');
        return;
    }

    switch(type) {
        case 'rejections':
            await analyzeRejections(selectedFile.id);
            break;
        case 'trends':
            await analyzeTrends(selectedFile.id);
            break;
        case 'patterns':
            await analyzePatterns(selectedFile.id);
            break;
        case 'insights':
            await generateInsights(selectedFile.id);
            break;
        default:
            analyzer.showNotification('Unknown analysis type', 'error');
    }
}

async function analyzePatterns(resultId) {
    if (!resultId) {
        analyzer.showNotification('Please select a processed file first', 'error');
        return;
    }

    try {
        analyzer.showNotification('Analyzing patterns...', 'info');
        const response = await fetch('/api/analyze/patterns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resultId })
        });

        if (response.ok) {
            const result = await response.json();
            displayAnalysisResults('patterns', result.data);
            analyzer.showNotification('Pattern analysis completed!', 'success');
        } else {
            throw new Error('Pattern analysis failed');
        }
    } catch (error) {
        console.error('Pattern analysis error:', error);
        analyzer.showNotification('Failed to analyze patterns', 'error');
    }
}

// Initialize reports list when reports tab is shown
document.addEventListener('DOMContentLoaded', function() {
    // Override the original showTab function to load reports when reports tab is selected
    const originalShowTab = window.showTab;
    window.showTab = function(tabName) {
        originalShowTab(tabName);

        if (tabName === 'reports') {
            loadReportsList();
        }
    };
});

// Initialize the application when DOM is loaded
let analyzer;
document.addEventListener('DOMContentLoaded', () => {
    analyzer = new TawniaAnalyzer();
});
