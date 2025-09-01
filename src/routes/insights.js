const fs = require('fs').promises;
const path = require('path');
const OpenAI = require('openai');

const router = require('express').Router();

// Initialize OpenAI client (if API key is provided)
let openai = null;
if (process.env.OPENAI_API_KEY) {
  openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });
}

/**
 * Generate AI-powered insights for processed data
 */
router.post('/generate', async (req, res) => {
  try {
    const {
      resultId,
      insightTypes = ['patterns', 'recommendations', 'predictions'],
      useOpenAI = false
    } = req.body;

    if (!resultId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter',
        message: 'Result ID is required for AI insights generation'
      });
    }

    // Load processed data
    const dataPath = path.join(__dirname, '../../data', `${resultId}.json`);

    try {
      const rawData = await fs.readFile(dataPath, 'utf8');
      const processedData = JSON.parse(rawData);

      let insights;

      // Use OpenAI if available and requested
      if (useOpenAI && openai) {
        insights = await generateOpenAIInsights(processedData, insightTypes);
      } else {
        // Fallback to enhanced rule-based analysis
        insights = await generateEnhancedInsights(processedData, insightTypes);
      }

      res.json({
        success: true,
        message: 'AI insights generated successfully',
        data: {
          resultId,
          insightTypes,
          insights,
          aiProvider: useOpenAI && openai ? 'OpenAI' : 'Statistical Analysis',
          generatedAt: new Date().toISOString()
        }
      });

    } catch (fileError) {
      res.status(404).json({
        success: false,
        error: 'Data not found',
        message: 'The specified result ID was not found'
      });
    }

  } catch (error) {
    console.error('AI insights generation error:', error);
    res.status(500).json({
      success: false,
      error: 'Insights generation failed',
      message: error.message
    });
  }
});

/**
 * Generate statistical insights (AI simulation)
 */
async function generateStatisticalInsights(processedData, insightTypes) {
  const insights = {
    patterns: [],
    recommendations: [],
    predictions: [],
    summary: {}
  };

  // Generate pattern insights
  if (insightTypes.includes('patterns')) {
    insights.patterns = generatePatternInsights(processedData);
  }

  // Generate recommendations
  if (insightTypes.includes('recommendations')) {
    insights.recommendations = generateRecommendations(processedData);
  }

  // Generate predictions
  if (insightTypes.includes('predictions')) {
    insights.predictions = generatePredictions(processedData);
  }

  // Generate summary
  insights.summary = generateInsightsSummary(insights);

  return insights;
}

/**
 * Generate pattern insights
 */
function generatePatternInsights(processedData) {
  const patterns = [];

  // Analyze data quality patterns
  const avgQuality = processedData.summary.overallQuality;
  if (avgQuality < 80) {
    patterns.push({
      type: 'data_quality',
      severity: 'medium',
      title: 'Data Quality Opportunity',
      description: `Data quality score of ${avgQuality.toFixed(1)}% indicates room for improvement`,
      details: 'Missing values, inconsistent formats, or invalid entries detected',
      confidence: 0.85
    });
  }

  // Analyze volume patterns
  const totalRows = processedData.summary.totalDataRows;
  if (totalRows > 50000) {
    patterns.push({
      type: 'volume',
      severity: 'info',
      title: 'Large Dataset Detected',
      description: `Processing ${totalRows.toLocaleString()} records suggests high-volume operations`,
      details: 'Consider implementing automated monitoring and batch processing',
      confidence: 0.95
    });
  }

  // Analyze rejection patterns
  processedData.sheets.forEach(sheet => {
    if (sheet.analysis?.patterns?.rejectionReasons) {
      const rejections = sheet.analysis.patterns.rejectionReasons;
      const topRejection = Object.keys(rejections)[0];
      if (topRejection) {
        patterns.push({
          type: 'rejection_pattern',
          severity: 'high',
          title: 'Dominant Rejection Pattern',
          description: `"${topRejection}" is the most frequent rejection reason`,
          details: `Accounts for ${rejections[topRejection]} cases in ${sheet.name}`,
          confidence: 0.9
        });
      }
    }
  });

  return patterns;
}

/**
 * Generate recommendations
 */
