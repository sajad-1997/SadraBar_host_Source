# راهنمای استفاده از سیستم ولیدیشن فرم‌ها

## معرفی
این سیستم یک راهکار یکپارچه برای اعتبارسنجی فرم‌ها در کل پروژه فراهم می‌کند. تمام قالب‌ها اکنون از استایل و رفتار یکسانی برای نمایش خطاهای فیلدهای اجباری استفاده می‌کنند.

## ویژگی‌ها
- ✅ بررسی پر بودن فیلدهای اجباری قبل از ارسال فرم
- ✅ نمایش بوردر قرمز رنگ برای فیلدهای خالی
- ✅ اسکرول خودکار صفحه به اولین فیلد خطا دار
- ✅ فوکوس خودکار روی فیلد خطا دار
- ✅ نمایش پیام خطای واضح زیر هر فیلد
- ✅ انیمیشن لرزش (shake) برای جلب توجه کاربر
- ✅ پاک شدن خطا هنگام شروع به تایپ کردن کاربر

## فایل‌های اضافه شده

### 1. استایل‌های CSS
**مسیر:** `/workspace/issuance/static/issuance/css/main.css`

کلاس‌های اضافه شده:
- `.error-field`: بوردر قرمز و پس‌زمینه صورتی کمرنگ برای فیلدهای دارای خطا
- `.error-msg`: استایل پیام خطا زیر فیلدها
- `label.required`: اضافه کردن ستاره قرمز به لیبل فیلدهای اجباری
- `.error-field.shake`: انیمیشن لرزش برای فیلد خطا دار
- `.form-error-alert`: پیام خطای کلی فرم

### 2. جاوااسکریپت ولیدیشن
**مسیر:** `/workspace/issuance/static/issuance/js/form_validation.js`

توابع اصلی:
- `FormValidation.addErrorClass(field, message)`: افزودن کلاس خطا به فیلد
- `FormValidation.clearErrors(form)`: حذف تمام خطاها از فرم
- `FormValidation.scrollToElement(element, offset)`: اسکرول به المان مشخص شده
- `FormValidation.validateRequiredFields(form, requiredSelectors)`: اعتبارسنجی فیلدهای اجباری
- `$.fn.setupFormValidation(options)`: راه‌اندازی خودکار ولیدیشن برای فرم

## نحوه استفاده

### روش 1: استفاده مستقیم از توابع (پیشنهادی برای فرم‌های موجود)

```javascript
$(document).ready(function () {
    const form = $("#my-form");
    const nameField = $("#name-input");
    const addressField = $("#address-input");

    function validateForm() {
        FormValidation.clearErrors(form);
        let valid = true;
        let firstErrorField = null;

        if (!nameField.val().trim()) {
            FormValidation.addErrorClass(nameField, 'نام الزامی است');
            valid = false;
            if (!firstErrorField) firstErrorField = nameField;
        }
        
        if (!addressField.val().trim()) {
            FormValidation.addErrorClass(addressField, 'آدرس الزامی است');
            valid = false;
            if (!firstErrorField) firstErrorField = addressField;
        }

        if (!valid) {
            FormValidation.scrollToElement(firstErrorField, 100);
        }
        
        return valid;
    }

    form.on("submit", function (e) {
        if (!validateForm()) {
            e.preventDefault();
        }
    });

    // پاک کردن خطا هنگام تایپ
    form.find("input").on("input", function () {
        $(this).removeClass("error-field shake");
        $(this).next(".error-msg").remove();
    });
});
```

### روش 2: استفاده از صفت required در HTML (خودکار)

```html
<form id="my-form">
    <label>نام:</label>
    <input type="text" id="name" name="name" required>
    
    <label>آدرس:</label>
    <input type="text" id="address" name="address" required>
    
    <button type="submit">ذخیره</button>
</form>

<script>
$(document).ready(function () {
    $("#my-form").setupFormValidation({
        onSubmit: function(e, form) {
            // اینجا کد ارسال فرم را بنویسید
            console.log("فرم معتبر است و ارسال می‌شود");
        }
    });
});
</script>
```

### روش 3: تعیین دستی فیلدهای اجباری

