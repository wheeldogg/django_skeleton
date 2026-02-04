"""
Admin configuration for LLM Analysis application.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import SystemSettings, PromptTemplate, PromptAuditLog


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin for system settings (singleton)."""

    list_display = ['prompt_mode_display', 'demo_status', 'bypass_status', 'model_id', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Prompt Configuration', {
            'fields': ('prompt_mode', 'model_id', 'max_tokens')
        }),
        ('Demo & Development', {
            'fields': ('demo_mode', 'bypass_guardrails'),
            'description': 'Demo mode returns simulated responses without calling Bedrock. Bypass should only be used for testing.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def prompt_mode_display(self, obj):
        return obj.get_prompt_mode_display()
    prompt_mode_display.short_description = 'Prompt Mode'

    def demo_status(self, obj):
        if obj.demo_mode:
            return format_html(
                '<span style="color: orange; font-weight: bold;">DEMO</span>'
            )
        return format_html(
            '<span style="color: green;">Production</span>'
        )
    demo_status.short_description = 'Mode'

    def bypass_status(self, obj):
        if obj.bypass_guardrails:
            return format_html(
                '<span style="color: red; font-weight: bold;">ENABLED</span>'
            )
        return format_html(
            '<span style="color: green;">Disabled</span>'
        )
    bypass_status.short_description = 'Guardrail Bypass'


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    """Admin for prompt templates."""

    list_display = ['name', 'category', 'is_active', 'usage_count', 'updated_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description', 'template']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'is_active')
        }),
        ('Template Configuration', {
            'fields': ('template', 'variables'),
            'description': 'Use {variable_name} syntax for placeholders. Variables should be a JSON array.'
        }),
        ('Statistics', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Make usage_count always readonly
        return self.readonly_fields


@admin.register(PromptAuditLog)
class PromptAuditLogAdmin(admin.ModelAdmin):
    """Admin for audit logs (read-only)."""

    list_display = [
        'created_at',
        'user_display',
        'mode',
        'status_display',
        'response_time_display',
        'ip_address'
    ]
    list_filter = ['was_filtered', 'mode', 'bypass_used', 'created_at']
    search_fields = ['prompt', 'user__username', 'ip_address']
    readonly_fields = [
        'user', 'prompt', 'rendered_prompt', 'mode', 'template',
        'was_filtered', 'filter_reason', 'guardrail_response',
        'llm_response', 'response_time_ms', 'input_tokens',
        'output_tokens', 'bypass_used', 'ip_address', 'user_agent',
        'created_at'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'mode', 'template', 'ip_address', 'user_agent', 'created_at')
        }),
        ('Prompt', {
            'fields': ('prompt', 'rendered_prompt'),
        }),
        ('Security', {
            'fields': ('was_filtered', 'filter_reason', 'guardrail_response', 'bypass_used'),
        }),
        ('Response', {
            'fields': ('llm_response', 'response_time_ms', 'input_tokens', 'output_tokens'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser

    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return 'Anonymous'
    user_display.short_description = 'User'

    def status_display(self, obj):
        if obj.was_filtered:
            return format_html(
                '<span style="color: red;">BLOCKED</span>'
            )
        return format_html(
            '<span style="color: green;">OK</span>'
        )
    status_display.short_description = 'Status'

    def response_time_display(self, obj):
        if obj.response_time_ms:
            return f'{obj.response_time_ms}ms'
        return '-'
    response_time_display.short_description = 'Response Time'
