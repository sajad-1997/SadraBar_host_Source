# issuance/templatetags/user_tags.py
from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    """بررسی می‌کند که کاربر عضو گروه خاصی هست یا نه"""
    return user.groups.filter(name=group_name).exists()
