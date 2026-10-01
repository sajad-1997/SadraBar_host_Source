from django.contrib import admin

from .models import (
    CommissionDebt,
    DriverAttendance,
    DriverLocation,
    RateCard,
    ServiceRequest,
    ServiceRequestStatusLog,
    UrbanCustomerProfile,
    UrbanService,
)


@admin.register(UrbanService)
class UrbanServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'commission_percent', 'base_fare', 'per_km_fare', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    search_fields = ('title',)


@admin.register(RateCard)
class RateCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'service', 'vehicle_type', 'base_fare', 'per_km_fare',
                    'minimum_fare', 'commission_percent', 'is_active')
    list_filter = ('is_active', 'vehicle_type', 'service')
    search_fields = ('title',)


@admin.register(UrbanCustomerProfile)
class UrbanCustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_at', 'updated_at')
    search_fields = ('customer__name', 'customer__phone')


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'customer', 'status', 'assigned_driver',
                    'fare_amount', 'commission_amount', 'commission_paid', 'created_at')
    list_filter = ('status', 'commission_paid', 'service')
    search_fields = ('tracking_code', 'customer__name')
    readonly_fields = ('tracking_code',)


@admin.register(ServiceRequestStatusLog)
class ServiceRequestStatusLogAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'from_status', 'to_status', 'changed_by', 'created_at')
    list_filter = ('to_status',)


@admin.register(DriverAttendance)
class DriverAttendanceAdmin(admin.ModelAdmin):
    list_display = ('driver', 'date', 'status', 'check_in', 'check_out')
    list_filter = ('status', 'date')
    search_fields = ('driver__name',)


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ('driver', 'status', 'lat', 'lng', 'current_request', 'updated_at')
    list_filter = ('status',)


@admin.register(CommissionDebt)
class CommissionDebtAdmin(admin.ModelAdmin):
    list_display = ('driver', 'service_request', 'amount', 'paid_amount',
                    'is_settled', 'created_at')
    list_filter = ('is_settled',)
    search_fields = ('driver__name',)
