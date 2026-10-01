from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import User, RolePermission
from accounts.decorators import role_required, get_user_permissions
from .models import DriverBlock


@login_required
@role_required(['admin', 'manager'])
def user_list(request):
    """لیست کاربران برای مدیریت"""
    permissions = get_user_permissions(request.user)
    
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(user_code__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    # دریافت وضعیت مسدودی برای رانندگان
    driver_blocks = DriverBlock.objects.select_related('driver').all()
    blocked_driver_ids = set(db.driver_id for db in driver_blocks if db.is_blocked)
    
    context = {
        'users': users,
        'permissions': permissions,
        'search_query': search_query,
        'role_filter': role_filter,
        'blocked_driver_ids': blocked_driver_ids,
    }
    return render(request, 'user_management/user_list.html', context)


@login_required
@role_required(['admin', 'manager'])
def user_detail(request, user_id):
    """جزئیات کاربر و مدیریت مجوزها"""
    permissions = get_user_permissions(request.user)
    
    user = get_object_or_404(User, id=user_id)
    
    # دریافت یا ایجاد مجوزهای نقش کاربر
    role_permission, created = RolePermission.objects.get_or_create(
        role=user.role
    )
    
    # اگر راننده است، وضعیت مسدودی را دریافت کن
    driver_block = None
    if user.role == 'driver':
        driver_block, _ = DriverBlock.objects.get_or_create(driver=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_permissions':
            # به‌روزرسانی مجوزهای نقش
            for field in RolePermission._meta.get_fields():
                if field.name.startswith('can_') and field.name != 'id' and field.name != 'role':
                    value = request.POST.get(field.name) == 'on'
                    setattr(role_permission, field.name, value)
            role_permission.save()
            messages.success(request, 'مجوزها با موفقیت به‌روزرسانی شد.')
            return redirect('user_management:user_detail', user_id=user.id)
        
        elif action == 'change_role':
            # تغییر نقش کاربر
            new_role = request.POST.get('new_role')
            if new_role and new_role in dict(User.ROLE_CHOICES):
                user.role = new_role
                user.save()
                messages.success(request, 'نقش کاربر با موفقیت تغییر یافت.')
                return redirect('user_management:user_detail', user_id=user.id)
        
        elif action == 'block_driver' and user.role == 'driver':
            # مسدود کردن راننده
            reason = request.POST.get('block_reason', '')
            driver_block.block(request.user, reason)
            messages.success(request, 'راننده با موفقیت مسدود شد.')
            return redirect('user_management:user_detail', user_id=user.id)
        
        elif action == 'unblock_driver' and user.role == 'driver':
            # رفع مسدودی راننده
            driver_block.unblock(request.user)
            messages.success(request, 'مسدودی راننده با موفقیت رفع شد.')
            return redirect('user_management:user_detail', user_id=user.id)
    
    context = {
        'user': user,
        'role_permission': role_permission,
        'driver_block': driver_block,
        'permissions': permissions,
    }
    return render(request, 'user_management/user_detail.html', context)


@login_required
@role_required(['admin', 'manager'])
def driver_block_list(request):
    """لیست رانندگان مسدود شده"""
    permissions = get_user_permissions(request.user)
    
    blocked_drivers = DriverBlock.objects.filter(
        is_blocked=True
    ).select_related('driver', 'blocked_by').order_by('-blocked_at')
    
    context = {
        'blocked_drivers': blocked_drivers,
        'permissions': permissions,
    }
    return render(request, 'user_management/driver_block_list.html', context)


@login_required
@role_required(['admin', 'manager'])
def user_management_dashboard(request):
    """داشبورد مدیریت کاربران"""
    permissions = get_user_permissions(request.user)
    
    # آمار کاربران
    total_users = User.objects.count()
    admin_count = User.objects.filter(role='admin').count()
    manager_count = User.objects.filter(role='manager').count()
    employee_count = User.objects.filter(role='employee').count()
    driver_count = User.objects.filter(role='driver').count()
    customer_count = User.objects.filter(role='customer').count()
    
    # آمار رانندگان مسدود شده
    blocked_driver_count = DriverBlock.objects.filter(is_blocked=True).count()
    
    # آخرین کاربران ثبت شده
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # رانندگان مسدود شده اخیر
    recent_blocked = DriverBlock.objects.filter(
        is_blocked=True
    ).select_related('driver', 'blocked_by').order_by('-blocked_at')[:5]
    
    context = {
        'permissions': permissions,
        'total_users': total_users,
        'admin_count': admin_count,
        'manager_count': manager_count,
        'employee_count': employee_count,
        'driver_count': driver_count,
        'customer_count': customer_count,
        'blocked_driver_count': blocked_driver_count,
        'recent_users': recent_users,
        'recent_blocked': recent_blocked,
    }
    return render(request, 'user_management/dashboard.html', context)
