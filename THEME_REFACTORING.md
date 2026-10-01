# سیستم تم سراسری - مستندات بازسازی

## خلاصه تغییرات

این پروژه شامل بازسازی کامل سیستم استایل‌ها و اسکریپت‌ها برای استفاده از یک سیستم تم سراسری با پشتیبانی از حالت تاریک و روشن در تمام ماژول‌های پروژه است.

## فایل‌های جدید ایجاد شده

### 1. فایل CSS سراسری
**مسیر:** `/static/global/css/theme.css`

این فایل شامل:
- متغیرهای CSS برای رنگ‌های تم روشن و تاریک
- استایل‌های مشترک برای کارت‌ها، فرم‌ها، جداول، دکمه‌ها و آلرت‌ها
- پشتیبانی از `prefers-color-scheme: dark` برای تشخیص خودکار تم سیستم
- پشتیبانی از کلاس `.dark-mode` برای تغییر دستی تم
- استایل‌های مخصوص هر ماژول (dashboard, city_drivers, driver_queue)

### 2. فایل JavaScript سراسری
**مسیر:** `/static/global/js/theme.js`

این فایل شامل:
- مدیریت خودکار تم بر اساس تنظیمات سیستم
- ذخیره ترجیح کاربر در localStorage
- تابع `toggleTheme()` برای تغییر دستی تم
- توابع کمکی مشترک:
  - `togglePassword()` برای نمایش/مخفی کردن رمز عبور
  - `validateForm()` برای اعتبارسنجی فرم‌ها
  - `setupAutoDismissAlerts()` برای بستن خودکار آلرت‌ها
  - `copyToClipboard()` برای کپی متن

## قالب‌های به‌روزرسانی شده

### قالب‌های پایه (Base Templates)

1. **dashboard/templates/dashboard/base.html**
   - حذف استایل‌های inline برای حالت تاریک
   - افزودن لینک به `global/css/theme.css`
   - افزودن اسکریپت `global/js/theme.js`

2. **issuance/templates/issuance/base.html**
   - حذف استایل‌های تکراری برای حالت تاریک
   - افزودن لینک به `global/css/theme.css`
   - افزودن اسکریپت `global/js/theme.js`

3. **city_drivers/templates/city_drivers/base.html**
   - افزودن لینک به `global/css/theme.css`
   - به‌روزرسانی `urban.css` برای استفاده از متغیرهای سراسری
   - افزودن اسکریپت `global/js/theme.js`

4. **driver_queue/templates/driver_queue/base.html**
   - به‌روزرسانی استایل‌ها برای استفاده از متغیرهای سراسری
   - افزودن لینک به `global/css/theme.css`
   - افزودن اسکریپت `global/js/theme.js`

5. **accounts/templates/accounts/login.html**
   - حذف اسکریپت inline برای toggle password
   - استفاده از تابع سراسری `togglePassword()`
   - افزودن اسکریپت `global/js/theme.js`

6. **report/templates/report/report_dashboard.html**
   - به‌روزرسانی متغیرهای CSS برای استفاده از متغیرهای سراسری
   - حذف استایل‌های تکراری برای حالت تاریک
   - افزودن لینک به `global/css/theme.css`
   - افزودن اسکریپت `global/js/theme.js`
   - به‌روزرسانی Chart.js برای استفاده از مدیریت تم سراسری

7. **system_control/templates/system_control/base.html**
   - حذف استایل‌های inline برای حالت تاریک
   - به‌روزرسانی برای استفاده از متغیرهای سراسری
   - افزودن لینک به `global/css/theme.css`
   - افزودن اسکریپت `global/js/theme.js`

8. **issuance/templates/issuance/search/base.html**
   - حذف کامل استایل‌های حالت تاریک (توسط global theme مدیریت می‌شود)
   - به‌روزرسانی تمام استایل‌ها برای استفاده از متغیرهای سراسری
   - افزودن لینک به `global/css/theme.css`
   - افزودن اسکریپت `global/js/theme.js`

