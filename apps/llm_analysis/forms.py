"""
Forms for LLM Analysis application.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import PromptTemplate, SystemSettings, PromptMode
from .services.security import PromptSecurityService, InputValidator


class PromptForm(forms.Form):
    """
    Form for free-text prompt input (Guided and Open modes).
    """
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'rows': 4,
            'placeholder': 'Enter your data analysis query...',
            'x-model': 'prompt',
        }),
        min_length=10,
        max_length=10000,
        help_text='Describe what you want to analyze. Be specific about the data and metrics.'
    )

    def __init__(self, *args, enable_security_check: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_security_check = enable_security_check
        self.security_service = PromptSecurityService()

    def clean_prompt(self):
        prompt = self.cleaned_data.get('prompt', '').strip()

        # Length validation
        is_valid, error = InputValidator.validate_length(prompt)
        if not is_valid:
            raise ValidationError(error)

        # Security check
        if self.enable_security_check:
            is_safe, reason, severity = self.security_service.validate_prompt(prompt)
            if not is_safe:
                raise ValidationError(
                    f'Your prompt was blocked for security reasons: {reason}',
                    code='security_violation'
                )

        return prompt


class TemplatePromptForm(forms.Form):
    """
    Form for template-based prompt input (Constrained mode).
    """
    template_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, template: PromptTemplate = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = template
        self.security_service = PromptSecurityService()

        if template:
            self.fields['template_id'].initial = template.id
            # Dynamically add fields based on template variables
            for var in template.variables:
                field_name = var.get('name')
                field_label = var.get('label', field_name)
                field_type = var.get('type', 'text')
                required = var.get('required', True)
                max_length = var.get('max_length', 500)
                choices = var.get('choices', [])
                help_text = var.get('help_text', '')

                if field_type == 'select' and choices:
                    self.fields[field_name] = forms.ChoiceField(
                        choices=[(c, c) for c in choices],
                        required=required,
                        label=field_label,
                        help_text=help_text,
                        widget=forms.Select(attrs={
                            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                        })
                    )
                elif field_type == 'textarea':
                    self.fields[field_name] = forms.CharField(
                        required=required,
                        label=field_label,
                        max_length=max_length,
                        help_text=help_text,
                        widget=forms.Textarea(attrs={
                            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                            'rows': 3
                        })
                    )
                elif field_type == 'number':
                    self.fields[field_name] = forms.DecimalField(
                        required=required,
                        label=field_label,
                        help_text=help_text,
                        widget=forms.NumberInput(attrs={
                            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                        })
                    )
                else:
                    self.fields[field_name] = forms.CharField(
                        required=required,
                        label=field_label,
                        max_length=max_length,
                        help_text=help_text,
                        widget=forms.TextInput(attrs={
                            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                        })
                    )

    def clean(self):
        cleaned_data = super().clean()

        if not self.template:
            raise ValidationError('Template not found')

        # Validate variable values
        variables = {
            var.get('name'): cleaned_data.get(var.get('name'))
            for var in self.template.variables
            if var.get('name') in cleaned_data
        }

        is_valid, error = InputValidator.validate_template_variables(
            variables, self.template.variables
        )
        if not is_valid:
            raise ValidationError(error)

        # Render the prompt and check for injection
        rendered_prompt = self.template.render(variables)
        is_safe, reason, severity = self.security_service.validate_prompt(rendered_prompt)
        if not is_safe:
            raise ValidationError(
                f'The rendered prompt was blocked for security reasons: {reason}',
                code='security_violation'
            )

        cleaned_data['rendered_prompt'] = rendered_prompt
        return cleaned_data

    def get_rendered_prompt(self) -> str:
        """Get the rendered prompt after validation."""
        return self.cleaned_data.get('rendered_prompt', '')


class SystemSettingsForm(forms.ModelForm):
    """
    Form for admin to update system settings.
    """
    class Meta:
        model = SystemSettings
        fields = ['prompt_mode', 'bypass_guardrails', 'max_tokens', 'model_id']
        widgets = {
            'prompt_mode': forms.Select(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'bypass_guardrails': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'max_tokens': forms.NumberInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': 100,
                'max': 8192
            }),
            'model_id': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
        }

    def clean_bypass_guardrails(self):
        bypass = self.cleaned_data.get('bypass_guardrails', False)
        from django.conf import settings as django_settings

        # Prevent bypass in production
        if bypass and not django_settings.DEBUG:
            raise ValidationError(
                'Guardrails bypass cannot be enabled in production mode'
            )
        return bypass


class PromptTemplateForm(forms.ModelForm):
    """
    Form for creating/editing prompt templates.
    """
    class Meta:
        model = PromptTemplate
        fields = ['name', 'description', 'template', 'variables', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 2
            }),
            'template': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 font-mono',
                'rows': 5,
                'placeholder': 'Analyze {dataset} for {metric} trends over the past {time_period}.'
            }),
            'variables': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 font-mono',
                'rows': 6,
                'placeholder': '[{"name": "dataset", "label": "Dataset", "type": "text"}]'
            }),
            'category': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
        }

    def clean_template(self):
        template = self.cleaned_data.get('template', '')

        # Check for basic injection patterns in template itself
        security_service = PromptSecurityService()
        is_safe, reason, severity = security_service.validate_prompt(template)
        if not is_safe:
            raise ValidationError(
                f'Template contains potentially dangerous content: {reason}'
            )

        return template

    def clean_variables(self):
        variables = self.cleaned_data.get('variables', [])

        if not isinstance(variables, list):
            raise ValidationError('Variables must be a JSON array')

        for var in variables:
            if not isinstance(var, dict):
                raise ValidationError('Each variable must be a JSON object')
            if 'name' not in var:
                raise ValidationError('Each variable must have a "name" field')
            if not var['name'].isidentifier():
                raise ValidationError(
                    f'Variable name "{var["name"]}" is not a valid identifier'
                )

        return variables
