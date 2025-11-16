"""
Demo app models.
"""

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class TimeStampedModel(models.Model):
    """Abstract base class with created and modified timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Item(TimeStampedModel):
    """Sample item model for demonstrating CRUD operations."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    priority = models.IntegerField(
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')],
        default=2
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='items',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('demo:item-detail', kwargs={'pk': self.pk})