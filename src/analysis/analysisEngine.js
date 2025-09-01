const moment = require('moment');
const _ = require('lodash');

/**
 * Advanced Analysis Engine for Healthcare Insurance Data
 * Provides comprehensive analysis capabilities for Tawuniya data processing
 */
class AnalysisEngine {
  constructor() {
    this.rejectionReasonCategories = {
      'medical': ['medical necessity', 'treatment not covered', 'experimental', 'investigational'],
      'administrative': ['missing documentation', 'prior authorization', 'referral required', 'coding error'],
      'eligibility': ['member not eligible', 'coverage expired', 'waiting period', 'pre-existing condition'],
      'financial': ['benefit limit exceeded', 'deductible not met', 'copay required', 'coinsurance']
    };
  }

  /**
   * Analyze rejection patterns in healthcare data
   */
  async analyzeRejections(processedData, analysisType = 'comprehensive') {
    const analysis = {
      summary: {
        totalClaims: 0,
        rejectedClaims: 0,
        rejectionRate: 0,
        averageRejectedAmount: 0,
        totalRejectedAmount: 0
      },
      patterns: {
        byReason: {},
        byCategory: {},
        byProvider: {},
        bySpecialty: {},
        byMonth: {},
        byAmountRange: {}
      },
      trends: {
        monthly: {},
        weekday: {},
        seasonal: {}
      },
      insights: []
    };

    // Process each sheet
    for (const sheet of processedData.sheets) {
      await this.analyzeSheetRejections(sheet, analysis);
    }

    // Calculate summary statistics
    this.calculateRejectionSummary(analysis);

    // Generate insights
    analysis.insights = this.generateRejectionInsights(analysis);

    // Add detailed analysis if requested
    if (analysisType === 'comprehensive') {
      analysis.detailedAnalysis = await this.performDetailedRejectionAnalysis(processedData);
    }

    return analysis;
  }

  /**
   * Analyze individual sheet for rejections
   */
  async analyzeSheetRejections(sheet, analysis) {
    for (const row of sheet.data) {
      analysis.summary.totalClaims++;

      // Check if claim is rejected
      const isRejected = this.isClaimRejected(row);
      if (isRejected) {
        analysis.summary.rejectedClaims++;

        // Analyze rejection reason
        const rejectionReason = this.extractRejectionReason(row);
        if (rejectionReason) {
          analysis.patterns.byReason[rejectionReason] = (analysis.patterns.byReason[rejectionReason] || 0) + 1;

          // Categorize rejection reason
          const category = this.categorizeRejectionReason(rejectionReason);
          analysis.patterns.byCategory[category] = (analysis.patterns.byCategory[category] || 0) + 1;
        }

        // Analyze by provider
        const provider = this.extractProvider(row);
        if (provider) {
          analysis.patterns.byProvider[provider] = (analysis.patterns.byProvider[provider] || 0) + 1;
        }

        // Analyze by specialty
        const specialty = this.extractSpecialty(row);
        if (specialty) {
          analysis.patterns.bySpecialty[specialty] = (analysis.patterns.bySpecialty[specialty] || 0) + 1;
        }

        // Analyze by date
        const claimDate = this.extractDate(row);
        if (claimDate && moment(claimDate).isValid()) {
          const monthKey = moment(claimDate).format('YYYY-MM');
          analysis.patterns.byMonth[monthKey] = (analysis.patterns.byMonth[monthKey] || 0) + 1;

          const weekday = moment(claimDate).format('dddd');
          analysis.trends.weekday[weekday] = (analysis.trends.weekday[weekday] || 0) + 1;
        }

        // Analyze by amount
        const amount = this.extractAmount(row);
        if (amount) {
          analysis.summary.totalRejectedAmount += amount;
          const amountRange = this.getAmountRange(amount);
          analysis.patterns.byAmountRange[amountRange] = (analysis.patterns.byAmountRange[amountRange] || 0) + 1;
        }
      }
    }
  }