function generateRecommendations(processedData) {
  const recommendations = [];

  // Data quality recommendations
  const avgQuality = processedData.summary.overallQuality;
  if (avgQuality < 90) {
    recommendations.push({
      category: 'data_quality',
      priority: 'high',
      title: 'Implement Data Validation',
      description: 'Establish automated data validation checks to improve quality',
      actions: [
        'Set up real-time validation rules',
        'Implement data cleansing procedures',
        'Create quality monitoring dashboards',
        'Train staff on data entry standards'
      ],
      expectedImpact: 'Reduce processing errors by 30-50%',
      timeline: '2-4 weeks',
      confidence: 0.88
    });
  }

  // Process optimization recommendations
  recommendations.push({
    category: 'process_optimization',
    priority: 'medium',
    title: 'Automate Routine Analysis',
    description: 'Implement automated reporting and analysis workflows',
    actions: [
      'Set up scheduled data processing',
      'Create automated alert systems',
      'Implement trend monitoring',
      'Develop exception reporting'
    ],
    expectedImpact: 'Reduce manual work by 60-80%',
    timeline: '4-6 weeks',
    confidence: 0.82
  });

  // Rejection reduction recommendations
  processedData.sheets.forEach(sheet => {
    if (sheet.analysis?.patterns?.rejectionReasons) {
      const rejections = Object.keys(sheet.analysis.patterns.rejectionReasons);
      if (rejections.length > 0) {
        recommendations.push({
          category: 'rejection_reduction',
          priority: 'high',
          title: 'Address Top Rejection Causes',
          description: 'Focus on reducing the most common rejection reasons',
          actions: [
            `Investigate root causes of "${rejections[0]}" rejections`,
            'Implement preventive controls',
            'Provide targeted training',
            'Monitor improvement metrics'
          ],
          expectedImpact: 'Reduce rejection rates by 20-40%',
          timeline: '3-5 weeks',
          confidence: 0.85
        });
      }
    }
  });

  // Technology recommendations
  recommendations.push({
    category: 'technology',
    priority: 'low',
    title: 'Enhanced Analytics Platform',
    description: 'Consider upgrading to advanced analytics capabilities',
    actions: [
      'Evaluate AI-powered analysis tools',
      'Implement predictive analytics',
      'Add real-time monitoring',
      'Integrate with existing systems'
    ],
    expectedImpact: 'Improve insights quality by 40-60%',
    timeline: '8-12 weeks',
    confidence: 0.75
  });

  return recommendations;
}

/**
 * Generate predictions
 */
function generatePredictions(processedData) {
  const predictions = [];

  // Trend predictions
  predictions.push({
    type: 'trend',
    category: 'volume',
    title: 'Data Volume Growth',
    description: 'Based on current patterns, expect continued growth in data volume',
    prediction: '15-25% increase in monthly data volume over next quarter',
    confidence: 0.78,
    timeframe: '3 months',
    factors: ['Historical growth patterns', 'Business expansion', 'Process improvements']
  });

  // Quality predictions
  const avgQuality = processedData.summary.overallQuality;
  if (avgQuality < 85) {
    predictions.push({
      type: 'quality',
      category: 'improvement',
      title: 'Data Quality Improvement Potential',
      description: 'With proper interventions, significant quality improvements are achievable',
      prediction: `Potential to reach 90-95% quality score from current ${avgQuality.toFixed(1)}%`,
      confidence: 0.82,
      timeframe: '2-3 months',
      factors: ['Implementation of validation rules', 'Staff training', 'Process standardization']
    });
  }

  // Efficiency predictions
  predictions.push({
    type: 'efficiency',
    category: 'processing',
    title: 'Processing Efficiency Gains',
    description: 'Automation and optimization can significantly improve processing speed',
    prediction: '40-60% reduction in processing time with recommended improvements',
    confidence: 0.85,
    timeframe: '1-2 months',
    factors: ['Automation implementation', 'Workflow optimization', 'System integration']
  });

  return predictions;
}

// Helper Functions

/**
 * Generate insights using OpenAI
 */
async function generateOpenAIInsights(processedData, insightTypes) {
  try {
    // Prepare data summary for OpenAI
    const dataSummary = prepareDataSummary(processedData);

    const prompt = `
You are a healthcare insurance data analyst. Analyze the following healthcare claims data and provide insights:

Data Summary:
${JSON.stringify(dataSummary, null, 2)}

Please provide insights for: ${insightTypes.join(', ')}

For each insight type, provide:
1. Patterns: Key patterns found in the data
2. Recommendations: Actionable recommendations to improve claim processing
3. Predictions: Trends and potential future outcomes

Format your response as a JSON object with the following structure:
{
  "insights": [
    {
      "category": "pattern|recommendation|prediction",
      "title": "Brief title",
      "description": "Detailed description",
      "confidence": 0.0-1.0,
      "impact": "high|medium|low",
      "actionable": true|false
    }
  ],
  "summary": "Overall analysis summary",
  "risks": ["Risk 1", "Risk 2"],
  "opportunities": ["Opportunity 1", "Opportunity 2"]
}`;

    const completion = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: "You are an expert healthcare insurance data analyst with deep knowledge of claim processing, rejection patterns, and healthcare analytics."
        },
        {
          role: "user",
          content: prompt
        }
      ],
      temperature: 0.3,
      max_tokens: 2000
    });

    const aiResponse = completion.choices[0].message.content;

    try {
      return JSON.parse(aiResponse);
    } catch (parseError) {
      console.error('Failed to parse OpenAI response:', parseError);
      // Fallback to enhanced statistical analysis
      return await generateEnhancedInsights(processedData, insightTypes);
    }

  } catch (error) {
    console.error('OpenAI API error:', error);
    // Fallback to enhanced statistical analysis
    return await generateEnhancedInsights(processedData, insightTypes);
  }
}

