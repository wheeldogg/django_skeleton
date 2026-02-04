"""
Models for LLM Analysis application.

Includes:
- SystemSettings: Global feature flags and configuration
- PromptTemplate: Pre-defined templates for constrained mode
- PromptAuditLog: Security audit trail for all prompts
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


class PromptMode(models.TextChoices):
    """Available prompt input modes."""
    CONSTRAINED = 'constrained', 'Constrained (Templates Only)'
    GUIDED = 'guided', 'Guided Free-Text'
    OPEN = 'open', 'Open with Filtering'


class SystemSettings(models.Model):
    """
    Singleton model for system-wide settings.
    Controls prompt mode and security bypass options.
    """
    prompt_mode = models.CharField(
        max_length=20,
        choices=PromptMode.choices,
        default=PromptMode.GUIDED,
        help_text='Controls how users can input prompts'
    )
    bypass_guardrails = models.BooleanField(
        default=False,
        help_text='Development only: bypass Bedrock Guardrails (auto-disabled in production)'
    )
    demo_mode = models.BooleanField(
        default=True,
        help_text='Demo mode: returns mock responses without calling Bedrock'
    )
    max_tokens = models.PositiveIntegerField(
        default=4096,
        help_text='Maximum tokens for LLM response'
    )
    model_id = models.CharField(
        max_length=100,
        default='anthropic.claude-3-sonnet-20240229-v1:0',
        help_text='Bedrock model identifier'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f'System Settings (Mode: {self.get_prompt_mode_display()})'

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
        # Clear cache when settings change
        cache.delete('system_settings')

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        settings = cache.get('system_settings')
        if settings is None:
            settings, _ = cls.objects.get_or_create(pk=1)
            cache.set('system_settings', settings, timeout=300)
        return settings


class PromptTemplate(models.Model):
    """
    Pre-defined prompt templates for constrained mode.
    Templates contain placeholders that users fill in.
    """
    name = models.CharField(
        max_length=100,
        help_text='Display name for the template'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of what this template analyzes'
    )
    template = models.TextField(
        help_text='Template text with {variable} placeholders'
    )
    variables = models.JSONField(
        default=list,
        help_text='List of variable definitions: [{"name": "dataset", "label": "Dataset", "type": "text"}]'
    )
    category = models.CharField(
        max_length=50,
        help_text='Category for grouping templates',
        db_index=True
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times this template has been used'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Prompt Template'
        verbose_name_plural = 'Prompt Templates'

    def __str__(self):
        return f'{self.category}: {self.name}'

    def render(self, values: dict) -> str:
        """
        Render the template with provided values.

        Args:
            values: Dict mapping variable names to values

        Returns:
            Rendered prompt string
        """
        prompt = self.template
        for var in self.variables:
            var_name = var.get('name', '')
            if var_name in values:
                prompt = prompt.replace(f'{{{var_name}}}', str(values[var_name]))
        return prompt

    def increment_usage(self):
        """Increment the usage counter."""
        self.usage_count = models.F('usage_count') + 1
        self.save(update_fields=['usage_count'])


class PromptAuditLog(models.Model):
    """
    Audit log for all prompts submitted to the system.
    Records security events and filtering decisions.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prompt_audit_logs'
    )
    prompt = models.TextField(
        help_text='The prompt text submitted'
    )
    rendered_prompt = models.TextField(
        blank=True,
        help_text='Final prompt sent to LLM (after template rendering)'
    )
    mode = models.CharField(
        max_length=20,
        choices=PromptMode.choices,
        help_text='Prompt mode used'
    )
    template = models.ForeignKey(
        PromptTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='Template used (if constrained mode)'
    )
    was_filtered = models.BooleanField(
        default=False,
        help_text='Whether the prompt was blocked by filters'
    )
    filter_reason = models.TextField(
        blank=True,
        help_text='Reason for filtering (if blocked)'
    )
    guardrail_response = models.JSONField(
        null=True,
        blank=True,
        help_text='Full Guardrails API response'
    )
    llm_response = models.TextField(
        blank=True,
        help_text='LLM response (truncated for storage)'
    )
    response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Response time in milliseconds'
    )
    input_tokens = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    output_tokens = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    bypass_used = models.BooleanField(
        default=False,
        help_text='Whether guardrails bypass was used (dev only)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Client IP address'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='Client user agent'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prompt Audit Log'
        verbose_name_plural = 'Prompt Audit Logs'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['was_filtered', '-created_at']),
        ]

    def __str__(self):
        status = 'BLOCKED' if self.was_filtered else 'OK'
        user_str = self.user.username if self.user else 'Anonymous'
        return f'[{status}] {user_str} @ {self.created_at:%Y-%m-%d %H:%M}'

    @property
    def prompt_preview(self):
        """Return truncated prompt for display."""
        if len(self.prompt) > 100:
            return f'{self.prompt[:100]}...'
        return self.prompt
