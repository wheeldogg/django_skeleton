"""
Demo app tests.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from .models import Item


class ItemModelTest(TestCase):
    """Test cases for Item model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.item = Item.objects.create(
            title='Test Item',
            description='Test Description',
            priority=2,
            owner=self.user
        )

    def test_item_creation(self):
        """Test item is created correctly."""
        self.assertEqual(self.item.title, 'Test Item')
        self.assertEqual(self.item.owner, self.user)
        self.assertFalse(self.item.is_completed)

    def test_item_str_method(self):
        """Test string representation of item."""
        self.assertEqual(str(self.item), 'Test Item')

    def test_item_absolute_url(self):
        """Test get_absolute_url method."""
        self.assertEqual(
            self.item.get_absolute_url(),
            f'/demo/items/{self.item.pk}/'
        )