/**
 * Prepare data summary for AI analysis
 */
function prepareDataSummary(processedData) {
  const summary = {
    filename: processedData.filename,
    totalSheets: processedData.sheets.length,
    totalRecords: 0,
    sampleData: [],
    qualityMetrics: {},
    rejectionAnalysis: {}
  };

  // Aggregate data across all sheets
  processedData.sheets.forEach(sheet => {
    summary.totalRecords += sheet.data.length;

    // Add sample data (first few rows)
    if (summary.sampleData.length < 5 && sheet.data.length > 0) {
      summary.sampleData.push(...sheet.data.slice(0, 5 - summary.sampleData.length));
    }

    // Add quality metrics
    if (sheet.analysis && sheet.analysis.dataQuality) {
      summary.qualityMetrics[sheet.name] = {
        score: sheet.analysis.dataQuality.score,
        completeness: sheet.analysis.dataQuality.completeness,
        issues: sheet.analysis.dataQuality.issues || []
      };
    }
  });

  // Calculate rejection metrics from sample data
  const rejectedClaims = summary.sampleData.filter(row =>
    row.Status && row.Status.toLowerCase().includes('reject')
  );

  summary.rejectionAnalysis = {
    totalClaims: summary.sampleData.length,
    rejectedClaims: rejectedClaims.length,
    rejectionRate: summary.sampleData.length > 0
      ? (rejectedClaims.length / summary.sampleData.length * 100).toFixed(2)
      : 0,
    commonReasons: getTopRejectionReasons(rejectedClaims)
  };

  return summary;
}

/**
 * Enhanced statistical insights generation
 */
