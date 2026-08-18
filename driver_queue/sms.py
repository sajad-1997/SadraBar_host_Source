"""
درگاه پیامک. برای اتصال به ارائه‌دهنده واقعی (کاوه‌نگار، قاصدک و...)
کلاسی هم‌سطح ConsoleSmsGateway بسازید و مسیرش را در
settings.QUEUE_SMS_GATEWAY قرار دهید.
"""
import logging
from importlib import import_module

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseSmsGateway:
    def send(self, phone: str, text: str):
        raise NotImplementedError


class ConsoleSmsGateway(BaseSmsGateway):
    """درگاه توسعه: پیامک را در لاگ/کنسول چاپ می‌کند."""

    def send(self, phone, text):
        logger.info("[SMS] -> %s\n%s", phone, text)
        print(f"[SMS] -> {phone}\n{text}\n" + "-" * 40)
        return "ok(console)"


def get_sms_gateway() -> BaseSmsGateway:
    path = getattr(settings, "QUEUE_SMS_GATEWAY", "driver_queue.sms.ConsoleSmsGateway")
    module_name, class_name = path.rsplit(".", 1)
    gateway_class = getattr(import_module(module_name), class_name)
    return gateway_class()