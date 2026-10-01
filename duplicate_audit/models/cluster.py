from django.db import models


class DuplicateCluster(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Cluster {self.id} ({'Closed' if self.is_resolved else 'Open'})"
