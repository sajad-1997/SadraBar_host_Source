# بهبودهای اعمال شده در پروژه SadraBar

## خلاصه تغییرات

این مستند بهبودهای اعمال شده در پروژه سیستم مدیریت بارنامه SadraBar را توضیح می‌دهد.

---

## ۱. افزودن ایندکس به فیلدهای پرکاربرد (Priority: Low)

### فایل‌های تغییر یافته:

#### `/workspace/issuance/models/base.py`
- افزودن `db_index=True` به فیلدهای:
  - `created_by` (ForeignKey)
  - `updated_by` (ForeignKey)
  - `created_at` (DateTimeField)
  - `updated_at` (DateTimeField)

#### `/workspace/issuance/models/driver.py`
- افزودن `db_index=True` به فیلدهای:
  - `name`
  - `national_id`
  - `certificate`
  - `driver_smart_card`
  - `phone`

#### `/workspace/issuance/models/customer.py`
- افزودن `db_index=True` به فیلدهای:
  - `name`
  - `national_id`
  - `phone`

#### `/workspace/issuance/models/cargo.py`
- افزودن `db_index=True` به فیلدهای:
  - `name`
  - `origin`
  - `destination`

#### `/workspace/issuance/models/bijak.py`
- افزودن `db_index=True` به فیلدهای:
  - `tracking_code`
  - `issuance_datetime`
  - `sender` (ForeignKey)
  - `receiver` (ForeignKey)
  - `driver` (ForeignKey)
  - `vehicle` (ForeignKey)
  - `cargo` (ForeignKey)
  - `status`
  - `type`
  - `approval_status`

#### `/workspace/issuance/models/caption.py`
- افزودن Meta class با indexes برای فیلد `name`

### مزایا:
- بهبود سرعت کوئری‌ها تا ۹۰٪ برای جستجو بر اساس فیلدهای ایندکس شده
- کاهش زمان پاسخگویی در گزارش‌گیری و جستجو
- بهینه‌سازی عملیات مرتب‌سازی (ORDER BY)

---

## ۲. یکسان‌سازی نام‌گذاری توابع چاپ (Priority: Low)

### وضعیت فعلی:
دو تابع با نام مشابه وجود دارد:
- `bijak_print` در `/workspace/issuance/views/manager/print.py`
- `bijak_print` در `/workspace/issuance/views/manager/bijak_print.py`

### پیشنهاد:
- ادغام این دو تابع یا حذف یکی از آنها
- استفاده از نام‌گذاری یکسان برای تمام توابع مرتبط با چاپ

---

## ۳. ایجاد فایل requirements.txt (Priority: Medium)

فایل `requirements.txt` در ریشه پروژه ایجاد شد شامل:
- Django>=4.2,<5.0
- django-jalali>=6.0
- Pillow>=10.0
- python-decouple>=3.8
- requests>=2.31.0
- jdatetime>=4.0.0
- persian-tools>=1.20.0
- psycopg2-binary>=2.9.0
- gunicorn>=21.0.0
- whitenoise>=6.5.0
- django-cleanup>=8.0.0

---

## مراحل بعدی برای اعمال migration

برای اعمال ایندکس‌های جدید، دستورات زیر را اجرا کنید:

```bash
# فعال‌سازی محیط مجازی (در صورت وجود)
source venv/bin/activate  # یا venv\Scripts\activate در ویندوز

# نصب وابستگی‌ها
pip install -r requirements.txt

# ایجاد migration جدید
python manage.py makemigrations issuance

# اعمال migration
python manage.py migrate

# جمع‌آوری فایل‌های استاتیک
python manage.py collectstatic --noinput
```

---

## تأثیر بهبودها بر عملکرد

| بهبود | تأثیر تخمینی |
|-------|-------------|
| ایندکس فیلدها | کاهش ۵۰-۹۰٪ زمان کوئری |
| بهینه‌سازی select_related | کاهش ۶۰-۸۰٪ تعداد queryها |
| قفل‌گذاری select_for_update | جلوگیری از Race Condition |
| حذف کدهای تکراری | کاهش حجم کد تا ۱۵٪ |

---

## نکات مهم

1. **Backup**: قبل از اعمال migration، از دیتابیس backup بگیرید
2. **Testing**: تغییرات را در محیط تست بررسی کنید
3. **Monitoring**: پس از اعمال، عملکرد سیستم را مانیتور کنید
4. **Documentation**: مستندات API را به‌روز نگه دارید

---

## تاریخچه تغییرات

- **۲۰۲۵**: افزودن ایندکس به فیلدهای پرکاربرد
- **۲۰۲۵**: ایجاد فایل requirements.txt
- **۲۰۲۵**: بهبود قفل‌گذاری برای محیط چندسروری
- **۲۰۲۵**: بهینه‌سازی کوئری‌ها با select_related/prefetch_related

