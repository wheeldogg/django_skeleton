"""
Security services for prompt validation and injection detection.

Provides an additional layer of protection beyond Bedrock Guardrails.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SecurityCheckResult:
    """Result of a security check."""
    is_safe: bool
    reason: str = ''
    pattern_matched: str = ''
    severity: str = 'low'  # low, medium, high, critical


class PromptSecurityService:
    """
    Custom security layer for prompt injection detection.

    Complements Bedrock Guardrails with pattern-based detection
    for common prompt injection techniques.
    """

    # Patterns for prompt injection attempts (case-insensitive)
    INJECTION_PATTERNS = [
        # Direct instruction override
        (r'ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|guidelines?)',
         'Instruction override attempt', 'critical'),
        (r'disregard\s+(all\s+)?(your|the|my)?\s*(instructions?|rules?|guidelines?|training)',
         'Instruction disregard attempt', 'critical'),
        (r'forget\s+(everything|all|what)\s+(you\s+)?(know|learned|were\s+told)',
         'Memory reset attempt', 'critical'),

        # Role/identity manipulation
        (r'you\s+are\s+now\s+(?!a\s+data\s+analyst)',
         'Role override attempt', 'high'),
        (r'pretend\s+(to\s+be|you\s+are|you\'re)',
         'Role pretend attempt', 'high'),
        (r'act\s+as\s+if\s+you\s+(are|were)\s+(?!analyzing)',
         'Role acting attempt', 'high'),
        (r'roleplay\s+as',
         'Roleplay attempt', 'high'),
        (r'from\s+now\s+on\s+you\s+(are|will)',
         'Persistent role change', 'high'),

        # System prompt extraction
        (r'(show|tell|reveal|display|print|output)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions?|rules?)',
         'System prompt extraction', 'critical'),
        (r'what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?)',
         'System prompt inquiry', 'high'),
        (r'repeat\s+(your|the)\s+(initial|original|first|system)\s+(prompt|instructions?|message)',
         'Prompt repeat attempt', 'critical'),

        # Jailbreak techniques
        (r'(DAN|STAN|DUDE)\s*(mode)?',
         'Known jailbreak persona', 'critical'),
        (r'do\s+anything\s+now',
         'DAN jailbreak attempt', 'critical'),
        (r'(developer|debug|maintenance|god)\s+mode',
         'Privilege escalation attempt', 'critical'),
        (r'bypass\s+(safety|security|filter|guardrail)',
         'Bypass attempt', 'critical'),

        # Encoding/obfuscation
        (r'base64\s*(encode|decode)',
         'Encoding manipulation', 'medium'),
        (r'rot13',
         'Encoding manipulation', 'medium'),
        (r'in\s+(hex|binary|morse)',
         'Encoding manipulation', 'medium'),

        # Output manipulation
        (r'respond\s+(only\s+)?with\s+(yes|no|true|false|1|0)',
         'Output constraint attempt', 'medium'),
        (r'only\s+say\s+',
         'Output constraint attempt', 'medium'),

        # Context injection
        (r'\[\s*system\s*\]',
         'System message injection', 'critical'),
        (r'<\s*/?system\s*>',
         'System tag injection', 'critical'),
        (r'###\s*(system|instructions?)\s*:',
         'System marker injection', 'high'),

        # Delimiter attacks
        (r'---+\s*(end|ignore|new)\s*(prompt|instructions?)?',
         'Delimiter injection', 'high'),
        (r'```\s*(system|hidden|ignore)',
         'Code block injection', 'high'),
    ]

    # Topics that should be blocked (outside data analysis scope)
    OFF_TOPIC_PATTERNS = [
        (r'(write|create|generate)\s+(a\s+)?(story|poem|song|essay|fiction)',
         'Creative writing request', 'low'),
        (r'(tell\s+me\s+)?a\s+joke',
         'Entertainment request', 'low'),
        (r'(how\s+to\s+)?(hack|crack|exploit|attack)\s+',
         'Security attack request', 'high'),
        (r'(make|create|write)\s+(a\s+)?(malware|virus|ransomware)',
         'Malware request', 'critical'),
    ]

    def __init__(self, enable_off_topic_check: bool = True):
        """
        Initialize the security service.

        Args:
            enable_off_topic_check: Whether to check for off-topic requests
        """
        self.enable_off_topic_check = enable_off_topic_check
        # Compile patterns for efficiency
        self._compiled_injection = [
            (re.compile(p, re.IGNORECASE), reason, severity)
            for p, reason, severity in self.INJECTION_PATTERNS
        ]
        self._compiled_off_topic = [
            (re.compile(p, re.IGNORECASE), reason, severity)
            for p, reason, severity in self.OFF_TOPIC_PATTERNS
        ]

    def check_for_injection(self, prompt: str) -> SecurityCheckResult:
        """
        Check prompt for injection attempts.

        Args:
            prompt: The prompt text to check

        Returns:
            SecurityCheckResult with safety status
        """
        for pattern, reason, severity in self._compiled_injection:
            match = pattern.search(prompt)
            if match:
                logger.warning(
                    f'Prompt injection detected: {reason} '
                    f'(matched: "{match.group()}")'
                )
                return SecurityCheckResult(
                    is_safe=False,
                    reason=reason,
                    pattern_matched=match.group(),
                    severity=severity
                )

        return SecurityCheckResult(is_safe=True)

    def check_off_topic(self, prompt: str) -> SecurityCheckResult:
        """
        Check if prompt is off-topic for data analysis.

        Args:
            prompt: The prompt text to check

        Returns:
            SecurityCheckResult with safety status
        """
        if not self.enable_off_topic_check:
            return SecurityCheckResult(is_safe=True)

        for pattern, reason, severity in self._compiled_off_topic:
            match = pattern.search(prompt)
            if match:
                logger.info(
                    f'Off-topic request detected: {reason} '
                    f'(matched: "{match.group()}")'
                )
                return SecurityCheckResult(
                    is_safe=False,
                    reason=reason,
                    pattern_matched=match.group(),
                    severity=severity
                )

        return SecurityCheckResult(is_safe=True)

    def validate_prompt(self, prompt: str) -> Tuple[bool, str, str]:
        """
        Full prompt validation.

        Runs all security checks.

        Args:
            prompt: The prompt text to validate

        Returns:
            Tuple of (is_safe, reason, severity)
        """
        # Check for injection attempts first (most critical)
        injection_result = self.check_for_injection(prompt)
        if not injection_result.is_safe:
            return False, injection_result.reason, injection_result.severity

        # Check for off-topic content
        off_topic_result = self.check_off_topic(prompt)
        if not off_topic_result.is_safe:
            return False, off_topic_result.reason, off_topic_result.severity

        return True, '', ''

    def sanitize_prompt(self, prompt: str) -> str:
        """
        Sanitize prompt by removing potentially dangerous content.

        Note: This is a best-effort sanitization. It's better to
        reject suspicious prompts than try to sanitize them.

        Args:
            prompt: The prompt to sanitize

        Returns:
            Sanitized prompt
        """
        # Remove potential system message markers
        sanitized = re.sub(r'\[\s*system\s*\]', '[filtered]', prompt, flags=re.IGNORECASE)
        sanitized = re.sub(r'<\s*/?system\s*>', '', sanitized, flags=re.IGNORECASE)

        # Remove excessive whitespace that might be used to hide content
        sanitized = re.sub(r'\s{10,}', ' ', sanitized)

        # Remove null bytes and other control characters
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)

        return sanitized.strip()


class InputValidator:
    """
    Validates and sanitizes user input beyond security concerns.
    """

    MAX_PROMPT_LENGTH = 10000
    MIN_PROMPT_LENGTH = 10

    @classmethod
    def validate_length(cls, prompt: str) -> Tuple[bool, str]:
        """
        Validate prompt length.

        Args:
            prompt: The prompt to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(prompt) < cls.MIN_PROMPT_LENGTH:
            return False, f'Prompt must be at least {cls.MIN_PROMPT_LENGTH} characters'

        if len(prompt) > cls.MAX_PROMPT_LENGTH:
            return False, f'Prompt exceeds maximum length of {cls.MAX_PROMPT_LENGTH} characters'

        return True, ''

    @classmethod
    def validate_template_variables(cls, variables: dict, expected: List[dict]) -> Tuple[bool, str]:
        """
        Validate template variable values.

        Args:
            variables: Provided variable values
            expected: Expected variable definitions

        Returns:
            Tuple of (is_valid, error_message)
        """
        for var_def in expected:
            name = var_def.get('name')
            required = var_def.get('required', True)

            if required and name not in variables:
                return False, f'Missing required variable: {name}'

            if name in variables:
                value = variables[name]
                var_type = var_def.get('type', 'text')

                # Type validation
                if var_type == 'number':
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        return False, f'Variable {name} must be a number'

                # Length validation
                max_length = var_def.get('max_length', 500)
                if isinstance(value, str) and len(value) > max_length:
                    return False, f'Variable {name} exceeds maximum length of {max_length}'

        return True, ''
