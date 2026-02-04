# Generated manually for LLM Analysis app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PromptTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Display name for the template', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Description of what this template analyzes')),
                ('template', models.TextField(help_text='Template text with {variable} placeholders')),
                ('variables', models.JSONField(default=list, help_text='List of variable definitions: [{"name": "dataset", "label": "Dataset", "type": "text"}]')),
                ('category', models.CharField(db_index=True, help_text='Category for grouping templates', max_length=50)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('usage_count', models.PositiveIntegerField(default=0, help_text='Number of times this template has been used')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Prompt Template',
                'verbose_name_plural': 'Prompt Templates',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt_mode', models.CharField(choices=[('constrained', 'Constrained (Templates Only)'), ('guided', 'Guided Free-Text'), ('open', 'Open with Filtering')], default='guided', help_text='Controls how users can input prompts', max_length=20)),
                ('bypass_guardrails', models.BooleanField(default=False, help_text='Development only: bypass Bedrock Guardrails (auto-disabled in production)')),
                ('demo_mode', models.BooleanField(default=True, help_text='Demo mode: returns mock responses without calling Bedrock')),
                ('max_tokens', models.PositiveIntegerField(default=4096, help_text='Maximum tokens for LLM response')),
                ('model_id', models.CharField(default='anthropic.claude-3-sonnet-20240229-v1:0', help_text='Bedrock model identifier', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'System Settings',
                'verbose_name_plural': 'System Settings',
            },
        ),
        migrations.CreateModel(
            name='PromptAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField(help_text='The prompt text submitted')),
                ('rendered_prompt', models.TextField(blank=True, help_text='Final prompt sent to LLM (after template rendering)')),
                ('mode', models.CharField(choices=[('constrained', 'Constrained (Templates Only)'), ('guided', 'Guided Free-Text'), ('open', 'Open with Filtering')], help_text='Prompt mode used', max_length=20)),
                ('was_filtered', models.BooleanField(default=False, help_text='Whether the prompt was blocked by filters')),
                ('filter_reason', models.TextField(blank=True, help_text='Reason for filtering (if blocked)')),
                ('guardrail_response', models.JSONField(blank=True, help_text='Full Guardrails API response', null=True)),
                ('llm_response', models.TextField(blank=True, help_text='LLM response (truncated for storage)')),
                ('response_time_ms', models.PositiveIntegerField(blank=True, help_text='Response time in milliseconds', null=True)),
                ('input_tokens', models.PositiveIntegerField(blank=True, null=True)),
                ('output_tokens', models.PositiveIntegerField(blank=True, null=True)),
                ('bypass_used', models.BooleanField(default=False, help_text='Whether guardrails bypass was used (dev only)')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='Client IP address', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='Client user agent')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('template', models.ForeignKey(blank=True, help_text='Template used (if constrained mode)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='llm_analysis.prompttemplate')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prompt_audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Prompt Audit Log',
                'verbose_name_plural': 'Prompt Audit Logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='promptauditlog',
            index=models.Index(fields=['user', '-created_at'], name='llm_analysi_user_id_1d56e0_idx'),
        ),
        migrations.AddIndex(
            model_name='promptauditlog',
            index=models.Index(fields=['was_filtered', '-created_at'], name='llm_analysi_was_fil_dc61a9_idx'),
        ),
    ]
