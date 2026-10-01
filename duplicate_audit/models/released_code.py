from django.db import models

from .cluster import DuplicateCluster


class ReleasedTrackingCode(models.Model):
    code = models.CharField(max_length=100)
    cluster = models.ForeignKey(DuplicateCluster, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
