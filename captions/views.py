from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache

from .forms import CaptionForm
from .models import Caption
from .utils import normalize_caption


def _get_role(user):
    """استخراج نقش کاربر (مطابق الگوی UserTrackingModel سایر ماژول‌ها)"""
    if not user:
        return None

    get_role = getattr(user, "get_role_display", None)
    if callable(get_role):
        try:
            return get_role()
        except Exception:
            pass

    for attr in ("role", "role_name"):
        if hasattr(user, attr):
            try:
                return str(getattr(user, attr))
            except Exception:
                pass
    return None


def _safe_next_url(request):
    """دریافت آدرس بازگشت امن (برای جلوگیری از open redirect)"""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return None


@login_required
@never_cache
def caption_list(request):
    """لیست تمام توضیحات آماده با امکان جستجو"""
    query = request.GET.get("q", "").strip()
    captions = Caption.objects.all().order_by("-id")

    if query:
        captions = captions.filter(
            Q(name__icontains=query) | Q(content__icontains=query)
        )

    return render(
        request,
        "captions/caption_list.html",
        {"captions": captions, "query": query},
    )


@login_required
@never_cache
def add_caption(request):
    """افزودن توضیح آماده جدید"""
    form = CaptionForm(request.POST or None)
    next_url = _safe_next_url(request)

    if request.method == "POST" and form.is_valid():
        content = form.cleaned_data.get("content") or ""

        # جلوگیری از ثبت توضیح تکراری (مقایسه بر اساس متن نرمال‌شده)
        normalized_input = normalize_caption(content)
        for caption in Caption.objects.filter(content__isnull=False):
            if normalize_caption(caption.content) == normalized_input:
                messages.warning(
                    request,
                    "این توضیح قبلاً ثبت شده است. لطفاً از لیست توضیحات آماده انتخاب کنید."
                )
                break
        else:
            caption = form.save(commit=False)
            caption.created_by = request.user
            caption.created_by_role = _get_role(request.user)
            caption.updated_by = request.user
            caption.updated_by_role = _get_role(request.user)
            caption.save()
            messages.success(request, "توضیح آماده با موفقیت ثبت شد.")
            return redirect(next_url or "captions:caption_list")

        return redirect(next_url or "captions:caption_list")

    return render(
        request,
        "captions/add_caption.html",
        {
            "form": form,
            "next": request.GET.get("next", ""),
            "back_url": next_url or "/captions/",
        },
    )


@login_required
@never_cache
def edit_caption(request, caption_id):
    """ویرایش توضیح آماده موجود"""
    caption = get_object_or_404(Caption, pk=caption_id)
    form = CaptionForm(request.POST or None, instance=caption)
    next_url = _safe_next_url(request)

    if request.method == "POST" and form.is_valid():
        caption = form.save(commit=False)
        caption.updated_by = request.user
        caption.updated_by_role = _get_role(request.user)
        caption.save()
        messages.success(request, "توضیح آماده با موفقیت ویرایش شد.")
        return redirect(next_url or "captions:caption_list")

    return render(
        request,
        "captions/edit_caption.html",
        {
            "form": form,
            "caption": caption,
            "next": request.GET.get("next", ""),
            "back_url": next_url or "/captions/",
        },
    )


@login_required
@never_cache
def search_caption(request):
    """جستجوی زنده توضیحات آماده (JSON API برای فرم‌های ماژول‌های دیگر)"""
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    captions = (
        Caption.objects.filter(
            Q(name__icontains=query) | Q(content__icontains=query)
        )
        .order_by("-id")[:20]
    )

    results = [
        {
            "id": caption.id,
            "name": caption.name,
            "content": caption.content,
        }
        for caption in captions
    ]

    return JsonResponse({"results": results})

