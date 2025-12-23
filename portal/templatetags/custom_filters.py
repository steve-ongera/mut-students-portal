# ============= TEMPLATETAGS/CUSTOM_FILTERS.PY =============
# Create templatetags folder with __init__.py and custom_filters.py

from django import template

register = template.Library()

@register.filter
def filter_by_status(queryset, status):
    """Filter queryset by status"""
    return queryset.filter(status=status)


