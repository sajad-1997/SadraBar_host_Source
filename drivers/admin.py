from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'national_id', 'phone', 'certificate', 'residence')
    search_fields = ('name', 'national_id', 'phone', 'certificate')
    list_filter = ('residence',)
    ordering = ('-id',)
