import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_via_smsir(phone_number, code):
    """
    ارسال کد تأیید از طریق API جدید sms.ir (متد verify)
    """
    if settings.SMS_IR_FAKE_MODE:
        # print(f"[FAKE] ارسال کد {code} به شماره {phone_number}")
        logger.info(f"FAKE MODE: OTP code {code} for {phone_number}")
        return True, "کد در حالت تست چاپ شد"

    # === نمایش کد تولید شده در ترمینال برای دیباگ ===
    # print(f"[DEBUG] کد تولید شده برای شماره {phone_number}: {code}")

    # === اصلاح شماره: حذف صفر ابتدایی (در صورت وجود) ===
    original_phone = phone_number
    if phone_number.startswith('09'):
        phone_number = phone_number[1:]  # 09123456789 -> 9123456789
        # print(f"[DEBUG] شماره اصلاح شد: {original_phone} -> {phone_number}")

    url = "https://api.sms.ir/v1/send/verify"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "x-api-key": settings.SMS_IR_API_KEY
    }

    # توجه: نام پارامتر ('name') باید دقیقاً با متغیر تعریف شده در الگوی پنل مطابقت داشته باشد
    # در اینجا 'Code' فرض شده است. در صورت نیاز به 'code' یا غیره تغییر دهید.
    payload = {
        "mobile": phone_number,
        "templateId": int(settings.SMS_IR_PATTERN_CODE),
        "parameters": [
            {"name": "OTP", "value": str(code)}
        ]
    }

    # در صورت وجود شماره خط، به payload اضافه کنید (اختیاری)
    if hasattr(settings, 'SMS_IR_LINE_NUMBER') and settings.SMS_IR_LINE_NUMBER:
        payload["lineNumber"] = settings.SMS_IR_LINE_NUMBER

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # بررسی موفقیت بر اساس ساختار پاسخ sms.ir (status=1 یعنی موفق)
        if data.get("status") == 1:
            logger.info(f"SMS sent successfully. messageId: {data.get('data', {}).get('messageId')}")
            return True, "پیامک با موفقیت ارسال شد"
        else:
            error_msg = data.get("message", "خطای ناشناخته")
            logger.error(f"SMS.ir error: {data}")
            return False, error_msg

    except requests.exceptions.RequestException as e:
        logger.exception("خطا در ارتباط با sms.ir")
        return False, f"خطای شبکه: {str(e)}"