from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Caption

@login_required
def caption_list(request):
    """لیست تمام کپشن‌ها"""
    captions = Caption.objects.all().order_by("-id")
    return render(request, "captions/caption_list.html", {"captions": captions})

@login_required
def add_caption(request):
    """افزودن کپشن جدید"""
    return render(request, "captions/add_caption.html")

@login_required
def edit_caption(request, caption_id):
    """ویرایش کپشن"""
    return render(request, "captions/edit_caption.html", {"caption_id": caption_id})

@login_required
def search_caption(request):
    """جستجوی کپشن"""
    return render(request, "captions/search_caption.html")
