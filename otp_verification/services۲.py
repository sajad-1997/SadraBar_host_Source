import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_via_smsir(phone_number, code):
    """
    ارسال کد OTP از طریق API الگو (Pattern) sms.ir
    اگر حالت fake فعال باشد، فقط در لاگ چاپ می‌کند.
    """
    if settings.SMS_IR_FAKE_MODE:
        # logger.info(f"[FAKE] ارسال کد {code} به شماره {phone_number}")
        # return True, "کد در حالت تست چاپ شد"
        # به جای logger از print استفاده کن
        print(f"[FAKE] ارسال کد {code} به شماره {phone_number}")
        return True, "کد در حالت تست چاپ شد"

    url = "https://api.sms.ir/send/pattern"
    headers = {
        "Authorization": f"Bearer {settings.SMS_IR_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "patternCode": settings.SMS_IR_PATTERN_CODE,
        "mobile": phone_number,
        "inputData": {"code": str(code)},
    }
    # در صورت نیاز به شماره خط مشخص:
    if hasattr(settings, 'SMS_IR_LINE_NUMBER') and settings.SMS_IR_LINE_NUMBER:
        payload["lineNumber"] = settings.SMS_IR_LINE_NUMBER

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("statusCode") == 200:
            return True, "پیامک با موفقیت ارسال شد"
        else:
            logger.error(f"SMS.ir error: {data}")
            return False, data.get("message", "خطا در ارسال")
    except Exception as e:
        logger.exception("مشکل در ارتباط با sms.ir")
        return False, str(e)