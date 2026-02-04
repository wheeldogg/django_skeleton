"""
Views for LLM Analysis application.

Provides HTMX-powered views for the analysis interface.
"""

import logging
import time
from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST

from .models import (
    PromptTemplate,
    SystemSettings,
    PromptAuditLog,
    PromptMode,
)
from .forms import PromptForm, TemplatePromptForm
from .services.bedrock import (
    BedrockService,
    BedrockServiceError,
    GuardrailBlockedError,
)
from .services.security import PromptSecurityService
from .services.output_parser import OutputParser
from .services.demo import DemoService

logger = logging.getLogger(__name__)


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def analysis_home(request):
    """
    Main analysis page.

    Displays the appropriate input interface based on system settings.
    """
    settings = SystemSettings.get_settings()
    templates = PromptTemplate.objects.filter(is_active=True)

    # Group templates by category
    template_categories = {}
    for template in templates:
        if template.category not in template_categories:
            template_categories[template.category] = []
        template_categories[template.category].append(template)

    context = {
        'settings': settings,
        'prompt_mode': settings.prompt_mode,
        'templates': templates,
        'template_categories': template_categories,
        'form': PromptForm() if settings.prompt_mode != PromptMode.CONSTRAINED else None,
        'demo_mode': settings.demo_mode,
        'demo_message': DemoService.get_demo_banner_message() if settings.demo_mode else None,
    }
    return render(request, 'llm_analysis/analysis.html', context)


@login_required
@require_POST
def analyze(request):
    """
    Process analysis request.

    Handles both free-text and template-based prompts.
    Returns HTMX partial for results.
    """
    settings = SystemSettings.get_settings()
    start_time = time.time()

    # Determine if bypass is allowed
    bypass_guardrails = (
        settings.bypass_guardrails and
        request.user.is_superuser and
        request.POST.get('bypass') == 'true'
    )

    # Initialize audit log data
    audit_data = {
        'user': request.user if request.user.is_authenticated else None,
        'mode': settings.prompt_mode,
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
        'bypass_used': bypass_guardrails,
    }

    # Process based on mode
    if settings.prompt_mode == PromptMode.CONSTRAINED:
        # Template-based prompt
        template_id = request.POST.get('template_id')
        if not template_id:
            return render(request, 'llm_analysis/partials/error.html', {
                'error': 'Please select a template'
            })

        template = get_object_or_404(PromptTemplate, id=template_id, is_active=True)
        form = TemplatePromptForm(request.POST, template=template)

        if not form.is_valid():
            return render(request, 'llm_analysis/partials/error.html', {
                'error': form.errors.as_text()
            })

        prompt = form.get_rendered_prompt()
        audit_data['template'] = template
        audit_data['prompt'] = request.POST.get('prompt', '')[:1000]
        audit_data['rendered_prompt'] = prompt

        # Increment template usage
        template.increment_usage()

    else:
        # Free-text prompt (guided or open mode)
        form = PromptForm(
            request.POST,
            enable_security_check=(settings.prompt_mode != PromptMode.OPEN or not bypass_guardrails)
        )

        if not form.is_valid():
            # Check if it was a security violation
            if form.has_error('prompt', 'security_violation'):
                audit_data['prompt'] = request.POST.get('prompt', '')[:1000]
                audit_data['was_filtered'] = True
                audit_data['filter_reason'] = str(form.errors['prompt'])
                PromptAuditLog.objects.create(**audit_data)

            return render(request, 'llm_analysis/partials/error.html', {
                'error': form.errors['prompt'][0] if 'prompt' in form.errors else str(form.errors)
            })

        prompt = form.cleaned_data['prompt']
        audit_data['prompt'] = prompt
        audit_data['rendered_prompt'] = prompt

    # Check for demo mode
    if settings.demo_mode:
        # Use demo service for mock responses
        response = DemoService.generate_mock_response(prompt)

        # Parse the mock response
        result = OutputParser.parse(response.get('result', {}))

        # Update audit log
        audit_data['llm_response'] = f"[DEMO MODE] {str(response.get('result', {}))[:4900]}"
        audit_data['response_time_ms'] = response.get('elapsed_ms')
        audit_data['input_tokens'] = response['usage'].get('input_tokens')
        audit_data['output_tokens'] = response['usage'].get('output_tokens')

        PromptAuditLog.objects.create(**audit_data)

        return render(request, 'llm_analysis/partials/results.html', {
            'result': result,
            'response_time_ms': response.get('elapsed_ms'),
            'input_tokens': response['usage'].get('input_tokens'),
            'output_tokens': response['usage'].get('output_tokens'),
            'demo_mode': True,
        })

    # Call Bedrock (production mode)
    try:
        bedrock_service = BedrockService()

        # Use structured output for analysis
        guardrail_id = None if bypass_guardrails else None  # Uses default from settings
        response = bedrock_service.invoke_structured(
            prompt=prompt,
            guardrail_id=guardrail_id if not bypass_guardrails else None,
            model_id=settings.model_id,
            max_tokens=settings.max_tokens,
        )

        # Parse the structured response
        result = OutputParser.parse(response.get('result', {}))

        # Update audit log
        audit_data['llm_response'] = str(response.get('result', {}))[:5000]
        audit_data['response_time_ms'] = response.get('elapsed_ms')
        audit_data['input_tokens'] = response['usage'].get('input_tokens')
        audit_data['output_tokens'] = response['usage'].get('output_tokens')
        audit_data['guardrail_response'] = response.get('guardrail_trace')

        PromptAuditLog.objects.create(**audit_data)

        return render(request, 'llm_analysis/partials/results.html', {
            'result': result,
            'response_time_ms': response.get('elapsed_ms'),
            'input_tokens': response['usage'].get('input_tokens'),
            'output_tokens': response['usage'].get('output_tokens'),
        })

    except GuardrailBlockedError as e:
        audit_data['was_filtered'] = True
        audit_data['filter_reason'] = str(e)
        audit_data['guardrail_response'] = e.guardrail_response
        PromptAuditLog.objects.create(**audit_data)

        return render(request, 'llm_analysis/partials/error.html', {
            'error': 'Your request was blocked by content safety filters. Please rephrase your query.',
            'is_guardrail_block': True
        })

    except BedrockServiceError as e:
        logger.error(f'Bedrock service error: {e}')
        audit_data['was_filtered'] = True
        audit_data['filter_reason'] = f'Service error: {e}'
        PromptAuditLog.objects.create(**audit_data)

        return render(request, 'llm_analysis/partials/error.html', {
            'error': 'An error occurred while processing your request. Please try again.'
        })


