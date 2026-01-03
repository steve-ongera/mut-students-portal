from django import template

register = template.Library()


@register.filter
def split(value, delimiter=","):
    if value:
        return value.split(delimiter)
    return []


@register.filter
def get_item(value, key):
    """
    Works for:
    - dict → value[key]
    - list → value[index]
    """
    try:
        if isinstance(value, dict):
            return value.get(key)
        elif isinstance(value, (list, tuple)):
            return value[int(key)]
    except (KeyError, IndexError, ValueError, TypeError):
        return None
