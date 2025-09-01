"""
Enhanced AI Insights Generator with Advanced Analytics
Production-ready AI analysis engine for healthcare data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

@dataclass
class AIInsight:
    """Structured AI insight with confidence scoring"""
    type: str
    category: str
    title: str
    description: str
    impact: str
    confidence: float
    recommendation: str
    priority: str
    data_points: List[Dict[str, Any]]
    
class EnhancedInsightsGenerator:
    """Advanced AI-powered insights generator for healthcare analytics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        
    def generate_comprehensive_insights(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive AI insights from analysis data"""
        try:
            insights = {
                'financial_insights': self._analyze_financial_patterns(analysis_data),
                'operational_insights': self._analyze_operational_efficiency(analysis_data),
                'risk_insights': self._analyze_risk_patterns(analysis_data),
                'predictive_insights': self._generate_predictive_insights(analysis_data),
                'anomaly_insights': self._detect_anomalies(analysis_data),
                'trend_insights': self._analyze_trends(analysis_data),
                'summary': self._generate_executive_summary(analysis_data)
            }
            
            return {
                'success': True,
                'insights': insights,
                'generated_at': datetime.now().isoformat(),
                'confidence_score': self._calculate_overall_confidence(insights)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_financial_patterns(self, data: Dict[str, Any]) -> List[AIInsight]:
        """Analyze financial patterns and generate insights"""
        insights = []
        
        try:
            # Extract financial metrics
            total_claims = data.get('summary', {}).get('totalClaims', 0)
            total_amount = data.get('summary', {}).get('totalAmount', 0)
            rejection_rate = data.get('summary', {}).get('rejectionRate', 0)
            
            if total_claims > 0:
                avg_claim_value = total_amount / total_claims
                
                # High-value claims analysis
                if avg_claim_value > 5000:
                    insights.append(AIInsight(
                        type='financial',
                        category='cost_analysis',
                        title='High Average Claim Value Detected',
                        description=f'Average claim value of ${avg_claim_value:,.2f} is significantly above industry average',
                        impact='High financial exposure requiring enhanced review processes',
                        confidence=0.85,
                        recommendation='Implement tiered approval process for claims above $3,000',
                        priority='high',
                        data_points=[{'metric': 'avg_claim_value', 'value': avg_claim_value}]
                    ))
                
                # Rejection cost analysis
                rejection_cost = total_amount * (rejection_rate / 100)
                if rejection_cost > 50000:
                    insights.append(AIInsight(
                        type='financial',
                        category='loss_prevention',
                        title='Significant Financial Impact from Rejections',
                        description=f'Estimated ${rejection_cost:,.2f} in rejected claims requiring attention',
                        impact='Direct revenue loss and operational inefficiency',
                        confidence=0.92,
                        recommendation='Focus on top rejection reasons to recover potential revenue',
                        priority='critical',
                        data_points=[{'metric': 'rejection_cost', 'value': rejection_cost}]
                    ))
            
        except Exception as e:
            self.logger.error(f"Error in financial analysis: {str(e)}")
        
        return insights
    
    def _analyze_operational_efficiency(self, data: Dict[str, Any]) -> List[AIInsight]:
        """Analyze operational efficiency patterns"""
        insights = []
        
        try:
            processing_time = data.get('summary', {}).get('avgProcessingTime', 0)
            data_quality = data.get('summary', {}).get('overallQuality', 0)
            
            # Processing efficiency
            if processing_time > 24:  # hours
                insights.append(AIInsight(
                    type='operational',
                    category='efficiency',
                    title='Extended Processing Times Detected',
                    description=f'Average processing time of {processing_time:.1f} hours exceeds optimal range',
                    impact='Delayed claim resolution affecting customer satisfaction',
                    confidence=0.78,
                    recommendation='Implement automated pre-screening and parallel processing workflows',
                    priority='medium',
                    data_points=[{'metric': 'processing_time', 'value': processing_time}]
                ))
            
            # Data quality insights
            if data_quality < 80:
                insights.append(AIInsight(
                    type='operational',
                    category='data_quality',
                    title='Data Quality Issues Impacting Operations',
                    description=f'Data quality score of {data_quality:.1f}% indicates systematic issues',
                    impact='Increased manual review requirements and processing delays',
                    confidence=0.88,
                    recommendation='Implement data validation at point of entry and provider training',
                    priority='high',
                    data_points=[{'metric': 'data_quality', 'value': data_quality}]
                ))
                
        except Exception as e:
            self.logger.error(f"Error in operational analysis: {str(e)}")
        
        return insights
    
    def _analyze_risk_patterns(self, data: Dict[str, Any]) -> List[AIInsight]:
        """Analyze risk patterns and compliance issues"""
        insights = []
        
        try:
            sheets = data.get('sheets', [])
            
            for sheet in sheets:
                patterns = sheet.get('analysis', {}).get('patterns', {})
                
                # Fraud risk indicators
                duplicate_claims = patterns.get('duplicateClaims', 0)
                if duplicate_claims > 5:
                    insights.append(AIInsight(
                        type='risk',
                        category='fraud_detection',
                        title='Potential Duplicate Claims Detected',
                        description=f'Found {duplicate_claims} potential duplicate claims requiring investigation',
                        impact='Possible fraudulent activity or system errors',
                        confidence=0.75,
                        recommendation='Implement automated duplicate detection and manual review process',
                        priority='high',
                        data_points=[{'metric': 'duplicate_claims', 'value': duplicate_claims}]
                    ))
                
                # Compliance risk
                missing_codes = patterns.get('missingCodes', 0)
                if missing_codes > 10:
                    insights.append(AIInsight(
                        type='risk',
                        category='compliance',
                        title='Coding Compliance Issues Identified',
                        description=f'{missing_codes} claims with missing or invalid codes',
                        impact='Regulatory compliance risk and audit findings',
                        confidence=0.82,
                        recommendation='Enhance coding validation and provider education programs',
                        priority='medium',
                        data_points=[{'metric': 'missing_codes', 'value': missing_codes}]
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error in risk analysis: {str(e)}")
        
        return insights
    
    def _generate_predictive_insights(self, data: Dict[str, Any]) -> List[AIInsight]:
        """Generate predictive insights using ML models"""
        insights = []
        
        try:
            # Trend-based predictions
            monthly_trends = data.get('trends', {}).get('monthly', {})
            if monthly_trends:
                trend_data = list(monthly_trends.values())
                if len(trend_data) >= 3:
                    # Simple trend analysis
                    recent_trend = np.mean(trend_data[-3:]) - np.mean(trend_data[:-3])
                    
                    if recent_trend > 0.1:
                        insights.append(AIInsight(
                            type='predictive',
                            category='volume_forecast',
                            title='Increasing Claim Volume Trend Detected',
                            description='Claims volume showing upward trend requiring capacity planning',
                            impact='Potential resource constraints and processing delays',
                            confidence=0.72,
                            recommendation='Scale processing capacity and consider automation investments',
                            priority='medium',
                            data_points=[{'metric': 'trend_slope', 'value': recent_trend}]
                        ))
                        
        except Exception as e:
            self.logger.error(f"Error in predictive analysis: {str(e)}")
        
        return insights
    
    def _detect_anomalies(self, data: Dict[str, Any]) -> List[AIInsight]:
        """Detect anomalies in the data using ML"""
        insights = []
        
        try:
            sheets = data.get('sheets', [])
            
            for sheet in sheets:
                sheet_data = sheet.get('data', [])
                if len(sheet_data) > 10:
                    # Prepare numerical features for anomaly detection
                    numerical_features = []
                    for row in sheet_data:
                        features = []
                        for key, value in row.items():
                            if isinstance(value, (int, float)) and not np.isnan(value):
                                features.append(value)
                        if features:
                            numerical_features.append(features)
                    
                    if len(numerical_features) > 10:
                        # Pad features to same length
                        max_len = max(len(f) for f in numerical_features)
                        padded_features = [f + [0] * (max_len - len(f)) for f in numerical_features]
                        
                        # Detect anomalies
                        anomalies = self.anomaly_detector.fit_predict(padded_features)
                        anomaly_count = np.sum(anomalies == -1)
                        
                        if anomaly_count > 0:
                            insights.append(AIInsight(
                                type='anomaly',
                                category='data_quality',
                                title=f'Data Anomalies Detected in {sheet.get("name", "Sheet")}',
                                description=f'Found {anomaly_count} anomalous records requiring investigation',
                                impact='Potential data quality issues or exceptional cases',
                                confidence=0.68,
                                recommendation='Review flagged records for data entry errors or exceptional cases',
                                priority='low',
                                data_points=[{'metric': 'anomaly_count', 'value': anomaly_count}]
                            ))
                            
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {str(e)}")
        
        return insights
    
    def _analyze_trends(self, data: Dict[str, Any]) -> List[AIInsight]:
        """Analyze temporal trends in the data"""
        insights = []
        
        try:
            # Seasonal patterns
            monthly_data = data.get('trends', {}).get('monthly', {})
            if len(monthly_data) >= 12:
                values = list(monthly_data.values())
                
                # Detect seasonality
                q1_avg = np.mean(values[0:3])
                q4_avg = np.mean(values[9:12])
                
                if abs(q4_avg - q1_avg) / q1_avg > 0.2:
                    insights.append(AIInsight(
                        type='trend',
                        category='seasonality',
                        title='Seasonal Pattern Detected',
                        description=f'Significant seasonal variation: Q4 vs Q1 difference of {abs(q4_avg - q1_avg)/q1_avg*100:.1f}%',
                        impact='Resource planning and capacity management implications',
                        confidence=0.79,
                        recommendation='Adjust staffing and processing capacity based on seasonal patterns',
                        priority='medium',
                        data_points=[{'metric': 'seasonal_variation', 'value': abs(q4_avg - q1_avg)/q1_avg}]
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {str(e)}")
        
        return insights
    
    def _generate_executive_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of key insights"""
        try:
            summary = {
                'total_claims_processed': data.get('summary', {}).get('totalClaims', 0),
                'total_financial_value': data.get('summary', {}).get('totalAmount', 0),
                'overall_rejection_rate': data.get('summary', {}).get('rejectionRate', 0),
                'data_quality_score': data.get('summary', {}).get('overallQuality', 0),
                'key_recommendations': [
                    'Implement automated pre-screening for high-value claims',
                    'Focus on top 3 rejection reasons for immediate impact',
                    'Enhance data quality validation at point of entry',
                    'Consider seasonal staffing adjustments'
                ],
                'risk_level': self._assess_overall_risk(data),
                'improvement_potential': self._calculate_improvement_potential(data)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {str(e)}")
            return {}
    
    def _assess_overall_risk(self, data: Dict[str, Any]) -> str:
        """Assess overall risk level"""
        risk_score = 0
        
        rejection_rate = data.get('summary', {}).get('rejectionRate', 0)
        data_quality = data.get('summary', {}).get('overallQuality', 100)
        
        if rejection_rate > 15:
            risk_score += 2
        elif rejection_rate > 10:
            risk_score += 1
            
        if data_quality < 70:
            risk_score += 2
        elif data_quality < 85:
            risk_score += 1
        
        if risk_score >= 3:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_improvement_potential(self, data: Dict[str, Any]) -> float:
        """Calculate potential improvement percentage"""
        rejection_rate = data.get('summary', {}).get('rejectionRate', 0)
        data_quality = data.get('summary', {}).get('overallQuality', 100)
        
        # Estimate improvement potential based on industry benchmarks
        rejection_improvement = max(0, rejection_rate - 5) / rejection_rate if rejection_rate > 0 else 0
        quality_improvement = max(0, 95 - data_quality) / 100
        
        return min(50, (rejection_improvement + quality_improvement) * 100 / 2)
    
    def _calculate_overall_confidence(self, insights: Dict[str, Any]) -> float:
        """Calculate overall confidence score for insights"""
        all_insights = []
        for category in insights.values():
            if isinstance(category, list):
                all_insights.extend(category)
        
        if not all_insights:
            return 0.0
        
        confidences = [insight.confidence for insight in all_insights if hasattr(insight, 'confidence')]
        return np.mean(confidences) if confidences else 0.0