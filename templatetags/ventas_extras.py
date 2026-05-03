# ventas/templatetags/ventas_extras.py
from django import template

register = template.Library()

@register.filter
def sum_attr(items, attr_name):
    """
    Suma un atributo de una lista de objetos
    Uso: {{ lista|sum_attr:'total_usd' }}
    """
    total = 0
    if not items:
        return total
    
    for item in items:
        try:
            value = getattr(item, attr_name, 0)
            if value is None:
                value = 0
            total += float(value) if hasattr(value, '__float__') else 0
        except (TypeError, ValueError):
            pass
    return total

@register.filter
def sum_dict_attr(items, attr_name):
    """
    Suma un atributo de una lista de diccionarios
    Uso: {{ lista|sum_dict_attr:'total_usd' }}
    """
    total = 0
    if not items:
        return total
    
    for item in items:
        try:
            value = item.get(attr_name, 0)
            if value is None:
                value = 0
            total += float(value) if hasattr(value, '__float__') else 0
        except (TypeError, ValueError):
            pass
    return total
