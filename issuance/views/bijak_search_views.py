from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, IntegerField, Value, Sum
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render

from ..models import Bijak


@login_required
def search_shipment(request):
    """صفحه اصلی جستجوی بارنامه‌ها"""
    template_name = "issuance/search/search.html"
    
    q = request.GET.get('q', '').strip()
    
    # نمایش اولیه بدون کوئری خاص
    bijaks = Bijak.objects.select_related(
        'sender',
        'receiver',
        'driver',
        'vehicle',
        'cargo'
    ).all().order_by('-created_at')[:50]  # محدود کردن نتایج اولیه برای سرعت بیشتر
    
    context = {
        "bijaks": bijaks,
        "search_query": q
    }
    
    return render(request, template_name, context)


@login_required
def ajax_search_shipment(request):
    """جستجوی AJAX سریع بارنامه‌ها با امتیازدهی"""
    q = request.GET.get("q", "").strip()
    
    if not q:
        html = render_to_string(
            "issuance/search/partials/bijak_list.html",
            {"bijaks": []},
            request=request
        )
        return JsonResponse({"html": html, "count": 0})
    
    # جدا کردن کلمات کلیدی
    terms = [t for t in q.split() if len(t) >= 1]
    
    if not terms:
        html = render_to_string(
            "issuance/search/partials/bijak_list.html",
            {"bijaks": []},
            request=request
        )
        return JsonResponse({"html": html, "count": 0})
    
    # کوئری بهینه با select_related
    queryset = Bijak.objects.select_related(
        'sender',
        'receiver',
        'driver',
        'vehicle',
        'cargo'
    ).all()
    
    # فیلتر بر اساس تمام کلمات (AND logic)
    for term in terms:
        queryset = queryset.filter(
            # کد رهگیری
            Q(tracking_code__icontains=term) |
            
            # اطلاعات فرستنده
            Q(sender__name__icontains=term) |
            Q(sender__national_id__icontains=term) |
            Q(sender__address__icontains=term) |
            Q(sender__phone__icontains=term) |
            
            # اطلاعات گیرنده
            Q(receiver__name__icontains=term) |
            Q(receiver__national_id__icontains=term) |
            Q(receiver__address__icontains=term) |
            Q(receiver__phone__icontains=term) |
            
            # اطلاعات راننده
            Q(driver__name__icontains=term) |
            Q(driver__national_id__icontains=term) |
            Q(driver__phone__icontains=term) |
            Q(driver__certificate__icontains=term) |
            Q(driver__driver_smart_card__icontains=term) |
            
            # اطلاعات محموله
            Q(cargo__name__icontains=term) |
            Q(cargo__origin__icontains=term) |
            Q(cargo__destination__icontains=term) |
            
            # اطلاعات خودرو
            Q(vehicle__license_plate_two_digit__icontains=term) |
            Q(vehicle__license_plate_alphabet__icontains=term) |
            Q(vehicle__license_plate_three_digit__icontains=term) |
            Q(vehicle__license_plate_series__icontains=term) |
            Q(vehicle__vehicle_smart_card__icontains=term)
        )
    
    # امتیازدهی برای مرتب‌سازی هوشمند نتایج
    score_cases = []
    for term in terms:
        score_cases.append(
            Case(
                # تطابق دقیق کد رهگیری - بالاترین امتیاز
                When(tracking_code__iexact=term, then=Value(100)),
                When(tracking_code__icontains=term, then=Value(80)),
                
                # تطابق کد ملی فرستنده/گیرنده
                When(sender__national_id__iexact=term, then=Value(75)),
                When(receiver__national_id__iexact=term, then=Value(75)),
                
                # تطابق شماره ملی راننده
                When(driver__national_id__iexact=term, then=Value(70)),
                When(driver__certificate__iexact=term, then=Value(65)),
                When(driver__driver_smart_card__iexact=term, then=Value(65)),
                
                # تطابق نام‌ها
                When(sender__name__icontains=term, then=Value(50)),
                When(receiver__name__icontains=term, then=Value(50)),
                When(driver__name__icontains=term, then=Value(45)),
                
                # تطابق آدرس‌ها
                When(sender__address__icontains=term, then=Value(35)),
                When(receiver__address__icontains=term, then=Value(35)),
                
                # تطابق مبدا و مقصد
                When(cargo__origin__icontains=term, then=Value(40)),
                When(cargo__destination__icontains=term, then=Value(40)),
                
                # تطابق نام محموله
                When(cargo__name__icontains=term, then=Value(30)),
                
                # تطابق پلاک خودرو
                When(vehicle__license_plate_two_digit__icontains=term, then=Value(25)),
                When(vehicle__license_plate_three_digit__icontains=term, then=Value(25)),
                When(vehicle__license_plate_alphabet__icontains=term, then=Value(25)),
                When(vehicle__license_plate_series__icontains=term, then=Value(25)),
                
                default=Value(0),
                output_field=IntegerField()
            )
        )
    
    # اعمال امتیازدهی و مرتب‌سازی
    queryset = (
        queryset
        .annotate(score=Sum(*score_cases))
        .filter(score__gt=0)
        .order_by("-score", "-created_at")
        .distinct()[:100]  # محدود کردن به 100 نتیجه برتر
    )
    
    bijaks = queryset
    count = bijaks.count()
    
    html = render_to_string(
        "issuance/search/partials/bijak_list.html",
        {"bijaks": bijaks, "search_query": q},
        request=request
    )
    
    return JsonResponse({"html": html, "count": count})




# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render
# from django.db.models import Q

# from ..models import Bijak

# @login_required
# def search_shipment(request):
#     return render(
#         request,
#         "issuance/search/search.html",
#         {
#             "bijaks": []
#         }
#     )


# @login_required
# def search_shipment(request):
#     template_name = "issuance/search/search.html"

#     q = request.GET.get('q', '').strip()

#     bijaks = Bijak.objects.all().order_by('-created_at')

#     if q:
#         bijaks = bijaks.filter(
#             Q(tracking_code__icontains=q) |

#             Q(sender__name__icontains=q) |
#             Q(receiver__name__icontains=q) |

#             Q(cargo__origin__icontains=q) |
#             Q(cargo__destination__icontains=q) |
#             Q(cargo__name__icontains=q) |

#             Q(driver__name__icontains=q) |

#             Q(vehicle__license_plate_two_digit__icontains=q) |
#             Q(vehicle__license_plate_alphabet__icontains=q) |
#             Q(vehicle__license_plate_three_digit__icontains=q) |
#             Q(vehicle__license_plate_series__icontains=q)
#         ).distinct()

#     context = {
#         "bijaks": bijaks,
#         "search_query": q
#     }

#     return render(request, template_name, context)
