"""
Output parsing utilities for structured LLM responses.

Handles parsing, validation, and transformation of LLM outputs.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    """Represents a single hypothesis from the analysis."""
    title: str
    confidence: str  # high, medium, low
    summary: str
    evidence: List[str] = field(default_factory=list)
    visualization_type: str = 'none'

    @classmethod
    def from_dict(cls, data: dict) -> 'Hypothesis':
        return cls(
            title=data.get('title', 'Untitled'),
            confidence=data.get('confidence', 'low'),
            summary=data.get('summary', ''),
            evidence=data.get('evidence', []),
            visualization_type=data.get('visualization_type', 'none')
        )

    @property
    def confidence_color(self) -> str:
        """Get Tailwind color class for confidence level."""
        colors = {
            'high': 'green',
            'medium': 'yellow',
            'low': 'red'
        }
        return colors.get(self.confidence, 'gray')


@dataclass
class SearchResult:
    """Represents a search result or data source reference."""
    source: str
    relevance: str  # high, medium, low
    snippet: str
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'SearchResult':
        return cls(
            source=data.get('source', 'Unknown'),
            relevance=data.get('relevance', 'low'),
            snippet=data.get('snippet', ''),
            url=data.get('url')
        )

    @property
    def relevance_color(self) -> str:
        """Get Tailwind color class for relevance level."""
        colors = {
            'high': 'green',
            'medium': 'yellow',
            'low': 'gray'
        }
        return colors.get(self.relevance, 'gray')


@dataclass
class Explanation:
    """Represents the methodology explanation."""
    methodology: str
    limitations: str
    next_steps: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'Explanation':
        return cls(
            methodology=data.get('methodology', ''),
            limitations=data.get('limitations', ''),
            next_steps=data.get('next_steps', [])
        )


@dataclass
class AnalysisResult:
    """Complete analysis result from the LLM."""
    hypotheses: List[Hypothesis] = field(default_factory=list)
    search_results: List[SearchResult] = field(default_factory=list)
    explanation: Optional[Explanation] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True
    error_message: str = ''

    @property
    def has_hypotheses(self) -> bool:
        return len(self.hypotheses) > 0

    @property
    def has_search_results(self) -> bool:
        return len(self.search_results) > 0

    @property
    def hypothesis_count(self) -> int:
        return len(self.hypotheses)

    @property
    def high_confidence_count(self) -> int:
        return sum(1 for h in self.hypotheses if h.confidence == 'high')


class OutputParser:
    """
    Parser for structured LLM output.

    Converts raw JSON from Bedrock tool use into typed dataclasses.
    """

    @classmethod
    def parse(cls, raw_output: dict) -> AnalysisResult:
        """
        Parse raw LLM output into structured AnalysisResult.

        Args:
            raw_output: Raw dictionary from Bedrock response

        Returns:
            AnalysisResult with parsed data
        """
        if not raw_output:
            return AnalysisResult(
                is_valid=False,
                error_message='Empty response from LLM',
                raw_response=raw_output
            )

        try:
            # Parse hypotheses
            hypotheses = []
            raw_hypotheses = raw_output.get('hypotheses', [])
            for h_data in raw_hypotheses:
                try:
                    hypotheses.append(Hypothesis.from_dict(h_data))
                except Exception as e:
                    logger.warning(f'Failed to parse hypothesis: {e}')

            # Parse search results
            search_results = []
            raw_results = raw_output.get('search_results', [])
            for r_data in raw_results:
                try:
                    search_results.append(SearchResult.from_dict(r_data))
                except Exception as e:
                    logger.warning(f'Failed to parse search result: {e}')

            # Parse explanation
            explanation = None
            raw_explanation = raw_output.get('explanation')
            if raw_explanation:
                try:
                    explanation = Explanation.from_dict(raw_explanation)
                except Exception as e:
                    logger.warning(f'Failed to parse explanation: {e}')

            return AnalysisResult(
                hypotheses=hypotheses,
                search_results=search_results,
                explanation=explanation,
                raw_response=raw_output,
                is_valid=True
            )

        except Exception as e:
            logger.error(f'Failed to parse LLM output: {e}')
            return AnalysisResult(
                is_valid=False,
                error_message=str(e),
                raw_response=raw_output
            )

    @classmethod
    def validate_schema(cls, output: dict) -> tuple[bool, str]:
        """
        Validate that output matches expected schema.

        Args:
            output: Raw output dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(output, dict):
            return False, 'Output must be a dictionary'

        # Check for required fields
        if 'hypotheses' not in output:
            return False, 'Missing required field: hypotheses'

        if not isinstance(output.get('hypotheses'), list):
            return False, 'hypotheses must be an array'

        # Validate hypotheses structure
        for i, h in enumerate(output.get('hypotheses', [])):
            if not isinstance(h, dict):
                return False, f'Hypothesis {i} must be an object'

            required_fields = ['title', 'confidence', 'summary']
            for field in required_fields:
                if field not in h:
                    return False, f'Hypothesis {i} missing required field: {field}'

            if h.get('confidence') not in ['high', 'medium', 'low']:
                return False, f'Hypothesis {i} has invalid confidence level'

        # Validate explanation if present
        explanation = output.get('explanation')
        if explanation:
            if not isinstance(explanation, dict):
                return False, 'explanation must be an object'

            required_fields = ['methodology', 'limitations']
            for field in required_fields:
                if field not in explanation:
                    return False, f'explanation missing required field: {field}'

        return True, ''


