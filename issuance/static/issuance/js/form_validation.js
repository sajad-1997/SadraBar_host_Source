/**
 * Form Validation Utility
 * این فایل برای اعتبارسنجی فرم‌ها و نمایش خطاها با استایل یکسان استفاده می‌شود
 */

(function($) {
    'use strict';

    // تابع اصلی اسکرول به فیلد خطا دار
    function scrollToElement(element, offset = 100) {
        if (element && element.length > 0) {
            $('html, body').animate({
                scrollTop: element.offset().top - offset
            }, 500);
            element.focus();
        }
    }

    // افزودن کلاس خطا به فیلد
    function addErrorClass(field, message) {
        field.addClass('error-field');
        
        // اگر پیام خطا وجود دارد و هنوز نمایش داده نشده
        if (message && !field.next('.error-msg').length) {
            field.after('<div class="error-msg">' + message + '</div>');
        }
        
        // افزودن انیمیشن لرزش
        field.addClass('shake');
        setTimeout(function() {
            field.removeClass('shake');
        }, 500);
    }

    // حذف تمام خطاها
    function clearErrors(form) {
        form.find('.error-msg').remove();
        form.find('.error-field').removeClass('error-field shake');
        form.find('.form-error-alert').remove();
    }

    // نمایش پیام خطای کلی
    function showFormError(form, message) {
        if (!form.find('.form-error-alert').length) {
            form.prepend('<div class="form-error-alert">' + message + '</div>');
            scrollToElement(form.find('.form-error-alert'), 50);
        }
    }

    // بررسی پر بودن فیلد
    function isFieldEmpty(field) {
        var value = field.val();
        if (typeof value === 'string') {
            return value.trim() === '';
        }
        return !value;
    }

    // اعتبارسنجی فیلدهای اجباری
    function validateRequiredFields(form, requiredSelectors) {
        var isValid = true;
        var firstErrorField = null;

        clearErrors(form);

        requiredSelectors.forEach(function(selector) {
            var field = form.find(selector.field);
            
            if (selector.required && isFieldEmpty(field)) {
                addErrorClass(field, selector.message || 'این فیلد الزامی است');
                isValid = false;
                
                if (!firstErrorField) {
                    firstErrorField = field;
                }
            }
        });

        if (!isValid) {
            showFormError(form, 'لطفاً فیلدهای اجباری را تکمیل کنید');
            scrollToElement(firstErrorField, 100);
        }

        return isValid;
    }

    // پیدا کردن فیلدهای دارای صفت required در HTML
    function findRequiredFields(form) {
        var requiredFields = [];
        
        form.find('input[required], select[required], textarea[required]').each(function() {
            var $this = $(this);
            var fieldName = $this.attr('name') || $this.attr('id') || 'فیلد';
            var label = $this.closest('.mb-3').find('label').text() || 
                       $this.prev('label').text() || 
                       $this.siblings('label').text() || fieldName;
            
            // پاک کردن ستاره و کاراکترهای اضافی از لیبل
            label = label.replace('*', '').trim();
            
            requiredFields.push({
                field: '#' + $this.attr('id'),
                required: true,
                message: label + ' الزامی است'
            });
        });

        return requiredFields;
    }

    // اضافه کردن نشانگر ستاره قرمز به لیبل فیلدهای اجباری
    function markRequiredLabels(form) {
        form.find('input[required], select[required], textarea[required]').each(function() {
            var $this = $(this);
            var label = $this.closest('.mb-3').find('label');
            if (label.length === 0) {
                label = $this.prev('label');
            }
            if (label.length === 0) {
                label = $this.siblings('label');
            }
            
            if (label.length > 0 && !label.hasClass('required')) {
                label.addClass('required');
                // اگر متن لیبل ستاره ندارد، اضافه کن
                if (label.text().indexOf('*') === -1) {
                    label.addClass('required');
                }
            }
        });
    }

    // راه‌اندازی ولیدیشن برای فرم
    $.fn.setupFormValidation = function(options) {
        var form = this;
        var settings = $.extend({
            requiredFields: [],
            onSubmit: null,
            preventDefault: true
        }, options);

        // مارک کردن لیبل‌های اجباری
        markRequiredLabels(form);

        // اگر فیلدهای اجباری مشخص نشده، از صفت required استفاده کن
        if (settings.requiredFields.length === 0) {
            settings.requiredFields = findRequiredFields(form);
        }

        // مدیریت submit فرم
        form.on('submit', function(e) {
            if (!validateRequiredFields(form, settings.requiredFields)) {
                if (settings.preventDefault) {
                    e.preventDefault();
                    return false;
                }
            } else if (settings.onSubmit) {
                // اگر callback وجود دارد، آن را اجرا کن
                settings.onSubmit(e, form);
            }
        });

        // پاک کردن خطا هنگام تایپ
        form.find('input, select, textarea').on('input change', function() {
            var $this = $(this);
            $this.removeClass('error-field shake');
            $this.next('.error-msg').remove();
            
            // اگر اولین فیلد اصلاح شده بود، پیام خطای کلی را حذف کن
            if (form.find('.error-field').length === 0) {
                form.find('.form-error-alert').fadeOut(300, function() {
                    $(this).remove();
                });
            }
        });

        return this;
    };

    // توابع کمکی برای استفاده مستقیم
    window.FormValidation = {
        scrollToElement: scrollToElement,
        addErrorClass: addErrorClass,
        clearErrors: clearErrors,
        validateRequiredFields: validateRequiredFields,
        findRequiredFields: findRequiredFields
    };

})(jQuery);
