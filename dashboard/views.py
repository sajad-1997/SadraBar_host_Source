# dashboard/views.py
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import RolePermission


@role_required(['admin'])
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html', {'user': request.user})


@role_required(['manager'])
def manager_dashboard(request):
    permissions = None
    if request.user.role == 'manager':
        permissions = RolePermission.objects.filter(role='manager').first()

    return render(request, 'dashboard/manager_dashboard.html', {
        'user': request.user,
        'permissions': permissions
    })


@role_required(['staff', 'manager', 'admin'])
def staff_dashboard(request):
    permissions = None
    if request.user.role == 'staff':
        permissions = RolePermission.objects.filter(role='staff').first()

    return render(request, 'dashboard/staff_dashboard.html', {
        'user': request.user,
        'permissions': permissions
    })


@role_required(['staff', 'manager', 'admin'])
def home_dashboard(request):
    permissions = None
    if request.user.role == 'staff':
        permissions = RolePermission.objects.filter(role='staff').first()

    return render(request, 'dashboard/home_dashboard.html', {
        'user': request.user,
        'permissions': permissions
    })
