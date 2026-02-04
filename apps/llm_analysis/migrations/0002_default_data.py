# Data migration to create default templates and settings

from django.db import migrations


def create_default_data(apps, schema_editor):
    """Create default system settings and prompt templates."""
    SystemSettings = apps.get_model('llm_analysis', 'SystemSettings')
    PromptTemplate = apps.get_model('llm_analysis', 'PromptTemplate')

    # Create default system settings
    SystemSettings.objects.get_or_create(
        pk=1,
        defaults={
            'prompt_mode': 'guided',
            'bypass_guardrails': False,
            'demo_mode': True,  # Demo mode enabled by default
            'max_tokens': 4096,
            'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
        }
    )

    # Create default prompt templates
    templates = [
        {
            'name': 'Trend Analysis',
            'description': 'Analyze trends in your data over a specified time period',
            'category': 'Analysis',
            'template': 'Analyze the trends in {dataset} data, focusing on {metric} over the past {time_period}. Identify any significant patterns, anomalies, or seasonal variations.',
            'variables': [
                {'name': 'dataset', 'label': 'Dataset Name', 'type': 'text', 'required': True, 'help_text': 'Name or description of your dataset'},
                {'name': 'metric', 'label': 'Key Metric', 'type': 'text', 'required': True, 'help_text': 'The primary metric to analyze'},
                {'name': 'time_period', 'label': 'Time Period', 'type': 'select', 'required': True, 'choices': ['last 7 days', 'last 30 days', 'last quarter', 'last year']},
            ],
        },
        {
            'name': 'Comparative Analysis',
            'description': 'Compare two groups or segments within your data',
            'category': 'Analysis',
            'template': 'Compare {group_a} against {group_b} based on {comparison_metrics}. Highlight key differences, similarities, and provide statistical significance where applicable.',
            'variables': [
                {'name': 'group_a', 'label': 'First Group', 'type': 'text', 'required': True},
                {'name': 'group_b', 'label': 'Second Group', 'type': 'text', 'required': True},
                {'name': 'comparison_metrics', 'label': 'Metrics to Compare', 'type': 'textarea', 'required': True, 'help_text': 'List the metrics or dimensions to compare'},
            ],
        },
        {
            'name': 'Anomaly Detection',
            'description': 'Identify unusual patterns or outliers in your data',
            'category': 'Analysis',
            'template': 'Analyze {dataset} for anomalies and outliers in {target_variables}. Flag any data points that deviate significantly from expected patterns and suggest potential causes.',
            'variables': [
                {'name': 'dataset', 'label': 'Dataset Description', 'type': 'text', 'required': True},
                {'name': 'target_variables', 'label': 'Variables to Analyze', 'type': 'textarea', 'required': True, 'help_text': 'Which variables should be checked for anomalies?'},
            ],
        },
        {
            'name': 'KPI Dashboard Summary',
            'description': 'Generate a summary of key performance indicators',
            'category': 'Reporting',
            'template': 'Generate an executive summary of the following KPIs for {business_unit}: {kpi_list}. Include current values, trends, and recommendations for improvement.',
            'variables': [
                {'name': 'business_unit', 'label': 'Business Unit', 'type': 'text', 'required': True},
                {'name': 'kpi_list', 'label': 'KPIs', 'type': 'textarea', 'required': True, 'help_text': 'List the KPIs to summarize'},
            ],
        },
        {
            'name': 'Correlation Analysis',
            'description': 'Find relationships between different variables',
            'category': 'Analysis',
            'template': 'Analyze the correlation between {variable_x} and {variable_y} in the context of {context}. Determine if there is a significant relationship and explain potential causal mechanisms.',
            'variables': [
                {'name': 'variable_x', 'label': 'First Variable', 'type': 'text', 'required': True},
                {'name': 'variable_y', 'label': 'Second Variable', 'type': 'text', 'required': True},
                {'name': 'context', 'label': 'Business Context', 'type': 'textarea', 'required': True, 'help_text': 'Describe the business context for this analysis'},
            ],
        },
        {
            'name': 'Forecast Request',
            'description': 'Request predictions based on historical data',
            'category': 'Forecasting',
            'template': 'Based on historical {metric} data, provide a forecast for the next {forecast_period}. Consider any known factors such as {external_factors} that might influence the forecast.',
            'variables': [
                {'name': 'metric', 'label': 'Metric to Forecast', 'type': 'text', 'required': True},
                {'name': 'forecast_period', 'label': 'Forecast Period', 'type': 'select', 'required': True, 'choices': ['1 week', '1 month', '1 quarter', '6 months', '1 year']},
                {'name': 'external_factors', 'label': 'External Factors', 'type': 'textarea', 'required': False, 'help_text': 'Any known external factors that might affect the forecast'},
            ],
        },
        {
            'name': 'Data Quality Assessment',
            'description': 'Evaluate the quality and completeness of your data',
            'category': 'Data Quality',
            'template': 'Assess the quality of {dataset} data, focusing on: completeness, accuracy, consistency, and timeliness. Identify any data quality issues and recommend remediation steps.',
            'variables': [
                {'name': 'dataset', 'label': 'Dataset Description', 'type': 'textarea', 'required': True, 'help_text': 'Describe the dataset and its structure'},
            ],
        },
        {
            'name': 'Root Cause Analysis',
            'description': 'Investigate the underlying causes of an observed issue',
            'category': 'Investigation',
            'template': 'Perform a root cause analysis for the following issue: {issue_description}. The issue was observed in {affected_area} starting around {start_time}. Provide a hypothesis tree and recommended investigation steps.',
            'variables': [
                {'name': 'issue_description', 'label': 'Issue Description', 'type': 'textarea', 'required': True},
                {'name': 'affected_area', 'label': 'Affected Area', 'type': 'text', 'required': True},
                {'name': 'start_time', 'label': 'When Issue Started', 'type': 'text', 'required': True, 'help_text': 'Approximate time the issue was first noticed'},
            ],
        },
    ]

    for template_data in templates:
        PromptTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults={
                'description': template_data['description'],
                'category': template_data['category'],
                'template': template_data['template'],
                'variables': template_data['variables'],
                'is_active': True,
            }
        )


def reverse_default_data(apps, schema_editor):
    """Remove default data (optional reverse migration)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('llm_analysis', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_data, reverse_default_data),
    ]
