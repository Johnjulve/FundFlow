from django import template

register = template.Library()

@register.filter
def min_value(value, arg):
    """Returns the minimum of value and arg"""
    try:
        return min(float(value), float(arg))
    except (ValueError, TypeError):
        return value
