from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Cargo

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
