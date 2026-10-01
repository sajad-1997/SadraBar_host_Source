from django.contrib import admin
from .models import DriverBlock


@admin.register(DriverBlock)
class DriverBlockAdmin(admin.ModelAdmin):
    list_display = ['driver', 'is_blocked', 'blocked_at', 'blocked_by', 'unblocked_at']
    list_filter = ['is_blocked', 'blocked_at']
    search_fields = ['driver__username', 'driver__first_name', 'driver__last_name', 'block_reason']
    readonly_fields = ['blocked_at', 'unblocked_at']