  /**
   * Calculate rejection summary statistics
   */
  calculateRejectionSummary(analysis) {
    const { totalClaims, rejectedClaims, totalRejectedAmount } = analysis.summary;

    analysis.summary.rejectionRate = totalClaims > 0 ? (rejectedClaims / totalClaims) * 100 : 0;
    analysis.summary.averageRejectedAmount = rejectedClaims > 0 ? totalRejectedAmount / rejectedClaims : 0;

    // Sort patterns by frequency
    analysis.patterns.byReason = this.sortByValue(analysis.patterns.byReason);
    analysis.patterns.byCategory = this.sortByValue(analysis.patterns.byCategory);
    analysis.patterns.byProvider = this.sortByValue(analysis.patterns.byProvider);
    analysis.patterns.bySpecialty = this.sortByValue(analysis.patterns.bySpecialty);
  }

  /**
   * Analyze trends in healthcare data
   */
  async analyzeTrends(processedData, timeframe = 'monthly', metrics = ['claims', 'rejections']) {
    const analysis = {
      timeframe,
      metrics,
      trends: {},
      patterns: {
        growth: {},
        seasonality: {},
        cyclical: {}
      },
      forecasts: {},
      insights: []
    };

    // Initialize trend data structures
    for (const metric of metrics) {
      analysis.trends[metric] = {};
    }

    // Process each sheet
    for (const sheet of processedData.sheets) {
      await this.analyzeSheetTrends(sheet, analysis, timeframe, metrics);
    }

    // Analyze patterns and generate forecasts
    this.analyzeTrendPatterns(analysis);
    analysis.insights = this.generateTrendInsights(analysis);

    return analysis;
  }

  /**
   * Analyze individual sheet for trends
   */
  async analyzeSheetTrends(sheet, analysis, timeframe, metrics) {
    for (const row of sheet.data) {
      const date = this.extractDate(row);
      if (!date || !moment(date).isValid()) continue;

      const periodKey = this.getPeriodKey(date, timeframe);

      for (const metric of metrics) {
        if (!analysis.trends[metric][periodKey]) {
          analysis.trends[metric][periodKey] = {
            count: 0,
            amount: 0,
            rejections: 0
          };
        }

        switch (metric) {
          case 'claims':
            analysis.trends[metric][periodKey].count++;
            const amount = this.extractAmount(row);
            if (amount) analysis.trends[metric][periodKey].amount += amount;
            break;

          case 'rejections':
            if (this.isClaimRejected(row)) {
              analysis.trends[metric][periodKey].rejections++;
            }
            break;

          case 'volume':
            analysis.trends[metric][periodKey].count++;
            break;
        }
      }
    }
  }

  /**
   * Analyze patterns across multiple datasets
   */
  async analyzePatterns(datasets, patternTypes = ['claims', 'rejections', 'providers']) {
    const analysis = {
      patternTypes,
      crossFilePatterns: {},
      commonalities: {},
      differences: {},
      correlations: {},
      insights: []
    };

    // Initialize pattern structures
    for (const patternType of patternTypes) {
      analysis.crossFilePatterns[patternType] = {};
    }

    // Analyze each dataset
    for (let i = 0; i < datasets.length; i++) {
      const dataset = datasets[i];
      await this.extractDatasetPatterns(dataset, analysis, i);
    }

    // Find cross-dataset patterns
    this.findCrossDatasetPatterns(analysis, datasets.length);
    analysis.insights = this.generatePatternInsights(analysis);

    return analysis;
  }

  /**
   * Perform comprehensive data quality analysis
   */
  async analyzeDataQuality(processedData, includeRecommendations = true) {
    const analysis = {
      overallScore: 0,
      dimensions: {
        completeness: 0,
        consistency: 0,
        validity: 0,
        accuracy: 0,
        uniqueness: 0
      },
      sheetAnalysis: [],
      issues: [],
      recommendations: [],
      trends: {
        qualityBySheet: {},
        issueFrequency: {}
      }
    };

    // Analyze each sheet
    for (const sheet of processedData.sheets) {
      const sheetQuality = await this.analyzeSheetQuality(sheet);
      analysis.sheetAnalysis.push(sheetQuality);
    }

    // Calculate overall quality metrics
    this.calculateOverallQuality(analysis);

    // Generate recommendations if requested
    if (includeRecommendations) {
      analysis.recommendations = this.generateQualityRecommendations(analysis);
    }

    return analysis;
  }

