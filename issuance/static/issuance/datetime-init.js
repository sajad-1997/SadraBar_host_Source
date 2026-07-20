$(document).ready(function () {

    $('.date-picker').persianDatepicker({
        format: 'YYYY/MM/DD',
        autoClose: true,
        observer: true,
        initialValue: false
    });


    $('.time-picker').persianDatepicker({
        format: 'HH:mm:ss',
        observer: true,
        initialValue: false,
        autoClose: true,
        onlyTimePicker: true,
        timePicker: {
            enabled: true,
            second: {
                enabled: true
            }
        }
    });

});


// $(document).ready(function() {
//     // تاریخ شمسی
//     $('.date-picker').persianDatepicker({
//         format: 'YYYY/MM/DD',
//         initialValue: false,
//         autoClose: true
//     });
//
//     // ساعت
//     $('.time-picker').timepicker({
//         timeFormat: 'HH:mm',
//         interval: 15,
//         dynamic: false,
//         dropdown: true,
//         scrollbar: true
//     });
// });
//


// $(function () {
//     // مطمئن شو پلاگین موجوده
//     if (!($.fn && $.fn.persianDatepicker)) {
//         console.warn("persianDatepicker plugin not available");
//         return;
//     }
//
//     // init فقط برای date inputs (بدون time)
//     $(".date-picker").each(function () {
//         $(this).persianDatepicker({
//             format: "YYYY/MM/DD",    // فرمت نمایش تاریخ به صورت شمسی
//             initialValue: false,     // اگر true: مقدار کنونی قرار داده می‌شود
//             autoClose: true,
//             timePicker: {enabled: false}  // مهم: زمان غیرفعال است
//         });
//     });
//
//     // اختیاری: اگر دلت می‌خواهد زمان پیش‌فرض را روی اکنون قرار بده
//     const timeInputs = document.querySelectorAll(".time-picker");
//     timeInputs.forEach(input => {
//         if (!input.value) {
//             const now = new Date();
//             const hh = String(now.getHours()).padStart(2, '0');
//             const mm = String(now.getMinutes()).padStart(2, '0');
//             input.value = `${hh}:${mm}`;
//         }
//     });
// });
