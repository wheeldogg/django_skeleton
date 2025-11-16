"""
API URL Configuration.
"""

from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()

# Register your API viewsets here
# Example: router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]