  /**
   * Compare multiple datasets
   */
  async compareDatasets(datasets, comparisonMetrics = ['volume', 'quality', 'rejections']) {
    const analysis = {
      comparisonMetrics,
      datasets: datasets.map(d => ({
        resultId: d.resultId,
        filename: d.data.filename,
        summary: {}
      })),
      comparisons: {},
      rankings: {},
      insights: []
    };

    // Analyze each dataset
    for (let i = 0; i < datasets.length; i++) {
      const dataset = datasets[i];
      analysis.datasets[i].summary = await this.generateDatasetSummary(dataset.data);
    }

    // Perform comparisons
    for (const metric of comparisonMetrics) {
      analysis.comparisons[metric] = this.compareMetric(analysis.datasets, metric);
      analysis.rankings[metric] = this.rankDatasets(analysis.datasets, metric);
    }

    analysis.insights = this.generateComparisonInsights(analysis);

    return analysis;
  }

  /**
   * Get available metrics for a dataset
   */
  getAvailableMetrics(processedData) {
    const metrics = {
      volume: [],
      quality: [],
      temporal: [],
      financial: [],
      medical: []
    };

    // Check what metrics are available based on data structure
    for (const sheet of processedData.sheets) {
      if (sheet.headers.some(h => this.isDateField(h))) {
        metrics.temporal.push('trends', 'seasonality', 'patterns');
      }

      if (sheet.headers.some(h => this.isAmountField(h))) {
        metrics.financial.push('amounts', 'cost_analysis', 'financial_trends');
      }

      if (sheet.headers.some(h => this.isRejectionField(h))) {
        metrics.quality.push('rejection_analysis', 'approval_rates');
      }

      if (sheet.headers.some(h => this.isMedicalField(h))) {
        metrics.medical.push('specialty_analysis', 'procedure_analysis');
      }

      metrics.volume.push('claim_counts', 'data_volume');
      metrics.quality.push('data_quality', 'completeness');
    }

    return metrics;
  }

  /**
   * Get recommended analyses based on data content
   */
  getRecommendedAnalyses(processedData) {
    const recommendations = [];

    const fileType = processedData.fileType;

    switch (fileType) {
      case 'Healthcare_Analytics_Report':
        recommendations.push(
          'rejection_analysis',
          'trend_analysis',
          'provider_performance',
          'specialty_patterns'
        );
        break;

      case 'HNH_StatementOfAccount':
        recommendations.push(
          'financial_analysis',
          'payment_patterns',
          'account_trends'
        );
        break;

      case 'TAWUNIYA_MEDICAL_INSURANCE':
        recommendations.push(
          'policy_analysis',
          'claim_patterns',
          'beneficiary_analysis',
          'network_performance'
        );
        break;

      default:
        recommendations.push(
          'data_quality_analysis',
          'pattern_discovery',
          'trend_analysis'
        );
    }

    return recommendations;
  }

  // Helper methods

