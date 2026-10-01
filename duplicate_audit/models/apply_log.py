from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class DuplicateApplyLog(models.Model):
    original_waybill_id = models.IntegerField()
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    old_tracking_code = models.CharField(max_length=100, null=True, blank=True)
    new_tracking_code = models.CharField(max_length=100, null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