```javascript
$(document).ready(function () {
    $("#my-form").setupFormValidation({
        requiredFields: [
            {
                field: "#name",
                required: true,
                message: "نام کامل الزامی است"
            },
            {
                field: "#national-code",
                required: true,
                message: "کد ملی را وارد کنید"
            },
            {
                field: "#phone",
                required: true,
                message: "شماره تلفن الزامی است"
            }
        ],
        onSubmit: function(e, form) {
            // کد ارسال فرم
        }
    });
});
```

## قالب‌های به‌روزرسانی شده

### 1. مشتریان
- ✅ `/workspace/customers/templates/customers/add_customer.html`
- ✅ `/workspace/issuance/templates/issuance/add/add_customer.html`

### 2. سایر قالب‌ها
برای به‌روزرسانی سایر قالب‌ها، کافیست:
1. تابع `validateForm()` را مشابه نمونه‌های بالا اضافه کنید
2. در رویداد submit، ولیدیشن را فراخوانی کنید
3. از `FormValidation.addErrorClass()` برای نمایش خطا استفاده کنید

## مثال کامل برای یک فرم جدید

```html
{% extends "issuance/base.html" %}

{% block content %}
<div class="container">
    <h3>عنوان فرم</h3>
    <form id="my-form" method="post">
        {% csrf_token %}
        
        <div class="mb-3">
            <label>*نام:</label>
            <input type="text" id="name" name="name">
        </div>
        
        <div class="mb-3">
            <label>*کد ملی:</label>
            <input type="text" id="national-code" name="national_code">
        </div>
        
        <div class="mb-3">
            <label>توضیحات:</label>
            <textarea id="description" name="description"></textarea>
        </div>
        
        <button type="submit">ذخیره</button>
    </form>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
$(document).ready(function () {
    const form = $("#my-form");
    const nameField = $("#name");
    const nationalCodeField = $("#national-code");

    function validateForm() {
        FormValidation.clearErrors(form);
        let valid = true;
        let firstErrorField = null;

        if (!nameField.val().trim()) {
            FormValidation.addErrorClass(nameField, 'نام الزامی است');
            valid = false;
            if (!firstErrorField) firstErrorField = nameField;
        }
        
        if (!nationalCodeField.val().trim()) {
            FormValidation.addErrorClass(nationalCodeField, 'کد ملی الزامی است');
            valid = false;
            if (!firstErrorField) firstErrorField = nationalCodeField;
        }

        if (!valid) {
            FormValidation.scrollToElement(firstErrorField, 100);
        }
        
        return valid;
    }

    form.on("submit", function (e) {
        e.preventDefault();
        if (!validateForm()) return;

        // ارسال فرم با AJAX یا روش معمولی
        $.ajax({
            url: "/your-endpoint/",
            type: "POST",
            data: form.serialize(),
            success: function (resp) {
                // موفقیت
            },
            error: function () {
                // خطا
            }
        });
    });

    // پاک کردن خطا هنگام تایپ
    form.find("input, textarea").on("input", function () {
        $(this).removeClass("error-field shake");
        $(this).next(".error-msg").remove();
    });
});
</script>
{% endblock %}
```

## نکات مهم

1. **اولویت فیلدها**: سیستم به صورت خودکار به اولین فیلد خطا دار اسکرول می‌کند
2. **پاک شدن خطاها**: به محض اینکه کاربر شروع به تایپ کند، خطای فیلد پاک می‌شود
3. **ریسپانسیو**: استایل‌ها کاملاً ریسپانسیو هستند و در موبایل به خوبی نمایش داده می‌شوند
4. **دسترسی‌پذیری**: فیلدهای خطا دار به صورت خودکار فوکوس می‌گیرند

## عیب‌یابی

### مشکل: اسکرول انجام نمی‌شود
- مطمئن شوید jQuery لود شده است
- بررسی کنید که سلکتور فیلد صحیح باشد

### مشکل: استایل قرمز نمایش داده نمی‌شود
- بررسی کنید که `main.css` لود شده باشد
- کش مرورگر را پاک کنید

### مشکل: پیام خطا نمایش داده نمی‌شود
- مطمئن شوید پیام به درستی به تابع `addErrorClass` پاس داده شده
- بررسی کنید که المان parent اجازه درج div را دارد

---
**تاریخ به‌روزرسانی:** 2024
**نسخه:** 1.0
