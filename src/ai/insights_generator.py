"""
AI-powered insights generator using OpenAI API
"""

import asyncio
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import pandas as pd
import numpy as np
from openai import AsyncOpenAI
import tiktoken

from ..utils.logger import setup_logger
from ..utils.config import get_settings
from ..processors.excel_processor import ExcelProcessor

logger = setup_logger(__name__)
settings = get_settings()


class InsightsGenerator:
    """AI-powered insights generator with healthcare domain expertise"""

    def __init__(self):
        self.excel_processor = ExcelProcessor()
        self.client = None
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Initialize OpenAI client if API key is available
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.info("OpenAI API key not provided, using statistical fallback")

        # Healthcare domain prompts
        self.domain_prompts = {
            'rejections': """
            You are a healthcare insurance claims expert. Analyze the provided claim rejection data and provide:
            1. Key insights about rejection patterns
            2. Root cause analysis
            3. Actionable recommendations to reduce rejections
            4. Financial impact assessment
            5. Process improvement suggestions

            Focus on practical, implementable solutions that healthcare organizations can use.
            """,

            'trends': """
            You are a healthcare data analyst. Analyze the provided trend data and provide:
            1. Key trend insights and patterns
            2. Seasonal or cyclical patterns
            3. Anomalies or outliers
            4. Predictive insights for future periods
            5. Strategic recommendations

            Consider healthcare industry cycles, regulatory changes, and market dynamics.
            """,

            'patterns': """
            You are a healthcare analytics expert. Analyze the provided pattern data and provide:
            1. Significant patterns discovered
            2. Clustering insights
            3. Anomaly explanations
            4. Provider behavior patterns
            5. Risk factors identification

            Focus on actionable insights that can improve healthcare operations and outcomes.
            """,

            'quality': """
            You are a healthcare data quality specialist. Analyze the provided quality metrics and provide:
            1. Data quality assessment
            2. Critical quality issues
            3. Impact on business operations
            4. Data governance recommendations
            5. Quality improvement strategies

            Emphasize the importance of data quality in healthcare decision-making.
            """,

            'comparison': """
            You are a healthcare business analyst. Analyze the provided comparison data and provide:
            1. Key differences between datasets
            2. Performance benchmarking insights
            3. Best practices identification
            4. Areas for improvement
            5. Standardization recommendations

            Focus on how organizations can learn from comparisons to improve performance.
            """
        }

    async def generate_insights(self, file_ids: List[str], analysis_type: str = "general",
                              custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate AI-powered insights for the given data"""
        try:
            logger.info(f"Generating insights for files: {file_ids}, type: {analysis_type}")

            # Prepare data summary for AI analysis
            data_summary = await self._prepare_data_summary(file_ids)

            if self.client and settings.openai_api_key:
                # Use OpenAI for insights
                result = await self._generate_openai_insights(data_summary, analysis_type, custom_prompt)
                result['source'] = 'openai'
            else:
                # Use statistical fallback
                result = await self._generate_statistical_insights(data_summary, analysis_type)
                result['source'] = 'statistical'

            logger.info(f"Generated insights from {result['source']} source")
            return result

        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            # Fallback to statistical insights
            data_summary = await self._prepare_data_summary(file_ids)
            result = await self._generate_statistical_insights(data_summary, analysis_type)
            result['source'] = 'statistical'
            return result

    async def _prepare_data_summary(self, file_ids: List[str]) -> Dict[str, Any]:
        """Prepare a comprehensive data summary for AI analysis"""
        summary = {
            'total_files': len(file_ids),
            'datasets': [],
            'combined_statistics': {},
            'key_metrics': {}
        }

        all_dataframes = []

        for file_id in file_ids:
            result = self.excel_processor.get_processing_result(file_id)
            if result:
                df = result.data
                all_dataframes.append(df)

                # Individual dataset summary
                dataset_summary = {
                    'file_id': file_id,
                    'records': len(df),
                    'columns': list(df.columns),
                    'data_types': df.dtypes.to_dict(),
                    'missing_data': df.isnull().sum().to_dict(),
                    'basic_stats': {}
                }

                # Add statistics for numeric columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                for col in numeric_columns:
                    if not df[col].empty:
                        dataset_summary['basic_stats'][col] = {
                            'mean': float(df[col].mean()),
                            'median': float(df[col].median()),
                            'std': float(df[col].std()),
                            'min': float(df[col].min()),
                            'max': float(df[col].max()),
                            'null_count': int(df[col].isnull().sum())
                        }

                # Add categorical summaries
                categorical_columns = df.select_dtypes(include=['object']).columns
                for col in categorical_columns:
                    if not df[col].empty:
                        value_counts = df[col].value_counts().head(5)
                        dataset_summary['basic_stats'][col] = {
                            'unique_count': int(df[col].nunique()),
                            'top_values': value_counts.to_dict(),
                            'null_count': int(df[col].isnull().sum())
                        }

                summary['datasets'].append(dataset_summary)

        # Combined analysis
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)

            summary['combined_statistics'] = {
                'total_records': len(combined_df),
                'total_columns': len(combined_df.columns),
                'overall_missing_percentage': float((combined_df.isnull().sum().sum() / (len(combined_df) * len(combined_df.columns))) * 100)
            }

            # Healthcare-specific metrics
            if 'status' in combined_df.columns:
                status_counts = combined_df['status'].value_counts()
                summary['key_metrics']['status_distribution'] = status_counts.to_dict()

                rejected_count = combined_df[combined_df['status'].str.lower().isin(['denied', 'rejected'])].shape[0]
                total_count = len(combined_df)
                summary['key_metrics']['rejection_rate'] = float((rejected_count / total_count) * 100) if total_count > 0 else 0.0

            if 'amount' in combined_df.columns:
                summary['key_metrics']['financial_metrics'] = {
                    'total_amount': float(combined_df['amount'].sum()),
                    'average_amount': float(combined_df['amount'].mean()),
                    'median_amount': float(combined_df['amount'].median())
                }

            if 'rejection_reason' in combined_df.columns:
                top_reasons = combined_df['rejection_reason'].value_counts().head(5)
                summary['key_metrics']['top_rejection_reasons'] = top_reasons.to_dict()

        return summary

    async def _generate_openai_insights(self, data_summary: Dict[str, Any],
                                      analysis_type: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate insights using OpenAI API"""
        try:
            # Prepare the prompt
            system_prompt = custom_prompt or self.domain_prompts.get(analysis_type, self.domain_prompts['trends'])

            # Prepare data context
            data_context = self._format_data_for_ai(data_summary)

            # Check token limit
            total_tokens = len(self.encoding.encode(system_prompt + data_context))
            if total_tokens > 3000:  # Leave room for response
                data_context = self._truncate_data_context(data_context, 2500)

            # Create the conversation
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please analyze this healthcare insurance data and provide detailed insights:\n\n{data_context}"}
            ]

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
                temperature=0.3  # Lower temperature for more consistent analysis
            )

            # Parse the response
            content = response.choices[0].message.content
            insights, recommendations = self._parse_ai_response(content)

            # Calculate confidence based on response quality
            confidence_score = self._calculate_ai_confidence(content, data_summary)

            return {
                'insights': insights,
                'recommendations': recommendations,
                'confidence_score': confidence_score,
                'raw_response': content
            }

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise

    async def _generate_statistical_insights(self, data_summary: Dict[str, Any],
                                           analysis_type: str) -> Dict[str, Any]:
        """Generate insights using statistical analysis as fallback"""
        insights = []
        recommendations = []

        try:
            # Analyze based on available data
            if data_summary.get('key_metrics'):
                metrics = data_summary['key_metrics']

                # Rejection rate analysis
                if 'rejection_rate' in metrics:
                    rejection_rate = metrics['rejection_rate']
                    if rejection_rate > 15:
                        insights.append(f"High rejection rate detected: {rejection_rate:.1f}% - This is above industry benchmarks")
                        recommendations.append("Implement rejection reduction strategies and provider training")
                    elif rejection_rate < 5:
                        insights.append(f"Excellent rejection rate: {rejection_rate:.1f}% - Well below industry average")
                        recommendations.append("Document and share best practices that maintain low rejection rates")
                    else:
                        insights.append(f"Moderate rejection rate: {rejection_rate:.1f}% - Within acceptable range")

                # Financial analysis
                if 'financial_metrics' in metrics:
                    financial = metrics['financial_metrics']
                    avg_amount = financial.get('average_amount', 0)
                    median_amount = financial.get('median_amount', 0)

                    if avg_amount > median_amount * 2:
                        insights.append("Significant variation in claim amounts detected - presence of high-value outliers")
                        recommendations.append("Review high-value claims for accuracy and potential fraud")

                    insights.append(f"Average claim amount: ${avg_amount:.2f}")

                # Rejection reasons analysis
                if 'top_rejection_reasons' in metrics:
                    top_reasons = metrics['top_rejection_reasons']
                    if top_reasons:
                        top_reason = list(top_reasons.keys())[0]
                        top_count = list(top_reasons.values())[0]
                        insights.append(f"Primary rejection reason: '{top_reason}' accounts for {top_count} rejections")
                        recommendations.append(f"Focus improvement efforts on addressing '{top_reason}' rejections")

            # Data quality insights
            if data_summary.get('combined_statistics'):
                stats = data_summary['combined_statistics']
                missing_pct = stats.get('overall_missing_percentage', 0)

                if missing_pct > 20:
                    insights.append(f"High missing data percentage: {missing_pct:.1f}% - Data quality concerns")
                    recommendations.append("Implement data validation and completion processes")
                elif missing_pct > 10:
                    insights.append(f"Moderate missing data: {missing_pct:.1f}% - Monitor data collection processes")
                    recommendations.append("Review data entry procedures for improvement opportunities")
                else:
                    insights.append(f"Good data completeness: {missing_pct:.1f}% missing data")

            # Multi-file analysis
            if data_summary.get('total_files', 0) > 1:
                insights.append(f"Analysis covers {data_summary['total_files']} datasets for comprehensive comparison")
                recommendations.append("Ensure consistent data collection and formatting across all data sources")

            # Default insights if no specific patterns found
            if not insights:
                insights = [
                    "Statistical analysis completed successfully",
                    "Data structure and quality assessed",
                    "Ready for detailed analytical processing"
                ]

            if not recommendations:
                recommendations = [
                    "Continue monitoring key performance indicators",
                    "Implement regular data quality checks",
                    "Consider advanced analytics for deeper insights"
                ]

            # Calculate confidence based on data availability
            confidence_score = self._calculate_statistical_confidence(data_summary)

            return {
                'insights': insights,
                'recommendations': recommendations,
                'confidence_score': confidence_score
            }

        except Exception as e:
            logger.error(f"Error in statistical insights generation: {str(e)}")
            return {
                'insights': ["Error in generating statistical insights"],
                'recommendations': ["Review data format and try again"],
                'confidence_score': 0.1
            }

    def _format_data_for_ai(self, data_summary: Dict[str, Any]) -> str:
        """Format data summary for AI consumption"""
        formatted_parts = []

        # Overall summary
        formatted_parts.append(f"DATASET OVERVIEW:")
        formatted_parts.append(f"- Total files analyzed: {data_summary.get('total_files', 0)}")

        if data_summary.get('combined_statistics'):
            stats = data_summary['combined_statistics']
            formatted_parts.append(f"- Total records: {stats.get('total_records', 0)}")
            formatted_parts.append(f"- Missing data percentage: {stats.get('overall_missing_percentage', 0):.1f}%")

        # Key metrics
        if data_summary.get('key_metrics'):
            formatted_parts.append(f"\nKEY METRICS:")
            metrics = data_summary['key_metrics']

            if 'rejection_rate' in metrics:
                formatted_parts.append(f"- Rejection rate: {metrics['rejection_rate']:.1f}%")

            if 'financial_metrics' in metrics:
                fin = metrics['financial_metrics']
                formatted_parts.append(f"- Total claim amount: ${fin.get('total_amount', 0):,.2f}")
                formatted_parts.append(f"- Average claim amount: ${fin.get('average_amount', 0):,.2f}")

            if 'top_rejection_reasons' in metrics:
                formatted_parts.append(f"- Top rejection reasons: {list(metrics['top_rejection_reasons'].keys())[:3]}")

        # Individual datasets
        formatted_parts.append(f"\nDATASET DETAILS:")
        for i, dataset in enumerate(data_summary.get('datasets', [])[:3]):  # Limit to first 3 datasets
            formatted_parts.append(f"Dataset {i+1}:")
            formatted_parts.append(f"  - Records: {dataset.get('records', 0)}")
            formatted_parts.append(f"  - Columns: {len(dataset.get('columns', []))}")

            # Add key statistics
            if dataset.get('basic_stats'):
                stats = dataset['basic_stats']
                for col, stat in list(stats.items())[:3]:  # Top 3 columns
                    if isinstance(stat, dict) and 'mean' in stat:
                        formatted_parts.append(f"  - {col}: avg={stat['mean']:.2f}, range={stat['min']:.2f}-{stat['max']:.2f}")

        return "\n".join(formatted_parts)

    def _truncate_data_context(self, data_context: str, max_tokens: int) -> str:
        """Truncate data context to fit within token limit"""
        tokens = self.encoding.encode(data_context)
        if len(tokens) <= max_tokens:
            return data_context

        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens) + "\n... (data truncated for analysis)"

    def _parse_ai_response(self, content: str) -> tuple[List[str], List[str]]:
        """Parse AI response to extract insights and recommendations"""
        insights = []
        recommendations = []

        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if any(keyword in line.lower() for keyword in ['insight', 'key finding', 'analysis', 'observation']):
                current_section = 'insights'
                if ':' in line:
                    insight_text = line.split(':', 1)[1].strip()
                    if insight_text:
                        insights.append(insight_text)
                continue
            elif any(keyword in line.lower() for keyword in ['recommendation', 'suggest', 'action', 'improve']):
                current_section = 'recommendations'
                if ':' in line:
                    rec_text = line.split(':', 1)[1].strip()
                    if rec_text:
                        recommendations.append(rec_text)
                continue

            # Add content to current section
            if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                clean_line = line.lstrip('-•*123456789. ').strip()
                if clean_line:
                    if current_section == 'insights':
                        insights.append(clean_line)
                    elif current_section == 'recommendations':
                        recommendations.append(clean_line)
            elif current_section and len(line) > 20:  # Substantial content
                if current_section == 'insights':
                    insights.append(line)
                elif current_section == 'recommendations':
                    recommendations.append(line)

        # Fallback parsing if structured sections not found
        if not insights and not recommendations:
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            for para in paragraphs:
                if len(para) > 30:  # Substantial content
                    if any(keyword in para.lower() for keyword in ['recommend', 'suggest', 'should', 'implement']):
                        recommendations.append(para)
                    else:
                        insights.append(para)

        # Ensure we have some content
        if not insights:
            insights = ["AI analysis completed - see full response for details"]
        if not recommendations:
            recommendations = ["Continue monitoring and analysis"]

        return insights[:10], recommendations[:10]  # Limit to 10 each

    def _calculate_ai_confidence(self, content: str, data_summary: Dict[str, Any]) -> float:
        """Calculate confidence score for AI-generated insights"""
        base_confidence = 0.8  # Base confidence for AI

        # Adjust based on response quality
        if len(content) < 100:
            base_confidence -= 0.2
        elif len(content) > 500:
            base_confidence += 0.1

        # Adjust based on data quality
        if data_summary.get('combined_statistics'):
            missing_pct = data_summary['combined_statistics'].get('overall_missing_percentage', 0)
            if missing_pct > 30:
                base_confidence -= 0.2
            elif missing_pct < 10:
                base_confidence += 0.1

        # Adjust based on data volume
        total_records = data_summary.get('combined_statistics', {}).get('total_records', 0)
        if total_records < 100:
            base_confidence -= 0.1
        elif total_records > 1000:
            base_confidence += 0.1

        return max(0.1, min(1.0, base_confidence))

    def _calculate_statistical_confidence(self, data_summary: Dict[str, Any]) -> float:
        """Calculate confidence score for statistical insights"""
        base_confidence = 0.6  # Base confidence for statistical analysis

        # Adjust based on data quality
        if data_summary.get('combined_statistics'):
            missing_pct = data_summary['combined_statistics'].get('overall_missing_percentage', 0)
            if missing_pct < 5:
                base_confidence += 0.2
            elif missing_pct < 15:
                base_confidence += 0.1
            elif missing_pct > 30:
                base_confidence -= 0.2

        # Adjust based on data volume
        total_records = data_summary.get('combined_statistics', {}).get('total_records', 0)
        if total_records > 1000:
            base_confidence += 0.2
        elif total_records > 500:
            base_confidence += 0.1
        elif total_records < 100:
            base_confidence -= 0.2

        # Adjust based on available metrics
        key_metrics_count = len(data_summary.get('key_metrics', {}))
        if key_metrics_count > 3:
            base_confidence += 0.1
        elif key_metrics_count < 2:
            base_confidence -= 0.1

        return max(0.1, min(1.0, base_confidence))
