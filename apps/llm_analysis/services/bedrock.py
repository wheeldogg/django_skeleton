"""
Amazon Bedrock integration service.

Provides:
- BedrockService: Main service class for LLM invocations
- Guardrails integration
- Structured output via tool use
"""

import json
import logging
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


# Output schema for structured analysis responses
ANALYSIS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "hypotheses": {
            "type": "array",
            "description": "List of hypotheses generated from the analysis",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Brief title for the hypothesis"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Confidence level in this hypothesis"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Detailed summary of the hypothesis"
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of evidence supporting this hypothesis"
                    },
                    "visualization_type": {
                        "type": "string",
                        "enum": ["chart", "table", "text", "none"],
                        "description": "Recommended visualization type"
                    }
                },
                "required": ["title", "confidence", "summary", "evidence"]
            }
        },
        "search_results": {
            "type": "array",
            "description": "Relevant data sources or references",
            "items": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Name or identifier of the source"
                    },
                    "relevance": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Relevance to the query"
                    },
                    "snippet": {
                        "type": "string",
                        "description": "Key excerpt or finding"
                    },
                    "url": {
                        "type": "string",
                        "description": "Optional URL or reference link"
                    }
                },
                "required": ["source", "relevance", "snippet"]
            }
        },
        "explanation": {
            "type": "object",
            "description": "Explanation of the analysis methodology",
            "properties": {
                "methodology": {
                    "type": "string",
                    "description": "How the analysis was conducted"
                },
                "limitations": {
                    "type": "string",
                    "description": "Known limitations of this analysis"
                },
                "next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recommended follow-up actions"
                }
            },
            "required": ["methodology", "limitations", "next_steps"]
        }
    },
    "required": ["hypotheses", "explanation"]
}

# System prompt for data analysis
DATA_ANALYST_SYSTEM_PROMPT = """You are an expert data analyst assistant. Your role is to:

1. Analyze data and generate hypotheses based on the information provided
2. Provide evidence-based insights with clear confidence levels
3. Be transparent about limitations and methodology
4. Suggest actionable next steps

Guidelines:
- Always cite specific evidence for your hypotheses
- Be conservative with confidence levels - use "high" only when strongly supported
- Consider alternative explanations
- Focus on actionable insights
- If data is insufficient, clearly state what additional information would help

You must respond using the provided analysis tool to structure your output."""


class BedrockServiceError(Exception):
    """Custom exception for Bedrock service errors."""
    pass


class GuardrailBlockedError(BedrockServiceError):
    """Raised when content is blocked by Guardrails."""
    def __init__(self, message: str, guardrail_response: dict = None):
        super().__init__(message)
        self.guardrail_response = guardrail_response