class ResponseFormatter:
    """
    Formats analysis results for different output contexts.
    """

    @staticmethod
    def to_json(result: AnalysisResult) -> dict:
        """Convert AnalysisResult to JSON-serializable dict."""
        return {
            'hypotheses': [
                {
                    'title': h.title,
                    'confidence': h.confidence,
                    'summary': h.summary,
                    'evidence': h.evidence,
                    'visualization_type': h.visualization_type
                }
                for h in result.hypotheses
            ],
            'search_results': [
                {
                    'source': r.source,
                    'relevance': r.relevance,
                    'snippet': r.snippet,
                    'url': r.url
                }
                for r in result.search_results
            ],
            'explanation': {
                'methodology': result.explanation.methodology,
                'limitations': result.explanation.limitations,
                'next_steps': result.explanation.next_steps
            } if result.explanation else None,
            'meta': {
                'hypothesis_count': result.hypothesis_count,
                'high_confidence_count': result.high_confidence_count,
                'is_valid': result.is_valid
            }
        }

    @staticmethod
    def to_markdown(result: AnalysisResult) -> str:
        """Convert AnalysisResult to Markdown format."""
        lines = ['# Analysis Results\n']

        if result.hypotheses:
            lines.append('## Hypotheses\n')
            for h in result.hypotheses:
                confidence_emoji = {'high': '++', 'medium': '+-', 'low': '--'}.get(h.confidence, '-')
                lines.append(f'### {h.title} [{confidence_emoji}]\n')
                lines.append(f'{h.summary}\n')
                if h.evidence:
                    lines.append('**Evidence:**')
                    for e in h.evidence:
                        lines.append(f'- {e}')
                lines.append('')

        if result.search_results:
            lines.append('## Data Sources\n')
            for r in result.search_results:
                lines.append(f'- **{r.source}** ({r.relevance}): {r.snippet}')
            lines.append('')

        if result.explanation:
            lines.append('## Methodology\n')
            lines.append(result.explanation.methodology)
            lines.append('')
            lines.append('### Limitations\n')
            lines.append(result.explanation.limitations)
            lines.append('')
            if result.explanation.next_steps:
                lines.append('### Next Steps\n')
                for step in result.explanation.next_steps:
                    lines.append(f'1. {step}')

        return '\n'.join(lines)
