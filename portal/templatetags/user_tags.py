# Create a new file: your_app/templatetags/user_tags.py

from django import template
from portal.models import SecretaryAdmin  # Replace 'your_app' with your actual app name

register = template.Library()

@register.simple_tag
def is_secretary_admin(user):
    """Check if user is a secretary admin"""
    try:
        secretary = SecretaryAdmin.objects.get(user=user)
        return secretary.is_active
    except SecretaryAdmin.DoesNotExist:
        return False

@register.filter
def is_secretary(user):
    """Filter to check if user is a secretary admin"""
    try:
        secretary = SecretaryAdmin.objects.get(user=user)
        return secretary.is_active
    except SecretaryAdmin.DoesNotExist:
        return False