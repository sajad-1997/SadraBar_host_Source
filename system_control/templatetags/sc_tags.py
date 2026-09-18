from django import template

from ..services import role_label

register = template.Library()


@register.filter(name='role_label')
def role_label_filter(code):
    """نام نمایشی نقش (استاندارد یا سفارشی)"""
    return role_label(code)


@register.filter(name='attr')
def attr_filter(obj, field_name):
    """دریافت مقدار یک فیلد از شیء با نام داینامیک"""
    return getattr(obj, field_name, False)