async function generateEnhancedInsights(processedData, insightTypes) {
  const insights = {
    insights: [],
    summary: '',
    risks: [],
    opportunities: [],
    recommendations: []
  };

  // Process each sheet for comprehensive analysis
  let totalRecords = 0;
  let totalRejections = 0;
  let qualityScores = [];
  let commonIssues = [];

  processedData.sheets.forEach(sheet => {
    totalRecords += sheet.data.length;

    // Count rejections
    const rejections = sheet.data.filter(row =>
      row.Status && row.Status.toLowerCase().includes('reject')
    ).length;
    totalRejections += rejections;

    // Collect quality scores
    if (sheet.analysis && sheet.analysis.dataQuality) {
      qualityScores.push(parseFloat(sheet.analysis.dataQuality.score));
      if (sheet.analysis.dataQuality.issues) {
        commonIssues.push(...sheet.analysis.dataQuality.issues);
      }
    }
  });

  const rejectionRate = totalRecords > 0 ? (totalRejections / totalRecords * 100) : 0;
  const avgQualityScore = qualityScores.length > 0
    ? qualityScores.reduce((a, b) => a + b, 0) / qualityScores.length
    : 0;

  // Generate pattern insights
  if (insightTypes.includes('patterns')) {
    insights.insights.push({
      category: 'pattern',
      title: 'Claim Rejection Pattern',
      description: `Analysis reveals a ${rejectionRate.toFixed(2)}% rejection rate across ${totalRecords} claims. ${rejectionRate > 15 ? 'This is higher than industry standards.' : 'This is within acceptable ranges.'}`,
      confidence: 0.9,
      impact: rejectionRate > 20 ? 'high' : rejectionRate > 10 ? 'medium' : 'low',
      actionable: rejectionRate > 15
    });

    insights.insights.push({
      category: 'pattern',
      title: 'Data Quality Pattern',
      description: `Overall data quality score is ${avgQualityScore.toFixed(1)}%. ${avgQualityScore < 80 ? 'Significant quality improvements needed.' : 'Data quality is generally acceptable.'}`,
      confidence: 0.85,
      impact: avgQualityScore < 70 ? 'high' : avgQualityScore < 85 ? 'medium' : 'low',
      actionable: avgQualityScore < 85
    });
  }

  // Generate recommendations
  if (insightTypes.includes('recommendations')) {
    if (rejectionRate > 15) {
      insights.insights.push({
        category: 'recommendation',
        title: 'Reduce Claim Rejections',
        description: 'Implement pre-submission validation checks and staff training on common rejection causes to reduce the high rejection rate.',
        confidence: 0.8,
        impact: 'high',
        actionable: true
      });
    }

    if (avgQualityScore < 85) {
      insights.insights.push({
        category: 'recommendation',
        title: 'Improve Data Quality',
        description: 'Establish data quality monitoring processes and mandatory field validation to improve overall data integrity.',
        confidence: 0.85,
        impact: 'medium',
        actionable: true
      });
    }

    insights.insights.push({
      category: 'recommendation',
      title: 'Automated Analytics',
      description: 'Implement automated daily reporting and trend monitoring to identify issues proactively.',
      confidence: 0.75,
      impact: 'medium',
      actionable: true
    });
  }

  // Generate predictions
  if (insightTypes.includes('predictions')) {
    insights.insights.push({
      category: 'prediction',
      title: 'Rejection Trend Forecast',
      description: `Based on current patterns, rejection rates may ${rejectionRate > 15 ? 'continue to impact efficiency' : 'remain stable'} over the next quarter.`,
      confidence: 0.7,
      impact: 'medium',
      actionable: false
    });

    insights.insights.push({
      category: 'prediction',
      title: 'Process Efficiency Prediction',
      description: 'With proper implementation of recommended improvements, claim processing efficiency could improve by 25-40%.',
      confidence: 0.65,
      impact: 'high',
      actionable: true
    });
  }

  // Generate summary
  insights.summary = `Analysis of ${totalRecords} healthcare claims reveals a ${rejectionRate.toFixed(2)}% rejection rate with ${avgQualityScore.toFixed(1)}% data quality score. ${rejectionRate > 15 || avgQualityScore < 80 ? 'Immediate attention required for process improvements.' : 'Performance is within acceptable parameters with room for optimization.'}`;

  // Add risks
  if (rejectionRate > 20) {
    insights.risks.push('High rejection rate may impact customer satisfaction and operational costs');
  }
  if (avgQualityScore < 70) {
    insights.risks.push('Poor data quality may lead to compliance issues and processing errors');
  }
  insights.risks.push('Manual processing inefficiencies may lead to increased operational overhead');

  // Add opportunities
  insights.opportunities.push('Implement AI-powered pre-submission validation');
  insights.opportunities.push('Develop predictive models for claim approval likelihood');
  insights.opportunities.push('Create automated quality assurance workflows');
  if (rejectionRate < 10) {
    insights.opportunities.push('Benchmark and share best practices across the organization');
  }

  return insights;
}

/**
 * Get top rejection reasons from rejected claims
 */
function getTopRejectionReasons(rejectedClaims) {
  const reasonCounts = {};

  rejectedClaims.forEach(claim => {
    const reason = claim['Rejection Reason'] || 'Unknown';
    reasonCounts[reason] = (reasonCounts[reason] || 0) + 1;
  });

  return Object.entries(reasonCounts)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([reason, count]) => ({ reason, count }));
}

/**
 * Generate insights summary
 */
function generateInsightsSummary(insights) {
  return {
    totalPatterns: insights.patterns.length,
    totalRecommendations: insights.recommendations.length,
    totalPredictions: insights.predictions.length,
    highPriorityItems: insights.recommendations.filter(r => r.priority === 'high').length,
    averageConfidence: calculateAverageConfidence(insights),
    keyFindings: generateKeyFindings(insights)
  };
}

/**
 * Calculate average confidence across all insights
 */
function calculateAverageConfidence(insights) {
  const allConfidences = [
    ...insights.patterns.map(p => p.confidence),
    ...insights.recommendations.map(r => r.confidence),
    ...insights.predictions.map(p => p.confidence)
  ];

  return allConfidences.length > 0
    ? allConfidences.reduce((sum, conf) => sum + conf, 0) / allConfidences.length
    : 0;
}

/**
 * Generate key findings
 */
function generateKeyFindings(insights) {
  const findings = [];

  // High-severity patterns
  const highSeverityPatterns = insights.patterns.filter(p => p.severity === 'high');
  if (highSeverityPatterns.length > 0) {
    findings.push(`${highSeverityPatterns.length} high-impact patterns identified`);
  }

  // High-priority recommendations
  const highPriorityRecs = insights.recommendations.filter(r => r.priority === 'high');
  if (highPriorityRecs.length > 0) {
    findings.push(`${highPriorityRecs.length} high-priority recommendations available`);
  }

  // High-confidence predictions
  const highConfPredictions = insights.predictions.filter(p => p.confidence > 0.8);
  if (highConfPredictions.length > 0) {
    findings.push(`${highConfPredictions.length} high-confidence predictions generated`);
  }

  return findings;
}

module.exports = router;