9. **homePage/templates/homePage/base.html**
   - تغییر فونت به Vazirmatn (فونت سراسری)
   - افزودن لینک به `global/css/theme.css`
   - به‌روزرسانی رنگ پس‌زمینه و متن با متغیرهای سراسری
   - افزودن اسکریپت `global/js/theme.js`

## متغیرهای CSS سراسری

### رنگ‌های اصلی
- `--global-bg`: رنگ پس‌زمینه
- `--global-text`: رنگ متن اصلی
- `--global-card-bg`: رنگ پس‌زمینه کارت‌ها
- `--global-input-bg`: رنگ پس‌زمینه فیلدهای ورودی
- `--global-border`: رنگ حاشیه‌ها
- `--global-muted`: رنگ متن مات/کم‌رنگ

### رنگ‌های تاکید
- `--global-accent`: رنگ اصلی (آبی)
- `--global-accent-2`: رنگ ثانویه (بنفش)
- `--global-accent-hover`: رنگ هاور

### رنگ‌های وضعیت
- `--global-success`: رنگ موفقیت
- `--global-danger`: رنگ خطر
- `--global-warning`: رنگ هشدار
- `--global-info`: رنگ اطلاعات

### سایه‌ها
- `--global-shadow`: سایه استاندارد
- `--global-shadow-dark`: سایه تیره‌تر

## نحوه استفاده

### افزودن تم سراسری به قالب جدید

```html
{% load static %}
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>عنوان صفحه</title>
    
    <!-- فونت فارسی -->
    <link href="https://cdn.jsdelivr.net/npm/vazirmatn@33.003/index.css" rel="stylesheet">
    
    <!-- Global Theme CSS -->
    <link rel="stylesheet" href="{% static 'global/css/theme.css' %}">
    
    <!-- استایل‌های اختصاصی صفحه -->
    <style>
        /* استفاده از متغیرهای سراسری */
        .my-element {
            background: var(--global-card-bg);
            color: var(--global-text);
            border: 1px solid var(--global-border);
        }
    </style>
</head>
<body>
    <!-- محتوای صفحه -->
    
    <!-- Global Theme JS -->
    <script src="{% static 'global/js/theme.js' %}"></script>
</body>
</html>
```

### تغییر دستی تم

برای افزودن دکمه تغییر تم:

```html
<button onclick="toggleTheme()">تغییر تم</button>
```

### استفاده از توابع کمکی

```javascript
// نمایش/مخفی کردن رمز عبور
togglePassword('passwordInputId', buttonElement);

// اعتبارسنجی فرم
<form data-validate onsubmit="return validateForm(this)">
    <!-- فیلدهای فرم -->
</form>

// کپی متن به کلیپ‌بورد
copyToClipboard('متن برای کپی', buttonElement);
```

## مزایای این بازسازی

1. **یکپارچگی**: تمام ماژول‌ها از یک سیستم تم یکسان استفاده می‌کنند
2. **قابلیت نگهداری**: تغییرات تم تنها در یک فایل انجام می‌شود
3. **پشتیبانی از حالت تاریک**: تمام صفحات به طور خودکار از تم سیستم پیروی می‌کنند
4. **کاهش کد تکراری**: حذف استایل‌های تکراری در قالب‌های مختلف
5. **عملکرد بهتر**: بارگذاری سریع‌تر به دلیل کاهش حجم CSS
6. **قابلیت توسعه**: افزودن قابلیت‌های جدید به سیستم تم آسان‌تر است

## سازگاری با مرورگرها

- پشتیبانی از `prefers-color-scheme` در مرورگرهای مدرن
- پشتیبانی از localStorage برای ذخیره ترجیح کاربر
- پشتیبانی از CSS Variables در تمام مرورگرهای مدرن

## آینده

امکانات پیشنهادی برای توسعه آینده:
- افزودن تم‌های رنگی بیشتر (سبز، قرمز، بنفش)
- پشتیبانی از اندازه فونت قابل تنظیم
- افزودن انیمیشن‌های مشترک
- پشتیبانی از RTL/LTR بهتر
