from django.db import models

from .base import UserTrackingModel


class Caption(UserTrackingModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    def __str__(self):
        return (self.content or "")[:50]
