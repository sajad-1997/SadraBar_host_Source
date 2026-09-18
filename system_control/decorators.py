from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def superuser_required(view_func):
    """دسترسی به ماژول کنترل سیستم فقط برای سوپر ادمین (پنل ادمین)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'برای مشاهده این صفحه ابتدا وارد شوید.')
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, 'این بخش فقط از طریق پنل سوپر ادمین قابل دسترسی است.')
            return redirect('forbidden')
        return view_func(request, *args, **kwargs)

    return _wrapped
