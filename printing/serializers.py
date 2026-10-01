"""
Serializers for printing app using Django REST Framework.
Standardized with type hints and PEP8 compliance.
"""
from typing import Any, Dict

from rest_framework import serializers

from issuance.models import Bijak
from .models import WaybillPrintOTP


class WaybillPrintOTPSerializer(serializers.ModelSerializer):
    """Serializer for WaybillPrintOTP model."""

    waybill_number = serializers.CharField(
        source='bijak.tracking_code',
        read_only=True
    )
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = WaybillPrintOTP
        fields = [
            'id',
            'waybill_number',
            'print_count',
            'last_print_time',
            'last_print_by',
            'is_verified',
            'is_expired',
        ]
        read_only_fields = fields

    def get_is_expired(self, obj: WaybillPrintOTP) -> bool:
        """Check if OTP is expired."""
        return obj.is_otp_expired()


class RequestOTPSerializer(serializers.Serializer):
    """Serializer for requesting OTP."""

    bijak_id = serializers.IntegerField(min_value=1)

    def validate_bijak_id(self, value: int) -> int:
        """Validate that bijak exists."""
        if not Bijak.objects.filter(id=value).exists():
            raise serializers.ValidationError('بارنامه یافت نشد.')
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP."""

    bijak_id = serializers.IntegerField(min_value=1)
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate_bijak_id(self, value: int) -> int:
        """Validate that bijak exists."""
        if not Bijak.objects.filter(id=value).exists():
            raise serializers.ValidationError('بارنامه یافت نشد.')
        return value
