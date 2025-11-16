"""
Main settings file - imports from base settings.
For specific environments, use DJANGO_SETTINGS_MODULE:
- config.settings.local (development)
- config.settings.production (production)
"""

from .settings.base import *  # noqa