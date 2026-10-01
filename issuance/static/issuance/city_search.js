/**
 * city_search.js
 * مدیریت جستجوی خودکار (Autocomplete) شهرها برای مبدأ و مقصد
 */

document.addEventListener("DOMContentLoaded", function () {
    // اطمینان از تعریف آدرس URL در قالب HTML
    if (typeof cargoCitySearchUrl === 'undefined') {
        console.error("متغیر cargoCitySearchUrl در قالب HTML تعریف نشده است.");
        return;
    }

    // تنظیمات برای مبدأ و مقصد
    const searchConfigs = [
        {
            inputId: "id_cargo-origin_display",
            hiddenId: "id_cargo-origin",
            resultsId: "cargo-origin-results"
        },
        {
            inputId: "id_cargo-destination_display",
            hiddenId: "id_cargo-destination",
            resultsId: "cargo-destination-results"
        }
    ];

    searchConfigs.forEach(config => {
        initCityAutocomplete(
            config.inputId,
            config.hiddenId,
            config.resultsId,
            cargoCitySearchUrl
        );
    });
});

function initCityAutocomplete(inputId, hiddenId, resultsId, searchUrl) {
    const $input = $(`#${inputId}`);
    const $hidden = $(`#${hiddenId}`);
    const $results = $(`#${resultsId}`);

    // اگر المان‌ها در صفحه وجود نداشتند، خارج شو
    if ($input.length === 0 || $hidden.length === 0 || $results.length === 0) {
        return;
    }

    // تابع Debounce برای جلوگیری از ارسال درخواست‌های پشت سر هم
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // تابع اصلی انجام جستجو
    function performSearch(query) {
        const trimmedQuery = query.trim();

        if (trimmedQuery.length < 2) {
            $results.empty().hide();
            $hidden.val(''); // پاک کردن ID اگر متن کافی نیست
            return;
        }

        // نمایش وضعیت در حال بارگذاری
        $results.html('<div class="list-group-item text-muted text-center">در حال جستجو...</div>').show();

        $.ajax({
            url: searchUrl,
            data: { q: trimmedQuery },
            method: "GET",
            success: function (data) {
                $results.empty(); // پاک کردن پیام "در حال جستجو"

                if (data && Array.isArray(data.results) && data.results.length > 0) {
                    data.results.forEach(item => {
                        const $btn = $(`<button type="button"></button>`)
                            .addClass("list-group-item list-group-item-action city-result-item")
                            .attr("data-id", item.id)
                            .attr("data-display", item.display)
                            .html(`<strong>${item.province}</strong> - ${item.name}`);

                        $results.append($btn);
                    });
                    $results.show();
                } else {
                    $results.html('<div class="list-group-item text-muted">موردی یافت نشد</div>').show();
                }
            },
            error: function () {
                $results.html('<div class="list-group-item text-danger">خطا در برقراری ارتباط با سرور</div>').show();
            }
        });
    }

    // اجرای جستجو با تأخیر ۳۰۰ میلی‌ثانیه
    const debouncedSearch = debounce(function () {
        performSearch($input.val());
    }, 300);

    // رویداد تایپ کردن کاربر
    $input.off('input.citySearch').on('input.citySearch', function () {
        // اگر کاربر کل متن را پاک کرد، فیلد مخفی هم پاک شود
        if ($(this).val().trim() === '') {
            $hidden.val('');
        }
        debouncedSearch();
    });

    // رویداد کلیک روی یکی از گزینه‌های لیست
    $results.off('click.citySearch').on('click.citySearch', '.city-result-item', function () {
        const selectedId = $(this).data('id');
        const selectedDisplay = $(this).data('display');

        $input.val(selectedDisplay);
        $hidden.val(selectedId);

        $results.empty().hide(); // بستن لیست پس از انتخاب
    });

    // رویداد کلیک در خارج از کادر برای بستن لیست نتایج
    $(document).off('click.citySearchDismiss').on('click.citySearchDismiss', function (e) {
        const isClickInsideInput = $(e.target).is($input);
        const isClickInsideResults = $(e.target).closest($results).length > 0;

        if (!isClickInsideInput && !isClickInsideResults) {
            $results.empty().hide();
        }
    });
}