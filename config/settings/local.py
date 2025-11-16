"""
Local development settings.
"""

from .base import *  # noqa

# Override any settings for local development
DEBUG = True

# Note: django_extensions is already included in base settings

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar (optional, add to dependencies if needed)
# if DEBUG:
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
#     INTERNAL_IPS = ['127.0.0.1', 'localhost']