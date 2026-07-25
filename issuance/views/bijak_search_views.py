from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from ..models import Bijak


@login_required
def search_shipment(request):
    template_name = "issuance/search/search.html"

    q = request.GET.get('q', '').strip()

    # بهینه‌سازی کوئری با select_related برای کاهش تعداد queryهای دیتابیس
    bijaks = Bijak.objects.select_related(
        'sender',
        'receiver',
        'driver',
        'vehicle',
        'cargo'
    ).all().order_by('-created_at')

    if q:
        words = q.split()

        for word in words:
            bijaks = bijaks.filter(
                Q(tracking_code__icontains=word) |

                Q(sender__name__icontains=word) |
                Q(receiver__name__icontains=word) |

                Q(cargo__name__icontains=word) |
                Q(cargo__destination__icontains=word) |

                Q(driver__name__icontains=word) |

                Q(vehicle__license_plate_two_digit__icontains=word) |
                Q(vehicle__license_plate_alphabet__icontains=word) |
                Q(vehicle__license_plate_three_digit__icontains=word) |
                Q(vehicle__license_plate_series__icontains=word)
            )

        bijaks = bijaks.distinct()

    context = {
        "bijaks": bijaks,
        "search_query": q
    }

    return render(request, template_name, context)




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
