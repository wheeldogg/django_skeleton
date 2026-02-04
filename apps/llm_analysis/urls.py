"""
URL configuration for LLM Analysis application.
"""

from django.urls import path
from . import views

app_name = 'llm_analysis'

urlpatterns = [
    # Main analysis interface
    path('', views.analysis_home, name='home'),
    path('analyze/', views.analyze, name='analyze'),

    # Template management (HTMX partials)
    path('template/<int:template_id>/form/', views.get_template_form, name='template-form'),
    path('templates/<str:category>/', views.get_templates_by_category, name='templates-by-category'),

    # History
    path('history/', views.analysis_history, name='history'),

    # Admin/staff endpoints
    path('audit/', views.audit_log_list, name='audit-logs'),
    path('audit/<int:log_id>/', views.audit_log_detail, name='audit-log-detail'),
    path('check-connection/', views.check_bedrock_connection, name='check-connection'),
]
