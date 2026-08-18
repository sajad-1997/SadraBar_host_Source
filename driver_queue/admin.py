from django.contrib import admin
from django.utils import timezone

from . import services
from .models import (Announcement, QueueLog, QueueProfile, QueueStaff, QueueTicket)


@admin.register(QueueProfile)
class QueueProfileAdmin(admin.ModelAdmin):
    list_display = ("driver", "office_approved", "registered_via_queue", "created_at")
    list_filter = ("office_approved", "registered_via_queue")
    search_fields = ("driver__name", "driver__national_id")
    raw_id_fields = ("driver",)

    @admin.action(description="تایید رانندگان انتخاب‌شده")
    def approve_drivers(self, request, queryset):
        queryset.update(office_approved=True)

    actions = ["approve_drivers"]


@admin.register(QueueStaff)
class QueueStaffAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "approved", "approved_by", "created_at")
    list_filter = ("role", "approved")
    search_fields = ("user__username",)
    raw_id_fields = ("user", "approved_by")

    def save_model(self, request, obj, form, change):
        if obj.approved and obj.approved_by_id is None:
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ("driver", "date", "number", "status", "joined_at", "removed_at")
    list_filter = ("date", "status")
    search_fields = ("driver__name", "driver__national_id")

    @admin.action(description="خروج از صف و به‌روزرسانی شماره‌ها")
    def remove_from_queue(self, request, queryset):
        waiting = queryset.filter(status=QueueTicket.Status.WAITING)
        waiting.update(status=QueueTicket.Status.LEFT, removed_at=timezone.now())
        for day in set(waiting.values_list("date", flat=True)):
            services.renumber(day)

    actions = ["remove_from_queue"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("ticket", "day", "sent_at", "response", "responded_at")
    list_filter = ("day", "response")


@admin.register(QueueLog)
class QueueLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "driver", "created_at")
    list_filter = ("action",)
    search_fields = ("detail", "driver__name")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
