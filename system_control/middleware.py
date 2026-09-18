from django.shortcuts import render

from .services import user_can_access_path


class ModuleAccessMiddleware:
    """مسدود کردن دسترسی کاربران (غیر سوپر ادمین) به ماژول‌های قفل‌شده.

    سوپر ادمین همیشه دسترسی کامل دارد؛ سایر کاربران در صورت قفل بودن
    ماژول (قفل کامل، قفل نقش یا دسترسی اختصاصی deny) با صفحه 403 مواجه می‌شوند.
    """

    EXEMPT_PREFIXES = (
        '/admin', '/static/', '/media/', '/accounts/', '/forbidden',
        '/system-control', '/sw.js', '/manifest.webmanifest',
        '/offline/', '/browserconfig.xml', '/favicon',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method != 'OPTIONS':
            user = getattr(request, 'user', None)
            if user and user.is_authenticated and not user.is_superuser:
                path = request.path
                if not path.startswith(self.EXEMPT_PREFIXES):
                    try:
                        allowed, reason = user_can_access_path(user, path)
                    except Exception:
                        # در صورت بروز خطا، دسترسی را نمی‌بندیم تا سیستم از کار نیفتد
                        allowed, reason = True, ''
                    if not allowed:
                        return render(
                            request, 'errors/403.html',
                            {'error_message': reason},
                            status=403,
                        )
        return self.get_response(request)