@login_required
def get_template_form(request, template_id: int):
    """
    Get the form for a specific template (HTMX partial).
    """
    template = get_object_or_404(PromptTemplate, id=template_id, is_active=True)
    form = TemplatePromptForm(template=template)

    return render(request, 'llm_analysis/partials/template_form.html', {
        'template': template,
        'form': form,
    })


@login_required
def get_templates_by_category(request, category: str):
    """
    Get templates for a category (HTMX partial).
    """
    templates = PromptTemplate.objects.filter(
        category=category,
        is_active=True
    )

    return render(request, 'llm_analysis/partials/template_list.html', {
        'templates': templates,
        'category': category,
    })


@staff_member_required
def audit_log_list(request):
    """
    View audit logs (staff only).
    """
    logs = PromptAuditLog.objects.select_related('user', 'template')[:100]

    # Filter options
    filter_blocked = request.GET.get('blocked')
    if filter_blocked == 'true':
        logs = logs.filter(was_filtered=True)
    elif filter_blocked == 'false':
        logs = logs.filter(was_filtered=False)

    return render(request, 'llm_analysis/audit_logs.html', {
        'logs': logs,
        'filter_blocked': filter_blocked,
    })


@staff_member_required
def audit_log_detail(request, log_id: int):
    """
    View single audit log detail (staff only).
    """
    log = get_object_or_404(PromptAuditLog, id=log_id)

    return render(request, 'llm_analysis/audit_log_detail.html', {
        'log': log,
    })


@staff_member_required
@require_POST
def check_bedrock_connection(request):
    """
    Test Bedrock connectivity (HTMX endpoint).
    """
    try:
        service = BedrockService()
        is_connected = service.check_connection()

        if is_connected:
            return HttpResponse(
                '<span class="text-green-600">Connected</span>',
                content_type='text/html'
            )
        else:
            return HttpResponse(
                '<span class="text-red-600">Connection failed</span>',
                content_type='text/html'
            )
    except Exception as e:
        logger.error(f'Bedrock connection check error: {e}')
        return HttpResponse(
            f'<span class="text-red-600">Error: {e}</span>',
            content_type='text/html'
        )


@login_required
def analysis_history(request):
    """
    View user's analysis history.
    """
    logs = PromptAuditLog.objects.filter(
        user=request.user
    ).select_related('template')[:50]

    return render(request, 'llm_analysis/history.html', {
        'logs': logs,
    })


# Error handlers for the app
def handle_analysis_error(request, error_message: str, status: int = 400):
    """Render error partial for HTMX requests."""
    if request.htmx:
        return render(
            request,
            'llm_analysis/partials/error.html',
            {'error': error_message},
            status=status
        )
    messages.error(request, error_message)
    return HttpResponse(status=status)
