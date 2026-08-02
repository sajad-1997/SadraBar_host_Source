# otp_verification/models.py
from django.db import models
from django.utils import timezone
from issuance.models import Bijak
from drivers.models import Driver


class OTPCode(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    waybill = models.ForeignKey(Bijak, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['driver', 'waybill'])]
        verbose_name = "OTP Code"
        verbose_name_plural = "OTP Codes"

    def __str__(self):
        return f"{self.driver} - {self.code}"


class OTPLog(models.Model):
    action = models.CharField(max_length=50)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True)
    waybill = models.ForeignKey(Bijak, on_delete=models.SET_NULL, null=True)
    code = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=50, default="INFO")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "OTP Log"
        verbose_name_plural = "OTP Logs"

    def __str__(self):
        return f"{self.action} ({self.status})"
