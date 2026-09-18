from django.contrib import admin

from .models import Caption


@admin.register(Caption)
class CaptionAdmin(admin.ModelAdmin):
    list_display = ("name", "short_content", "created_at", "updated_at")
    search_fields = ("name", "content")
    list_per_page = 30

    @admin.display(description="محتوای توضیح")
    def short_content(self, obj):
        return (obj.content or "")[:60]

