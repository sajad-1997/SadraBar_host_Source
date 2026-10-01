from datetime import datetime

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET


APP_NAME = "صدرابار خراسان"
APP_SHORT_NAME = "صدرابار"
THEME_COLOR = "#0f766e"
BACKGROUND_COLOR = "#f8fafc"


def _absolute_static(path):
    return static(path)


@cache_control(max_age=3600, public=True)
def manifest(request):
    icons = [
        {
            "src": _absolute_static(f"pwa/icons/icon-{size}x{size}.png"),
            "sizes": f"{size}x{size}",
            "type": "image/png",
            "purpose": "any",
        }
        for size in (72, 96, 128, 144, 152, 192, 384, 512)
    ]
    maskable_icons = [
        {
            "src": _absolute_static(f"pwa/icons/icon-{size}x{size}.png"),
            "sizes": f"{size}x{size}",
            "type": "image/png",
            "purpose": "maskable",
        }
        for size in (192, 512)
    ]

    data = {
        "id": "/",
        "name": APP_NAME,
        "short_name": APP_SHORT_NAME,
        "description": "سامانه حمل و نقل، صدور بارنامه، نوبت دهی رانندگان و پیگیری بار صدرابار خراسان.",
        "start_url": "/?source=pwa",
        "scope": "/",
        "display": "standalone",
        "display_override": ["window-controls-overlay", "standalone", "minimal-ui", "browser"],
        "orientation": "portrait-primary",
        "lang": "fa-IR",
        "dir": "rtl",
        "theme_color": THEME_COLOR,
        "background_color": BACKGROUND_COLOR,
        "categories": ["business", "productivity", "transportation"],
        "icons": icons + maskable_icons,
        "shortcuts": [
            {
                "name": "پیگیری بار",
                "short_name": "پیگیری",
                "description": "مشاهده وضعیت و پیگیری مرسوله",
                "url": reverse("tracking"),
                "icons": [{"src": _absolute_static("pwa/icons/icon-192x192.png"), "sizes": "192x192"}],
            },
            {
                "name": "نوبت دهی رانندگان",
                "short_name": "نوبت دهی",
                "description": "ورود به سامانه نوبت دهی رانندگان",
                "url": reverse("driver_queue:landing"),
                "icons": [{"src": _absolute_static("pwa/icons/icon-192x192.png"), "sizes": "192x192"}],
            },
            {
                "name": "پنل کاربری",
                "short_name": "پنل",
                "description": "ورود به پنل کاربری صدرابار",
                "url": reverse("go_dashboard"),
                "icons": [{"src": _absolute_static("pwa/icons/icon-192x192.png"), "sizes": "192x192"}],
            },
        ],
        "prefer_related_applications": False,
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})


@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    context = {
        "debug": settings.DEBUG,
        "version": getattr(settings, "PWA_CACHE_VERSION", "2026-09-29-1"),
        "offline_url": reverse("pwa_offline"),
        "queued_url": reverse("pwa_queued"),
        "ping_url": reverse("pwa_sync_ping"),
        "sync_tag": getattr(settings, "PWA_SYNC_TAG", "sadrabar-outbox-sync"),
        "sync_max_attempts": getattr(settings, "PWA_SYNC_MAX_ATTEMPTS", 40),
        "sync_retry_delay_ms": getattr(settings, "PWA_SYNC_RETRY_DELAY_MS", 700),
        "static_urls": [
            _absolute_static("pwa/pwa.css"),
            _absolute_static("pwa/pwa.js"),
            _absolute_static("pwa/offline.css"),
            _absolute_static("pwa/icons/icon-192x192.png"),
            _absolute_static("pwa/icons/icon-512x512.png"),
            _absolute_static("homePage/css/style.css"),
            _absolute_static("dashboard/css/style.css"),
            _absolute_static("issuance/css/main.css"),
            _absolute_static("issuance/css/page_link_style.css"),
        ],
    }
    
    response = render(
        request,
        "pwa/sw.js.jinja",
        context,
        content_type="application/javascript; charset=utf-8",
    )
    response["Service-Worker-Allowed"] = "/"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@cache_control(max_age=3600, public=True)
def offline(request):
    return render(request, "pwa/offline.html", status=503)


@cache_control(max_age=3600, public=True)
def queued(request):
    """
    صفحه «در صف همگام‌سازی».
    سرویس‌ورکر وقتی فرمی در حالت آفلاین ثبت می‌شود، این صفحه را (از کش) به کاربر
    نشان می‌دهد و درخواست اصلی را در صف IndexedDB برای ارسال بعدی نگه می‌دارد.
    """
    return render(request, "pwa/queued.html")


@require_GET
@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def sync_ping(request):
    """
    پینگ سبک برای تشخیص اتصال واقعی به سرور (navigator.onLine کافی نیست؛
    مثلاً در وای‌فای بی‌اینترنت true برمی‌گرداند). سرویس‌ورکر این مسیر را
    هیچ‌وقت کش نمی‌کند تا پاسخ همیشه از شبکه باشد.
    """
    return JsonResponse(
        {
            "ok": True,
            "server_time": datetime.now().isoformat(timespec="seconds"),
            "version": getattr(settings, "PWA_CACHE_VERSION", ""),
        }
    )


@require_GET
def sync_status(request):
    """
    بررسی وضعیت همگام‌سازی از سمت کلاینت (تعداد درخواست‌های در صف).
    این endpoint برای نمایش وضعیت به کاربر استفاده می‌شود.
    """
    return JsonResponse(
        {
            "ok": True,
            "message": "Sync status endpoint - client should check IndexedDB for pending items",
        }
    )


def browserconfig(request):
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
  <msapplication>
    <tile>
      <square150x150logo src="{_absolute_static('pwa/icons/icon-152x152.png')}"/>
      <TileColor>{THEME_COLOR}</TileColor>
    </tile>
  </msapplication>
</browserconfig>"""
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