  /**
   * Check if claim is rejected
   */
  isClaimRejected(row) {
    const statusFields = ['status', 'claim_status', 'approval_status', 'result'];

    for (const field of statusFields) {
      const value = this.getFieldValue(row, field);
      if (value && typeof value === 'string') {
        const lowerValue = value.toLowerCase();
        if (lowerValue.includes('reject') || lowerValue.includes('denied') ||
            lowerValue.includes('decline') || lowerValue === 'no') {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Extract rejection reason from row
   */
  extractRejectionReason(row) {
    const reasonFields = ['rejection_reason', 'denial_reason', 'reason', 'comments', 'notes'];

    for (const field of reasonFields) {
      const value = this.getFieldValue(row, field);
      if (value && typeof value === 'string' && value.trim() !== '') {
        return value.trim();
      }
    }

    return null;
  }

  /**
   * Categorize rejection reason
   */
  categorizeRejectionReason(reason) {
    const lowerReason = reason.toLowerCase();

    for (const [category, keywords] of Object.entries(this.rejectionReasonCategories)) {
      if (keywords.some(keyword => lowerReason.includes(keyword))) {
        return category;
      }
    }

    return 'other';
  }

  /**
   * Extract provider from row
   */
  extractProvider(row) {
    const providerFields = ['provider', 'provider_name', 'hospital', 'clinic', 'facility'];

    for (const field of providerFields) {
      const value = this.getFieldValue(row, field);
      if (value && typeof value === 'string' && value.trim() !== '') {
        return value.trim();
      }
    }

    return null;
  }

  /**
   * Extract specialty from row
   */
  extractSpecialty(row) {
    const specialtyFields = ['specialty', 'medical_specialty', 'department', 'service_type'];

    for (const field of specialtyFields) {
      const value = this.getFieldValue(row, field);
      if (value && typeof value === 'string' && value.trim() !== '') {
        return value.trim();
      }
    }

    return null;
  }

  /**
   * Extract date from row
   */
  extractDate(row) {
    const dateFields = ['date', 'claim_date', 'service_date', 'created_date', 'processed_date'];

    for (const field of dateFields) {
      const value = this.getFieldValue(row, field);
      if (value) {
        const date = moment(value);
        if (date.isValid()) {
          return date.toDate();
        }
      }
    }

    return null;
  }

  /**
   * Extract amount from row
   */
  extractAmount(row) {
    const amountFields = ['amount', 'claim_amount', 'total_amount', 'paid_amount', 'cost'];

    for (const field of amountFields) {
      const value = this.getFieldValue(row, field);
      if (value !== null && value !== undefined) {
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          return numValue;
        }
      }
    }

    return null;
  }

  /**
   * Get field value with fuzzy matching
   */
  getFieldValue(row, fieldName) {
    // Direct match
    if (row[fieldName] !== undefined) {
      return row[fieldName];
    }

    // Case-insensitive match
    const keys = Object.keys(row);
    const matchingKey = keys.find(key =>
      key.toLowerCase() === fieldName.toLowerCase() ||
      key.toLowerCase().includes(fieldName.toLowerCase()) ||
      fieldName.toLowerCase().includes(key.toLowerCase())
    );

    return matchingKey ? row[matchingKey] : null;
  }

  /**
   * Get amount range category
   */
  getAmountRange(amount) {
    if (amount < 100) return '0-100';
    if (amount < 500) return '100-500';
    if (amount < 1000) return '500-1K';
    if (amount < 5000) return '1K-5K';
    if (amount < 10000) return '5K-10K';
    if (amount < 50000) return '10K-50K';
    return '50K+';
  }

  /**
   * Get period key for timeframe
   */
  getPeriodKey(date, timeframe) {
    const momentDate = moment(date);

    switch (timeframe) {
      case 'daily':
        return momentDate.format('YYYY-MM-DD');
      case 'weekly':
        return momentDate.format('YYYY-[W]WW');
      case 'monthly':
        return momentDate.format('YYYY-MM');
      case 'quarterly':
        return momentDate.format('YYYY-[Q]Q');
      case 'yearly':
        return momentDate.format('YYYY');
      default:
        return momentDate.format('YYYY-MM');
    }
  }

  /**
   * Sort object by values in descending order
   */
  sortByValue(obj) {
    return Object.fromEntries(
      Object.entries(obj).sort(([,a], [,b]) => b - a)
    );
  }

  /**
   * Check if field is date-related
   */
  isDateField(fieldName) {
    const dateKeywords = ['date', 'time', 'created', 'updated', 'processed'];
    return dateKeywords.some(keyword =>
      fieldName.toLowerCase().includes(keyword)
    );
  }

  /**
   * Check if field is amount-related
   */
  isAmountField(fieldName) {
    const amountKeywords = ['amount', 'cost', 'price', 'total', 'paid', 'balance'];
    return amountKeywords.some(keyword =>
      fieldName.toLowerCase().includes(keyword)
    );
  }

  /**
   * Check if field is rejection-related
   */
  isRejectionField(fieldName) {
    const rejectionKeywords = ['status', 'rejection', 'denial', 'approved', 'declined'];
    return rejectionKeywords.some(keyword =>
      fieldName.toLowerCase().includes(keyword)
    );
  }

  /**
   * Check if field is medical-related
   */
  isMedicalField(fieldName) {
    const medicalKeywords = ['specialty', 'procedure', 'diagnosis', 'treatment', 'medical'];
    return medicalKeywords.some(keyword =>
      fieldName.toLowerCase().includes(keyword)
    );
  }

  /**
   * Generate rejection insights
   */
  generateRejectionInsights(analysis) {
    const insights = [];

    const { rejectionRate, rejectedClaims } = analysis.summary;

    // Rejection rate insights
    if (rejectionRate > 20) {
      insights.push({
        type: 'warning',
        category: 'rejection_rate',
        title: 'High Rejection Rate',
        description: `Rejection rate of ${rejectionRate.toFixed(1)}% is above industry average`,
        impact: 'high',
        recommendation: 'Review top rejection reasons and implement preventive measures'
      });
    }

    // Top rejection reason insights
    const topReason = Object.keys(analysis.patterns.byReason)[0];
    if (topReason) {
      const reasonCount = analysis.patterns.byReason[topReason];
      const reasonPercentage = (reasonCount / rejectedClaims) * 100;

      insights.push({
        type: 'info',
        category: 'top_reason',
        title: 'Primary Rejection Cause',
        description: `"${topReason}" accounts for ${reasonPercentage.toFixed(1)}% of all rejections`,
        impact: 'medium',
        recommendation: 'Focus improvement efforts on addressing this specific issue'
      });
    }

    return insights;
  }

  /**
   * Generate trend insights
   */
  generateTrendInsights(analysis) {
    const insights = [];

    // Add trend-specific insights based on patterns
    // This would analyze growth rates, seasonality, etc.

    return insights;
  }

  /**
   * Generate pattern insights
   */
  generatePatternInsights(analysis) {
    const insights = [];

    // Add pattern-specific insights

    return insights;
  }

  /**
   * Generate comparison insights
   */
  generateComparisonInsights(analysis) {
    const insights = [];

    // Add comparison-specific insights

    return insights;
  }

  /**
   * Perform detailed rejection analysis
   */
  async performDetailedRejectionAnalysis(processedData) {
    // Implement detailed analysis logic
    return {
      detailedPatterns: {},
      rootCauseAnalysis: {},
      impactAssessment: {}
    };
  }

  /**
   * Analyze trend patterns
   */
  analyzeTrendPatterns(analysis) {
    // Implement trend pattern analysis
  }

  /**
   * Extract dataset patterns
   */
  async extractDatasetPatterns(dataset, analysis, index) {
    // Implement pattern extraction
  }

  /**
   * Find cross-dataset patterns
   */
  findCrossDatasetPatterns(analysis, datasetCount) {
    // Implement cross-dataset pattern finding
  }

  /**
   * Analyze sheet quality
   */
  async analyzeSheetQuality(sheet) {
    // Implement sheet quality analysis
    return {
      sheetName: sheet.name,
      completeness: 0,
      consistency: 0,
      validity: 0,
      score: 0,
      issues: []
    };
  }

  /**
   * Calculate overall quality
   */
  calculateOverallQuality(analysis) {
    // Implement overall quality calculation
  }

  /**
   * Generate quality recommendations
   */
  generateQualityRecommendations(analysis) {
    // Implement quality recommendations
    return [];
  }

  /**
   * Generate dataset summary
   */
  async generateDatasetSummary(data) {
    // Implement dataset summary generation
    return {};
  }

  /**
   * Compare metric between datasets
   */
  compareMetric(datasets, metric) {
    // Implement metric comparison
    return {};
  }

  /**
   * Rank datasets by metric
   */
  rankDatasets(datasets, metric) {
    // Implement dataset ranking
    return [];
  }
}

module.exports = new AnalysisEngine();
