"""
Comprehensive report generator using Python libraries
"""

import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import uuid
from datetime import datetime
import tempfile
import base64
from io import BytesIO

# Data processing
import pandas as pd
import numpy as np

# Visualization
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# Report generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

# Excel export
import xlsxwriter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.chart import BarChart, PieChart, LineChart, Reference

from ..utils.logger import setup_logger, LoggedOperation
from ..processors.excel_processor import ExcelProcessor
from ..analysis.analysis_engine import AnalysisEngine
from ..models.schemas import ReportFormat, AnalysisType

logger = setup_logger(__name__)


class ReportGenerator:
    """Advanced report generator with multiple format support"""

    def __init__(self):
        self.excel_processor = ExcelProcessor()
        self.analysis_engine = AnalysisEngine()
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)

        # Set up matplotlib and seaborn styles
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # Configure plotly
        pio.templates.default = "plotly_white"

    async def generate_report(self, file_ids: List[str], format: ReportFormat = ReportFormat.PDF,
                            include_charts: bool = True, analysis_types: List[AnalysisType] = None,
                            custom_title: str = None, sections: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive report in specified format"""

        with LoggedOperation("report_generation", format=format.value, file_count=len(file_ids)):
            try:
                logger.info(f"Generating {format.value} report for {len(file_ids)} files")

                # Default analysis types if not specified
                if analysis_types is None:
                    analysis_types = [AnalysisType.REJECTIONS, AnalysisType.TRENDS, AnalysisType.QUALITY]

                # Generate report ID
                report_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Prepare report data
                report_data = await self._prepare_report_data(file_ids, analysis_types)

                # Generate report based on format
                if format == ReportFormat.PDF:
                    filename = f"healthcare_analytics_report_{timestamp}.pdf"
                    filepath = await self._generate_pdf_report(
                        report_data, filename, include_charts, custom_title
                    )
                elif format == ReportFormat.EXCEL:
                    filename = f"healthcare_analytics_report_{timestamp}.xlsx"
                    filepath = await self._generate_excel_report(
                        report_data, filename, include_charts, custom_title
                    )
                elif format == ReportFormat.JSON:
                    filename = f"healthcare_analytics_report_{timestamp}.json"
                    filepath = await self._generate_json_report(
                        report_data, filename, custom_title
                    )
                elif format == ReportFormat.CSV:
                    filename = f"healthcare_analytics_report_{timestamp}.csv"
                    filepath = await self._generate_csv_report(
                        report_data, filename
                    )
                else:
                    raise ValueError(f"Unsupported report format: {format}")

                # Get file size
                file_size = filepath.stat().st_size if filepath.exists() else 0

                logger.info(f"Report generated successfully: {filename} ({file_size} bytes)")

                return {
                    'report_id': report_id,
                    'filename': filename,
                    'filepath': str(filepath),
                    'file_size': file_size
                }

            except Exception as e:
                logger.error(f"Error generating report: {str(e)}")
                raise

    async def _prepare_report_data(self, file_ids: List[str], analysis_types: List[AnalysisType]) -> Dict[str, Any]:
        """Prepare comprehensive report data"""
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'file_ids': file_ids,
                'analysis_types': [at.value for at in analysis_types],
                'total_files': len(file_ids)
            },
            'executive_summary': {},
            'data_overview': {},
            'analyses': {},
            'charts': {},
            'recommendations': []
        }

        # Data overview
        report_data['data_overview'] = await self._generate_data_overview(file_ids)

        # Run analyses
        for analysis_type in analysis_types:
            try:
                if analysis_type == AnalysisType.REJECTIONS:
                    result = await self.analysis_engine.analyze_rejections(file_ids)
                elif analysis_type == AnalysisType.TRENDS:
                    result = await self.analysis_engine.analyze_trends(file_ids)
                elif analysis_type == AnalysisType.PATTERNS:
                    result = await self.analysis_engine.analyze_patterns(file_ids)
                elif analysis_type == AnalysisType.QUALITY:
                    result = await self.analysis_engine.analyze_quality(file_ids)
                elif analysis_type == AnalysisType.COMPARISON and len(file_ids) > 1:
                    result = await self.analysis_engine.analyze_comparison(file_ids)
                else:
                    continue

                report_data['analyses'][analysis_type.value] = result.dict()

                # Extract recommendations
                if result.recommendations:
                    report_data['recommendations'].extend(result.recommendations)

            except Exception as e:
                logger.error(f"Error in {analysis_type.value} analysis: {str(e)}")
                report_data['analyses'][analysis_type.value] = {'error': str(e)}

        # Generate executive summary
        report_data['executive_summary'] = await self._generate_executive_summary(report_data)

        return report_data

    async def _generate_data_overview(self, file_ids: List[str]) -> Dict[str, Any]:
        """Generate data overview section"""
        overview = {
            'total_files': len(file_ids),
            'files': [],
            'combined_statistics': {}
        }

        total_records = 0
        all_columns = set()

        for file_id in file_ids:
            result = self.excel_processor.get_processing_result(file_id)
            if result:
                file_info = {
                    'file_id': file_id,
                    'records': len(result.data),
                    'columns': len(result.data.columns),
                    'file_type': result.summary.file_type,
                    'quality_score': result.validation.quality_score,
                    'processing_time': result.summary.processing_time
                }
                overview['files'].append(file_info)

                total_records += len(result.data)
                all_columns.update(result.data.columns)

        overview['combined_statistics'] = {
            'total_records': total_records,
            'unique_columns': len(all_columns),
            'average_quality_score': np.mean([f['quality_score'] for f in overview['files']]) if overview['files'] else 0
        }

        return overview

    async def _generate_executive_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        summary = {
            'key_findings': [],
            'critical_issues': [],
            'opportunities': [],
            'overall_health_score': 0.0
        }

        # Extract key findings from analyses
        for analysis_type, result in report_data['analyses'].items():
            if 'error' in result:
                summary['critical_issues'].append(f"Analysis error in {analysis_type}: {result['error']}")
                continue

            if analysis_type == 'rejections' and 'summary' in result:
                rejection_rate = result['summary'].get('rejection_rate', 0)
                if rejection_rate > 15:
                    summary['critical_issues'].append(f"High rejection rate: {rejection_rate:.1f}%")
                elif rejection_rate < 5:
                    summary['opportunities'].append(f"Excellent rejection rate: {rejection_rate:.1f}%")

                summary['key_findings'].append(f"Analyzed {result['summary'].get('total_claims', 0)} claims with {rejection_rate:.1f}% rejection rate")

            elif analysis_type == 'quality' and 'summary' in result:
                quality_score = result['summary'].get('overall_quality_score', 0)
                if quality_score < 0.7:
                    summary['critical_issues'].append(f"Data quality below threshold: {quality_score:.1f}")
                else:
                    summary['key_findings'].append(f"Data quality score: {quality_score:.1f}")

        # Calculate overall health score
        quality_scores = []
        for file_info in report_data['data_overview']['files']:
            quality_scores.append(file_info['quality_score'])

        if quality_scores:
            summary['overall_health_score'] = np.mean(quality_scores)

        return summary

    async def _generate_pdf_report(self, report_data: Dict[str, Any], filename: str,
                                 include_charts: bool, custom_title: str = None) -> Path:
        """Generate PDF report using ReportLab"""
        filepath = self.reports_dir / filename

        # Create PDF document
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )

        # Title page
        title = custom_title or "Healthcare Insurance Analytics Report"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))

        # Metadata
        metadata = report_data['metadata']
        story.append(Paragraph("Report Information", heading_style))

        report_info = [
            ['Generated:', metadata['generated_at']],
            ['Files Analyzed:', str(metadata['total_files'])],
            ['Analysis Types:', ', '.join(metadata['analysis_types'])]
        ]

        table = Table(report_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(PageBreak())

        # Executive Summary
        summary = report_data['executive_summary']
        story.append(Paragraph("Executive Summary", heading_style))

        if summary.get('overall_health_score'):
            story.append(Paragraph(f"Overall Health Score: {summary['overall_health_score']:.1f}/1.0", styles['Normal']))
            story.append(Spacer(1, 12))

        if summary.get('key_findings'):
            story.append(Paragraph("Key Findings:", styles['Heading3']))
            for finding in summary['key_findings']:
                story.append(Paragraph(f"• {finding}", styles['Normal']))
            story.append(Spacer(1, 12))

        if summary.get('critical_issues'):
            story.append(Paragraph("Critical Issues:", styles['Heading3']))
            for issue in summary['critical_issues']:
                story.append(Paragraph(f"• {issue}", styles['Normal']))
            story.append(Spacer(1, 12))

        story.append(PageBreak())

        # Data Overview
        overview = report_data['data_overview']
        story.append(Paragraph("Data Overview", heading_style))

        overview_data = [
            ['Metric', 'Value'],
            ['Total Files', str(overview['total_files'])],
            ['Total Records', str(overview['combined_statistics']['total_records'])],
            ['Unique Columns', str(overview['combined_statistics']['unique_columns'])],
            ['Average Quality Score', f"{overview['combined_statistics']['average_quality_score']:.2f}"]
        ]

        table = Table(overview_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(PageBreak())

        # Analysis Results
        for analysis_type, result in report_data['analyses'].items():
            if 'error' in result:
                continue

            story.append(Paragraph(f"{analysis_type.title()} Analysis", heading_style))

            # Add analysis-specific content
            if 'summary' in result:
                summary_data = result['summary']
                for key, value in summary_data.items():
                    if isinstance(value, (str, int, float)):
                        story.append(Paragraph(f"{key.replace('_', ' ').title()}: {value}", styles['Normal']))

            # Add insights
            if 'insights' in result:
                story.append(Paragraph("Key Insights:", styles['Heading3']))
                for insight in result['insights'][:5]:  # Limit to top 5
                    story.append(Paragraph(f"• {insight}", styles['Normal']))

            story.append(Spacer(1, 20))

        # Recommendations
        if report_data.get('recommendations'):
            story.append(Paragraph("Recommendations", heading_style))
            for i, rec in enumerate(report_data['recommendations'][:10], 1):  # Limit to top 10
                story.append(Paragraph(f"{i}. {rec}", styles['Normal']))

        # Build PDF
        doc.build(story)
        return filepath

    async def _generate_excel_report(self, report_data: Dict[str, Any], filename: str,
                                   include_charts: bool, custom_title: str = None) -> Path:
        """Generate Excel report with multiple sheets"""
        filepath = self.reports_dir / filename

        with pd.ExcelWriter(str(filepath), engine='xlsxwriter') as writer:
            workbook = writer.book

            # Define formats
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#4472C4',
                'font_color': 'white'
            })

            header_format = workbook.add_format({
                'bold': True,
                'font_size': 12,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#D9E2F3',
                'border': 1
            })

            data_format = workbook.add_format({
                'align': 'left',
                'valign': 'vcenter',
                'border': 1
            })

            # Summary Sheet
            summary_df = self._create_summary_dataframe(report_data)
            summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)

            worksheet = writer.sheets['Executive Summary']
            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:B', 40)

            # Data Overview Sheet
            overview_df = self._create_overview_dataframe(report_data['data_overview'])
            overview_df.to_excel(writer, sheet_name='Data Overview', index=False)

            # Analysis Results Sheets
            for analysis_type, result in report_data['analyses'].items():
                if 'error' in result:
                    continue

                # Create analysis dataframe
                analysis_df = self._create_analysis_dataframe(result)
                sheet_name = analysis_type.replace('_', ' ').title()[:31]  # Excel sheet name limit
                analysis_df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Format the sheet
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column('A:Z', 15)

                # Add charts if requested
                if include_charts and 'charts' in result:
                    await self._add_excel_charts(worksheet, workbook, result['charts'])

            # Recommendations Sheet
            if report_data.get('recommendations'):
                rec_df = pd.DataFrame({
                    'Recommendation': report_data['recommendations'],
                    'Priority': ['High'] * len(report_data['recommendations'])
                })
                rec_df.to_excel(writer, sheet_name='Recommendations', index=False)

        return filepath

    async def _generate_json_report(self, report_data: Dict[str, Any], filename: str,
                                  custom_title: str = None) -> Path:
        """Generate JSON report"""
        filepath = self.reports_dir / filename

        # Add title to report data
        if custom_title:
            report_data['title'] = custom_title

        # Serialize complex objects
        json_data = self._serialize_for_json(report_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        return filepath

    async def _generate_csv_report(self, report_data: Dict[str, Any], filename: str) -> Path:
        """Generate CSV report with main data"""
        filepath = self.reports_dir / filename

        # Create combined summary data
        summary_data = []

        # Add metadata
        metadata = report_data['metadata']
        summary_data.append(['Report Type', 'Healthcare Analytics Report'])
        summary_data.append(['Generated', metadata['generated_at']])
        summary_data.append(['Files Analyzed', metadata['total_files']])
        summary_data.append(['', ''])  # Empty row

        # Add executive summary
        summary = report_data['executive_summary']
        summary_data.append(['Executive Summary', ''])
        summary_data.append(['Overall Health Score', summary.get('overall_health_score', 'N/A')])
        summary_data.append(['', ''])

        # Add key findings
        if summary.get('key_findings'):
            summary_data.append(['Key Findings', ''])
            for finding in summary['key_findings']:
                summary_data.append(['', finding])
            summary_data.append(['', ''])

        # Add analysis summaries
        for analysis_type, result in report_data['analyses'].items():
            if 'error' in result:
                continue

            summary_data.append([f'{analysis_type.title()} Analysis', ''])
            if 'summary' in result:
                for key, value in result['summary'].items():
                    if isinstance(value, (str, int, float)):
                        summary_data.append([key.replace('_', ' ').title(), str(value)])
            summary_data.append(['', ''])

        # Create DataFrame and save
        df = pd.DataFrame(summary_data, columns=['Category', 'Value'])
        df.to_csv(filepath, index=False)

        return filepath

    # Helper methods for dataframe creation
    def _create_summary_dataframe(self, report_data: Dict[str, Any]) -> pd.DataFrame:
        """Create executive summary dataframe"""
        summary = report_data['executive_summary']
        data = []

        data.append(['Overall Health Score', summary.get('overall_health_score', 'N/A')])
        data.append(['Total Files Analyzed', report_data['metadata']['total_files']])
        data.append(['Generation Date', report_data['metadata']['generated_at']])

        if summary.get('key_findings'):
            data.append(['Key Findings', '; '.join(summary['key_findings'][:3])])

        if summary.get('critical_issues'):
            data.append(['Critical Issues', '; '.join(summary['critical_issues'][:3])])

        return pd.DataFrame(data, columns=['Metric', 'Value'])

    def _create_overview_dataframe(self, overview: Dict[str, Any]) -> pd.DataFrame:
        """Create data overview dataframe"""
        data = []

        for file_info in overview['files']:
            data.append([
                file_info['file_id'][:8],  # Shortened ID
                file_info['records'],
                file_info['columns'],
                file_info['file_type'],
                f"{file_info['quality_score']:.2f}",
                f"{file_info['processing_time']:.2f}s"
            ])

        return pd.DataFrame(data, columns=[
            'File ID', 'Records', 'Columns', 'Type', 'Quality Score', 'Processing Time'
        ])

    def _create_analysis_dataframe(self, result: Dict[str, Any]) -> pd.DataFrame:
        """Create analysis results dataframe"""
        data = []

        if 'summary' in result:
            for key, value in result['summary'].items():
                if isinstance(value, (str, int, float)):
                    data.append(['Summary', key.replace('_', ' ').title(), str(value)])

        if 'statistics' in result:
            for key, value in result['statistics'].items():
                if isinstance(value, (str, int, float)):
                    data.append(['Statistics', key.replace('_', ' ').title(), str(value)])

        if 'insights' in result:
            for i, insight in enumerate(result['insights'][:10], 1):
                data.append(['Insights', f'Insight {i}', insight])

        if 'recommendations' in result:
            for i, rec in enumerate(result['recommendations'][:10], 1):
                data.append(['Recommendations', f'Recommendation {i}', rec])

        if not data:
            data = [['No Data', 'Available', '']]

        return pd.DataFrame(data, columns=['Category', 'Item', 'Value'])

    def _serialize_for_json(self, obj: Any) -> Any:
        """Serialize complex objects for JSON"""
        if isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    async def _add_excel_charts(self, worksheet, workbook, charts_data: List[Dict[str, Any]]):
        """Add charts to Excel worksheet"""
        # This is a placeholder for chart implementation
        # In a full implementation, you would create Excel charts based on the chart data
        pass
