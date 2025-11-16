"""
Demo app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'demo'

urlpatterns = [
    path('', views.demo_home, name='home'),
    path('items/', views.ItemListView.as_view(), name='item-list'),
    path('items/<int:pk>/toggle/', views.toggle_item, name='item-toggle'),
    path('items/create/', views.create_item_htmx, name='item-create'),
    path('items/<int:pk>/edit/', views.inline_edit, name='item-edit'),
    path('items/search/', views.search_items, name='item-search'),
    path('alpine/', views.alpine_examples, name='alpine-examples'),
    path('api/example/', views.api_example, name='api-example'),
]