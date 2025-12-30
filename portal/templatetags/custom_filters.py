# ============= TEMPLATETAGS/CUSTOM_FILTERS.PY =============
# Create templatetags folder with __init__.py and custom_filters.py

from django import template

register = template.Library()

@register.filter
def filter_by_status(queryset, status):
    """Filter queryset by status"""
    return queryset.filter(status=status)


from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Allows dictionary access in templates.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
