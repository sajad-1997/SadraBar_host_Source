import random
from django.core.cache import cache
from django.conf import settings

OTP_EXPIRE_SECONDS = 120  # 2 دقیقه
OTP_CACHE_PREFIX = "otp_"

def generate_otp(phone_number):
    """تولید کد ۶ رقمی و ذخیره در کش به ازای شماره تلفن"""
    code = str(random.randint(100000, 999999))
    cache_key = f"{OTP_CACHE_PREFIX}{phone_number}"
    cache.set(cache_key, code, timeout=OTP_EXPIRE_SECONDS)
    return code

def verify_otp(phone_number, entered_code):
    """بررسی صحت کد وارد شده"""
    cache_key = f"{OTP_CACHE_PREFIX}{phone_number}"
    stored_code = cache.get(cache_key)
    if stored_code and stored_code == entered_code:
        # پس از تأیید موفق، کد را حذف می‌کنیم
        cache.delete(cache_key)
        return True
    return False