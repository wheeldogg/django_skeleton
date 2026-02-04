"""
Demo mode service for testing UI without Bedrock connection.

Returns realistic mock responses for development and demonstration.
"""

import random
import time
from typing import Dict, Any


class DemoService:
    """
    Provides mock responses for demo mode.

    Use this when you want to test the UI without AWS credentials
    or Bedrock access.
    """

    # Sample hypothesis responses
    DEMO_HYPOTHESES = [
        {
            'title': 'Seasonal patterns detected in the data',
            'confidence': 'high',
            'summary': 'Analysis reveals strong seasonal patterns with peaks in Q4 and troughs in Q1. This aligns with typical consumer behavior patterns and suggests planning should account for these cyclical variations.',
            'evidence': [
                'Q4 metrics consistently 23% higher than annual average',
                'January shows 15% decline from December across all years',
                'Pattern consistent across 3+ years of historical data',
            ],
            'visualization_type': 'chart'
        },
        {
            'title': 'Correlation between marketing spend and engagement',
            'confidence': 'medium',
            'summary': 'There appears to be a moderate positive correlation between marketing investment and user engagement metrics, though other factors may be contributing.',
            'evidence': [
                'R-squared value of 0.67 between spend and engagement',
                'Lag effect observed: engagement peaks 2-3 weeks after campaigns',
                'Some high-engagement periods occurred without increased spend',
            ],
            'visualization_type': 'chart'
        },
        {
            'title': 'Anomaly detected in recent performance',
            'confidence': 'low',
            'summary': 'Recent data shows deviation from expected patterns. Further investigation recommended to determine if this represents a trend change or temporary fluctuation.',
            'evidence': [
                'Last 30 days show 8% variance from predicted values',
                'Similar anomalies in past resolved within 45 days',
                'External factors (market conditions) may be contributing',
            ],
            'visualization_type': 'table'
        },
    ]

    DEMO_SEARCH_RESULTS = [
        {
            'source': 'Historical Dataset (2022-2024)',
            'relevance': 'high',
            'snippet': 'Primary data source containing 2.3M records across the analysis period.',
            'url': None
        },
        {
            'source': 'Industry Benchmark Report',
            'relevance': 'medium',
            'snippet': 'Comparative data from industry peers showing similar seasonal patterns.',
            'url': None
        },
        {
            'source': 'External Market Data',
            'relevance': 'low',
            'snippet': 'Supplementary economic indicators that may influence observed trends.',
            'url': None
        },
    ]

    DEMO_EXPLANATIONS = [
        {
            'methodology': 'This analysis employed time-series decomposition to identify trend, seasonal, and residual components. Statistical significance was assessed using standard hypothesis testing with α=0.05.',
            'limitations': 'Analysis is based on available historical data only. External factors not captured in the dataset may influence results. Correlation does not imply causation.',
            'next_steps': [
                'Validate findings with domain experts',
                'Collect additional data points for higher confidence',
                'Design controlled experiment to test causal hypotheses',
                'Monitor key metrics over next quarter for trend confirmation',
            ]
        },
        {
            'methodology': 'Comparative analysis using cohort segmentation and statistical testing. Data was normalized to account for varying sample sizes across segments.',
            'limitations': 'Sample sizes vary across segments which may affect reliability of some comparisons. Self-selection bias may be present in certain cohorts.',
            'next_steps': [
                'Increase sample size for underrepresented segments',
                'Implement A/B testing for key hypotheses',
                'Review data collection methodology for potential biases',
            ]
        },
    ]

    @classmethod
    def generate_mock_response(cls, prompt: str) -> Dict[str, Any]:
        """
        Generate a realistic mock response based on the prompt.

        Args:
            prompt: The user's analysis prompt

        Returns:
            Mock response in the same format as Bedrock structured output
        """
        # Simulate some processing time
        time.sleep(random.uniform(0.5, 1.5))

        # Select random hypotheses (1-3)
        num_hypotheses = random.randint(1, 3)
        hypotheses = random.sample(cls.DEMO_HYPOTHESES, num_hypotheses)

        # Add prompt-specific context to first hypothesis
        if hypotheses:
            hypotheses[0] = hypotheses[0].copy()
            hypotheses[0]['summary'] = f"Based on your query about '{prompt[:50]}...': " + hypotheses[0]['summary']

        # Select search results
        num_results = random.randint(1, 3)
        search_results = random.sample(cls.DEMO_SEARCH_RESULTS, num_results)

        # Select explanation
        explanation = random.choice(cls.DEMO_EXPLANATIONS)

        return {
            'result': {
                'hypotheses': hypotheses,
                'search_results': search_results,
                'explanation': explanation,
            },
            'usage': {
                'input_tokens': len(prompt.split()) * 2,  # Rough estimate
                'output_tokens': random.randint(400, 800),
            },
            'stop_reason': 'end_turn',
            'elapsed_ms': random.randint(800, 2500),
            'guardrail_trace': None,
            'demo_mode': True,
        }

    @classmethod
    def generate_demo_error(cls) -> Dict[str, Any]:
        """Generate a mock error response for testing error handling."""
        return {
            'error': True,
            'message': 'This is a simulated error for testing purposes.',
            'demo_mode': True,
        }

    @classmethod
    def get_demo_banner_message(cls) -> str:
        """Get the demo mode banner message."""
        return (
            "Demo Mode Active: Responses are simulated and do not use Amazon Bedrock. "
            "Configure AWS credentials and disable demo mode in admin settings for real analysis."
        )
