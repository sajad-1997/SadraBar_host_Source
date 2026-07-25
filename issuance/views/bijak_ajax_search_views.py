from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q, Case, When, IntegerField, Value, Sum

from ..models import Bijak


@login_required
def ajax_search_shipment(request):
    q = request.GET.get("q", "").strip()

    bijaks = Bijak.objects.none()

    if q:
        # جدا کردن کلمات (تهران احمدی ۱۲۳)
        terms = [t for t in q.split() if len(t) >= 2]

        # بهینه‌سازی کوئری با select_related برای کاهش تعداد queryهای دیتابیس
        queryset = Bijak.objects.select_related(
            'sender',
            'receiver',
            'driver',
            'vehicle',
            'cargo'
        ).all()

        # 1️⃣ همه کلمات باید وجود داشته باشند (AND)
        for term in terms:
            queryset = queryset.filter(
                Q(tracking_code__icontains=term) |
                Q(sender__name__icontains=term) |
                Q(receiver__name__icontains=term) |
                Q(cargo__name__icontains=term) |
                Q(cargo__origin__icontains=term) |
                Q(cargo__destination__icontains=term) |
                Q(driver__name__icontains=term) |
                Q(vehicle__license_plate_two_digit__icontains=term) |
                Q(vehicle__license_plate_alphabet__icontains=term) |
                Q(vehicle__license_plate_three_digit__icontains=term) |
                Q(vehicle__license_plate_series__icontains=term)
            )

        # 2️⃣ امتیازدهی برای مرتب‌سازی نتایج
        score_cases = []

        for term in terms:
            score_cases.append(
                Case(
                    When(tracking_code__icontains=term, then=Value(10)),
                    When(sender__name__icontains=term, then=Value(6)),
                    When(receiver__name__icontains=term, then=Value(6)),
                    When(driver__name__icontains=term, then=Value(5)),
                    When(cargo__name__icontains=term, then=Value(4)),
                    When(cargo__origin__icontains=term, then=Value(3)),
                    When(cargo__destination__icontains=term, then=Value(3)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )

        queryset = (
            queryset
            .annotate(score=Sum(*score_cases))
            .filter(score__gt=0)
            .order_by("-score", "-created_at")
            .distinct()[:50]
        )

        bijaks = queryset

    html = render_to_string(
        "issuance/search/partials/bijak_list.html",
        {"bijaks": bijaks},
        request=request
    )

    return JsonResponse({"html": html})
