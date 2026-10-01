from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Cargo, City, Province

@login_required
def cargo_list(request):
    """لیست تمام محموله‌ها"""
    cargo_list = Cargo.objects.all().order_by("-id")
    return render(request, "cargo/cargo_list.html", {"cargo_list": cargo_list})

@login_required
def add_cargo(request):
    """افزودن محموله جدید"""
    return render(request, "cargo/add_cargo.html")

@login_required
def edit_cargo(request, cargo_id):
    """ویرایش محموله"""
    return render(request, "cargo/edit_cargo.html", {"cargo_id": cargo_id})

@login_required
def search_cargo(request):
    """جستجوی محموله"""
    return render(request, "cargo/search_cargo.html")

@login_required
def search_cargo_name(request):
    """جستجوی زنده نام محموله‌ها برای فرم صدور بارنامه (مشابه جستجوی فرستنده/گیرنده)"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    cargos = (
        Cargo.objects.filter(name__icontains=query)
        .order_by('name', 'id')
    )

    results = []
    seen_names = set()
    for cargo in cargos:
        # نام‌های تکراری فقط یک‌بار نمایش داده می‌شوند
        if cargo.name in seen_names:
            continue
        seen_names.add(cargo.name)
        results.append({
            'id': cargo.id,
            'name': cargo.name,
        })
        if len(results) >= 20:
            break

    return JsonResponse({'results': results})


@login_required
def search_city(request):
    """جستجوی شهر بر اساس نام شهر یا استان"""
    query = request.GET.get('q', '')
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    cities = City.objects.filter(
        Q(name__icontains=query) | Q(province__name__icontains=query)
    ).select_related('province')[:20]
    
    results = []
    for city in cities:
        results.append({
            'id': city.id,
            'name': city.name,
            'province': city.province.name,
            'display': f"{city.province.name} - {city.name}"
        })
    
    return JsonResponse({'results': results})
