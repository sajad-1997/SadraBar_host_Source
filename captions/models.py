from django.db import models
from django.conf import settings


class Caption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caption_created",
        db_index=True
    )
    created_by_role = models.CharField(max_length=50, blank=True, null=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caption_updated",
        db_index=True
    )
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return (self.content or "")[:50]

    class Meta:
        db_table = 'caption'
        indexes = [
            models.Index(fields=['name']),
        ]