class BedrockService:
    """
    Service for interacting with Amazon Bedrock.

    Provides methods for:
    - Basic LLM invocation with guardrails
    - Structured output using tool use
    - Error handling and logging
    """

    def __init__(self):
        self.client = self._create_client()
        self.guardrail_id = getattr(settings, 'BEDROCK_GUARDRAIL_ID', None)
        self.guardrail_version = getattr(settings, 'BEDROCK_GUARDRAIL_VERSION', 'DRAFT')
        self.default_model_id = getattr(
            settings,
            'BEDROCK_MODEL_ID',
            'anthropic.claude-3-sonnet-20240229-v1:0'
        )
        self.default_max_tokens = getattr(settings, 'BEDROCK_MAX_TOKENS', 4096)

    def _create_client(self):
        """Create boto3 Bedrock runtime client."""
        region = getattr(settings, 'AWS_DEFAULT_REGION', 'us-east-1')
        return boto3.client('bedrock-runtime', region_name=region)

    def invoke_with_guardrails(
        self,
        prompt: str,
        guardrail_id: str = None,
        model_id: str = None,
        max_tokens: int = None,
        system_prompt: str = None,
    ) -> dict:
        """
        Invoke Claude model with Guardrails protection.

        Args:
            prompt: User prompt text
            guardrail_id: Override default guardrail ID
            model_id: Override default model ID
            max_tokens: Override default max tokens
            system_prompt: Optional system prompt

        Returns:
            Dict with 'content', 'usage', 'stop_reason', and 'guardrail_trace'

        Raises:
            GuardrailBlockedError: If content is blocked by guardrails
            BedrockServiceError: For other Bedrock errors
        """
        start_time = time.time()

        model = model_id or self.default_model_id
        tokens = max_tokens or self.default_max_tokens
        gid = guardrail_id or self.guardrail_id

        # Build request
        request_params = {
            'modelId': model,
            'messages': [
                {
                    'role': 'user',
                    'content': [{'text': prompt}]
                }
            ],
            'inferenceConfig': {
                'maxTokens': tokens,
            }
        }

        # Add system prompt if provided
        if system_prompt:
            request_params['system'] = [{'text': system_prompt}]

        # Add guardrails if configured
        if gid:
            request_params['guardrailConfig'] = {
                'guardrailIdentifier': gid,
                'guardrailVersion': self.guardrail_version,
                'trace': 'enabled'
            }

        try:
            response = self.client.converse(**request_params)

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Check for guardrail intervention
            stop_reason = response.get('stopReason', '')
            if stop_reason == 'guardrail_intervened':
                guardrail_trace = response.get('trace', {}).get('guardrail', {})
                raise GuardrailBlockedError(
                    'Content blocked by Bedrock Guardrails',
                    guardrail_response=guardrail_trace
                )

            # Extract response content
            output = response.get('output', {})
            message = output.get('message', {})
            content_blocks = message.get('content', [])
            text_content = ''
            for block in content_blocks:
                if 'text' in block:
                    text_content += block['text']

            # Extract usage
            usage = response.get('usage', {})

            return {
                'content': text_content,
                'usage': {
                    'input_tokens': usage.get('inputTokens', 0),
                    'output_tokens': usage.get('outputTokens', 0),
                },
                'stop_reason': stop_reason,
                'elapsed_ms': elapsed_ms,
                'guardrail_trace': response.get('trace', {}).get('guardrail'),
            }

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f'Bedrock ClientError: {error_code} - {error_msg}')
            raise BedrockServiceError(f'Bedrock error: {error_msg}') from e

        except BotoCoreError as e:
            logger.error(f'Bedrock BotoCoreError: {e}')
            raise BedrockServiceError(f'AWS error: {e}') from e

    def invoke_structured(
        self,
        prompt: str,
        output_schema: dict = None,
        guardrail_id: str = None,
        model_id: str = None,
        max_tokens: int = None,
    ) -> dict:
        """
        Invoke Claude with tool use for structured JSON output.

        Uses the Converse API's tool use feature to enforce output schema.

        Args:
            prompt: User prompt text
            output_schema: JSON schema for output (defaults to ANALYSIS_OUTPUT_SCHEMA)
            guardrail_id: Override default guardrail ID
            model_id: Override default model ID
            max_tokens: Override default max tokens

        Returns:
            Dict with structured 'result', 'usage', and metadata

        Raises:
            GuardrailBlockedError: If content is blocked
            BedrockServiceError: For other errors
        """
        start_time = time.time()

        model = model_id or self.default_model_id
        tokens = max_tokens or self.default_max_tokens
        gid = guardrail_id or self.guardrail_id
        schema = output_schema or ANALYSIS_OUTPUT_SCHEMA

        # Define the analysis tool
        tool_config = {
            'tools': [
                {
                    'toolSpec': {
                        'name': 'submit_analysis',
                        'description': 'Submit the structured analysis results. You must use this tool to provide your analysis.',
                        'inputSchema': {
                            'json': schema
                        }
                    }
                }
            ],
            'toolChoice': {
                'tool': {'name': 'submit_analysis'}
            }
        }

        # Build request
        request_params = {
            'modelId': model,
            'messages': [
                {
                    'role': 'user',
                    'content': [{'text': prompt}]
                }
            ],
            'system': [{'text': DATA_ANALYST_SYSTEM_PROMPT}],
            'toolConfig': tool_config,
            'inferenceConfig': {
                'maxTokens': tokens,
            }
        }

        # Add guardrails if configured
        if gid:
            request_params['guardrailConfig'] = {
                'guardrailIdentifier': gid,
                'guardrailVersion': self.guardrail_version,
                'trace': 'enabled'
            }

        try:
            response = self.client.converse(**request_params)

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Check for guardrail intervention
            stop_reason = response.get('stopReason', '')
            if stop_reason == 'guardrail_intervened':
                guardrail_trace = response.get('trace', {}).get('guardrail', {})
                raise GuardrailBlockedError(
                    'Content blocked by Bedrock Guardrails',
                    guardrail_response=guardrail_trace
                )

            # Extract tool use response
            output = response.get('output', {})
            message = output.get('message', {})
            content_blocks = message.get('content', [])

            structured_result = None
            for block in content_blocks:
                if 'toolUse' in block:
                    tool_use = block['toolUse']
                    if tool_use.get('name') == 'submit_analysis':
                        structured_result = tool_use.get('input', {})
                        break

            if structured_result is None:
                logger.warning('No structured output received from LLM')
                # Fallback: try to parse any text content as JSON
                for block in content_blocks:
                    if 'text' in block:
                        try:
                            structured_result = json.loads(block['text'])
                            break
                        except json.JSONDecodeError:
                            pass

            # Extract usage
            usage = response.get('usage', {})

            return {
                'result': structured_result or {},
                'usage': {
                    'input_tokens': usage.get('inputTokens', 0),
                    'output_tokens': usage.get('outputTokens', 0),
                },
                'stop_reason': stop_reason,
                'elapsed_ms': elapsed_ms,
                'guardrail_trace': response.get('trace', {}).get('guardrail'),
            }

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f'Bedrock ClientError: {error_code} - {error_msg}')
            raise BedrockServiceError(f'Bedrock error: {error_msg}') from e

        except BotoCoreError as e:
            logger.error(f'Bedrock BotoCoreError: {e}')
            raise BedrockServiceError(f'AWS error: {e}') from e

    def check_connection(self) -> bool:
        """
        Test the Bedrock connection.

        Returns:
            True if connection is successful
        """
        try:
            # Simple invocation to test connectivity
            self.client.converse(
                modelId=self.default_model_id,
                messages=[
                    {'role': 'user', 'content': [{'text': 'Hello'}]}
                ],
                inferenceConfig={'maxTokens': 10}
            )
            return True
        except Exception as e:
            logger.error(f'Bedrock connection check failed: {e}')
            return False
