"""
URL configuration for Django Skeleton project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Auth URLs
    path('accounts/', include('django.contrib.auth.urls')),

    # App URLs
    path('demo/', include('apps.demo.urls')),
    path('analysis/', include('apps.llm_analysis.urls')),

    # API URLs
    path('api/', include('config.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Optional: Django Debug Toolbar
    # import debug_toolbar
    # urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

# Custom error handlers
handler404 = 'apps.demo.views.custom_404'
handler500 = 'apps.demo.views.custom_500'