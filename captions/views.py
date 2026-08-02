from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .forms import CaptionForm
from .models import Caption


@login_required
@never_cache
def caption_list(request):
    """لیست تمام توضیحات"""
    captions = Caption.objects.all().order_by("-id")

    # فیلترها
    name = request.GET.get("name")

    if name:
        captions = captions.filter(name__icontains=name)

    context = {
        "captions": captions,
        "filters": request.GET
    }
    return render(request, "captions/caption_list.html", context)


@login_required
@never_cache
def add_caption(request):
    """افزودن توضیح جدید"""
    form = CaptionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'توضیح جدید با موفقیت ثبت شد')
            return redirect('captions:caption_list')

    return render(request, 'captions/add_caption.html', {
        'form': form
    })


@login_required
@never_cache
def edit_caption(request, caption_id):
    """ویرایش اطلاعات توضیح"""
    caption = get_object_or_404(Caption, pk=caption_id)
    form = CaptionForm(request.POST or None, instance=caption)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            now = timezone.now()

            # مدیریت تاریخ ایجاد و بروزرسانی
            if not getattr(instance, 'created_at', None):
                instance.created_at = now
            instance.updated_at = now

            if not getattr(instance, 'created_by', None):
                instance.created_by = request.user
            instance.updated_by = request.user

            instance.save()
            messages.success(request, "اطلاعات توضیح با موفقیت ذخیره شد.")
            return redirect('captions:caption_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return render(request, 'captions/edit_caption.html', {'form': form, 'caption': caption})


@login_required
@never_cache
def search_caption(request):
    """جستجوی توضیح برای استفاده در فرم‌های دیگر"""
    q = request.GET.get('q', '')
    captions = Caption.objects.filter(content__icontains=q)[:15]
    return JsonResponse({
        'results': list(captions.values('id', 'name', 'content'))
    })
