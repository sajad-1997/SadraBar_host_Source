# issuance/templatetags/filters.py
from django import template
from django.db.models import Q

register = template.Library()

@register.filter
def get_by_type(queryset, type_value):
    """
    فیلتر بارنامه‌ها بر اساس type
    - اگر type_value 'unassigned' باشد، رکوردهایی که type خالی یا NULL هستند
    - در غیر این صورت رکوردهایی که type برابر type_value
    """
    if type_value == 'unassigned':
        return queryset.filter(Q(type__isnull=True) | Q(type=''))
    return queryset.filter(type=type_value)