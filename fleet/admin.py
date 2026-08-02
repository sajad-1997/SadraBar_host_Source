from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'license_plate', 
        'type', 
        'driver', 
        'vehicle_smart_card',
        'created_at'
    )
    list_filter = ('type', 'room_model', 'Animal_feed_license')
    search_fields = (
        'license_plate_two_digit',
        'license_plate_alphabet',
        'license_plate_three_digit',
        'license_plate_series',
        'vehicle_smart_card',
        'driver__name',
        'driver__national_id',
    )
    ordering = ('-id',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
