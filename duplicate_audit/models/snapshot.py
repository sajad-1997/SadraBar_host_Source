from django.db import models

from .cluster import DuplicateCluster

TYPE_CHOICES = [
    ('draft', 'پیش‌نویس'),
    ('sent', 'ارسال شده'),
    ('delivered', 'تحویل شده'),
    ('canceled', 'لغو شده'),
    ('inactive', 'غیر فعال'),
]


class DuplicateWaybillSnapshot(models.Model):
    cluster = models.ForeignKey(DuplicateCluster, on_delete=models.CASCADE, related_name="snapshots")

    original_waybill_id = models.IntegerField()
    tracking_code = models.CharField(max_length=100)
    issuer_name = models.CharField(max_length=255)
    sender_name = models.CharField(max_length=255)
    receiver_name = models.CharField(max_length=255)
    driver_name = models.CharField(max_length=255)
    cargo_name = models.CharField(max_length=255)
    cargo_weight = models.CharField(max_length=5)
    freight_amount = models.CharField(max_length=15)
    cargo_value = models.CharField(max_length=15)
    loading_cost = models.CharField(max_length=15)
    unloading_cost = models.CharField(max_length=15)
    scale_cost = models.CharField(max_length=15)
    description = models.TextField(blank=True, null=True)

    final_decision = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES + [('customer_copy', 'نسخه مشتری'), ('inactive_duplicate', 'تکراری-غیرفعال')],
        blank=True, null=True
    )

    customer_id = models.IntegerField(blank=True, null=True)  # برای نسخه مشتری

    def __str__(self):
        return f"Snapshot {self.original_waybill_id} in Cluster {self.cluster.id}"
