from django import template

register = template.Library()


@register.filter
def filter_by_status(queryset, status):
    return queryset.filter(status=status)


@register.filter
def get_item(dictionary, key):
    """
    Allows dictionary access in templates.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0
