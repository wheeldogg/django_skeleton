"""
Demo app admin configuration.
"""

from django.contrib import admin
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin configuration for Item model."""
    list_display = ['title', 'priority', 'is_completed', 'owner', 'created_at', 'updated_at']
    list_filter = ['is_completed', 'priority', 'created_at']
    search_fields = ['title', 'description', 'owner__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('title', 'description')
        }),
        ('Status', {
            'fields': ('is_completed', 'priority')
        }),
        ('Ownership', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at')