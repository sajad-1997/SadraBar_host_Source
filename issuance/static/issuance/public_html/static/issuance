// ================================================
// shipment.js - نسخه بهینه و آماده برای فایل خارجی
// ================================================

// -----------------------------
// ۱. تبدیل اعداد فارسی/عربی و جداکننده سه‌تایی
// -----------------------------
function toEnglishNumber(str) {
    if (!str) return "";
    return str
        .replace(/[\u06F0-\u06F9]/g, d => String.fromCharCode(d.charCodeAt(0) - 1728))
        .replace(/[\u0660-\u0669]/g, d => String.fromCharCode(d.charCodeAt(0) - 1584));
}

function parseNumber(value) {
    if (!value) return 0;
    value = toEnglishNumber(value.toString());
    const num = Number(value.replace(/,/g, ""));
    return isNaN(num) ? 0 : num;
}

function formatNumber(num) {
    if (isNaN(num)) return "0";
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// -----------------------------
// ۲. اعمال جداکننده سه‌تایی روی فیلد عددی با حفظ کرسر
// -----------------------------
function attachNumericField(field, callback) {
    field.addEventListener("input", function () {
        let cursorPos = field.selectionStart;
        let originalLength = field.value.length;
        let rawValue = parseNumber(field.value);
        field.value = formatNumber(rawValue);
        let newLength = field.value.length;
        cursorPos += newLength - originalLength;
        field.setSelectionRange(cursorPos, cursorPos);
        if (callback) callback();
    });
}

// -----------------------------
// ۳. محاسبات بارنامه
// -----------------------------
function initShipmentCalculations() {
    function getField(name) {
        return document.querySelector(`[name="shipment-${name}"]`);
    }

    const valueField = getField("value");
    const insuranceField = getField("insurance");
    const loadingFeeField = getField("loading_fee");
    const unloadingFeeField = getField("unloading_fee");
    const scaleFeeField = getField("scale_fee");
    const totalFareField = getField("total_fare");
    const freightField = getField("freight");

    if (!valueField || !insuranceField || !loadingFeeField ||  !unloadingFeeField || !scaleFeeField || !totalFareField || !freightField) {
        console.warn("یکی از فیلدهای فرم پیدا نشد!");
        return;
    }

    function updateInsurance() {
        const value = parseNumber(valueField.value);
        let insurance = 0;
        if (value > 0) {
            if (value <= 2000000000) {
                insurance = 2000000;  // سقف تا ۲ میلیارد ریال → بیمه ثابت
            } else {
                insurance = Math.floor(value * 0.001);  // بالای ۲ میلیارد ریال → ۱۰ درصد
            }
        }
        // const insurance = Math.round(value * 0.001);
        insuranceField.value = formatNumber(insurance);
    }

    function updateFreight() {
        const totalFare = parseNumber(totalFareField.value);
        const insurance = parseNumber(insuranceField.value);
        const loadingFee = parseNumber(loadingFeeField.value);
        const unloadingFee = parseNumber(unloadingFeeField.value);
        const scaleFee = parseNumber(scaleFeeField.value);

        let freight = totalFare - (insurance + loadingFee + unloadingFee + scaleFee);
        if (isNaN(freight) || freight < 0) freight = 0;
        freightField.value = formatNumber(freight);
    }

    [valueField, insuranceField, loadingFeeField, unloadingFeeField, scaleFeeField, totalFareField].forEach(f => {
        attachNumericField(f, () => {
            updateInsurance();
            updateFreight();
        });
    });

    attachNumericField(freightField);

    // مقداردهی اولیه
    [valueField, insuranceField, loadingFeeField, unloadingFeeField, scaleFeeField, totalFareField, freightField].forEach(f => {
        if (f.value) f.value = formatNumber(parseNumber(f.value));
    });
    updateInsurance();
    updateFreight();
    
    // اگر بارگیری / تخلیه / باسکول خالی بود صفر بفرست
    const feeFields = [loadingFeeField, unloadingFeeField, scaleFeeField];

    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", function () {
            feeFields.forEach(f => {
                let num = parseNumber(f.value);
                if (isNaN(num) || num <= 0) {
                    f.value = "0";
                }
            });
        });
    }

}

// -----------------------------
// ۴. selectable-card toggle
// -----------------------------
function initSelectableCards() {
    document.querySelectorAll('.selectable-card').forEach(card => {
        const checkbox = card.querySelector('input[type="checkbox"]');
        if (!checkbox) return;
        if (checkbox.checked) card.classList.add('selected');
        card.addEventListener('click', e => {
            if (e.target.tagName === 'INPUT') return; // جلوگیری از toggle روی input داخلی
            checkbox.checked = !checkbox.checked;
            card.classList.toggle('selected', checkbox.checked);
        });
    });
}

// -----------------------------
// ۵. توضیحات انتخابی + دستی (نسخه اصلاح‌شده - toggle قابل لغو)
// -----------------------------
function initExplanations() {
    const select = document.getElementById("explanations");
    const customInput = document.getElementById("customExplanation");
    const previewBox = document.getElementById("finalExplanationsPreview");
    const hiddenSelected = document.getElementById("selectedExplanations");
    const hiddenCustom = document.getElementById("customExplanations");

    if (!select || !previewBox || !hiddenSelected || !hiddenCustom) return;

    function updatePreview() {
        const selectedOptions = Array.from(select.options)
            .filter(opt => opt.selected)
            .map(opt => opt.value);

        const customLines = (customInput ? customInput.value : "")
            .split("\n")
            .map(l => l.trim())
            .filter(l => l);

        let html = "<ul>";
        selectedOptions.forEach(item => {
            html += `<li>${item}</li>`;
        });
        customLines.forEach(item => {
            html += `<li>${item}</li>`;
        });
        html += "</ul>";

        previewBox.innerHTML = html;
        hiddenSelected.value = JSON.stringify(selectedOptions);
        hiddenCustom.value = JSON.stringify(customLines);
    }

    // برای هر گزینه: mousedown (اصلی) + fallback click/touchstart
    Array.from(select.options).forEach(opt => {
        const toggleHandler = function (e) {
            // جلوگیری از رفتار پیش‌فرض مرورگر تا بتوانیم selection را خودمان مدیریت کنیم
            e.preventDefault();

            const willSelect = !this.selected;

            if (willSelect) {
                // اگر قرار است انتخاب شود => بقیه را پاک کن تا رفتار تک‌انتخابی حفظ شود
                Array.from(select.options).forEach(o => o.selected = false);
                this.selected = true;
            } else {
                // اگر قرار است لغو شود => خودش را false کن (بدون انتخاب هیچ‌کسی)
                this.selected = false;
            }

            updatePreview();
            return false;
        };

        opt.addEventListener('mousedown', toggleHandler);
        opt.addEventListener('click', toggleHandler);            // fallback برای برخی مرورگرها
        opt.addEventListener('touchstart', function (e) {         // موبایل: جلوگیری از native picker در برخی پیاده‌سازی‌ها
            // توجه: touchstart باید passive:false باشد تا preventDefault کار کند؛
            // اگر مرورگر اجازه نده، ممکن است native picker باز شود — در آن صورت باید از UI دلخواه استفاده کنید.
            e.preventDefault();
            toggleHandler.call(this, e);
        }, {passive: false});
    });

    // پشتیبانی ساده از صفحه‌کلید: Space/Enter برای toggle روی گزینهٔ فعلی
    select.addEventListener('keydown', function (e) {
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            const idx = select.selectedIndex;
            if (idx >= 0) {
                const opt = select.options[idx];
                const willSelect = !opt.selected;
                if (willSelect) {
                    Array.from(select.options).forEach(o => o.selected = false);
                    opt.selected = true;
                } else {
                    opt.selected = false;
                }
                updatePreview();
            }
        }
    });

    if (customInput) {
        customInput.addEventListener('input', updatePreview);
    }

    // مقداردهی اولیه
    updatePreview();
}


// -----------------------------
// ۶. جستجوی AJAX
// نسخه بهینه‌شده drop-in برای enableSearch
// -----------------------------
function enableSearch(inputId, resultsId, hiddenId, searchUrl, extraOptions = {}) {
    const $input = $(`#${inputId}`);
    const $results = $(`#${resultsId}`);
    const $hidden = $(`#${hiddenId}`);

    if ($input.length === 0 || $results.length === 0 || $hidden.length === 0) {
        console.warn("enableSearch: ورودی یا نتایج یا فیلد مخفی پیدا نشد:", inputId, resultsId, hiddenId);
        return;
    }

    // debounce ساده
    function debounce(fn, wait) {
        let t = null;
        return function () {
            const args = arguments;
            const ctx = this;
            clearTimeout(t);
            t = setTimeout(() => fn.apply(ctx, args), wait);
        };
    }

    // ارسال درخواست جستجو
    function doSearch(query) {
        // اگر فقط فاصله یا خالی است کاری نکن
        if (typeof query !== 'string' || query.trim().length === 0) {
            $results.empty().hide();
            return;
        }

        $.ajax({
            url: searchUrl,
            data: {q: query},
            success: function (data) {
                let html = "";
                if (data && Array.isArray(data.results) && data.results.length > 0) {
                    data.results.forEach(item => {
                        html += `<button type="button"
                                        class="list-group-item list-group-item-action"
                                        data-id="${item.id}"
                                        data-name="${item.name}"
                                        data-phone="${item.address || ''}"
                                        data-plate="${item.plate || ''}">
                                        <strong>${item.name}</strong>
                                        ${item.address ? " - " + item.address : ""}
                                 </button>`;
                    });
                } else {
                    html = `<div class="list-group-item">نتیجه‌ای یافت نشد</div>`;
                }
                $results.html(html).show();
            },
            error: function (xhr, status, err) {
                console.error("enableSearch AJAX error:", status, err);
                $results.html(`<div class="list-group-item text-muted">خطا در جستجو</div>`).show();
            }
        });
    }

    // بافرینگ (debounce) برای کاهش تعداد درخواست‌ها
    const debouncedSearch = debounce(function () {
        // مهم: مقدار خام را بدون trim() بخوانیم تا فاصلهٔ انتها حفظ شود
        const rawQuery = $input.val();
        doSearch(rawQuery);
    }, 250); // 250ms تأخیر؛ می‌تونید کم/زیاد کنید

    // استفاده از event مناسب: input برای پوشش کامل (موبایل، paste و غیره)
    $input.off('.enableSearch').on('input.enableSearch', function () {
        debouncedSearch();
    });

    // همچنین اگر خواستی روی Enter جستجو فوراً اجرا شود:
    $input.off('keydown.enableSearchEnter').on('keydown.enableSearchEnter', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            // اجرای فوری بدون debounce
            const rawQuery = $input.val();
            doSearch(rawQuery);
        }
    });

    // جلوگیری از چندبار اتصال handler کلیک: ابتدا off سپس on
    $results.off('click.enableSearch').on('click.enableSearch', '.list-group-item', function () {
        const $item = $(this);
        const id = $item.data('id');
        const name = $item.data('name') || "";
        const plate = $item.data('plate');

        // مقدار متن ورودی را با همان مقداری که عنصر پیشنهاد می‌دهد پر می‌کنیم
        $input.val(name);
        $hidden.val(id);

        if (extraOptions.fillPlateField && plate !== undefined) {
            $(`#${extraOptions.fillPlateField}`).val(plate);
        }

        $results.empty().hide();

        if (extraOptions.updateVehicleAjax) {
            $.ajax({
                url: extraOptions.updateVehicleAjax,
                data: {driver_id: id},
                success: function (res) {
                    if (res && res.success) {
                        $("#first-number").text(res.vehicle.two_digit);
                        $("#letter").text(res.vehicle.alphabet);
                        $("#second-number").text(res.vehicle.three_digit);
                        $("#province").text(res.vehicle.series);
                    } else {
                        $("#first-number").text("--");
                        $("#letter").text("-");
                        $("#second-number").text("---");
                        $("#province").text("**");
                    }
                },
                error: function () {
                    $("#first-number").text("--");
                    $("#letter").text("-");
                    $("#second-number").text("---");
                    $("#province").text("**");
                }
            });
        }
    });

    // کلیک بیرون از نتایج => مخفی کردن لیست
    // این handler هم بصورت namespaced اضافه شده تا در صورت جایگزینی تابع قبلاً تعریف‌شده تداخل نکند
    $(document).off('click.enableSearchDismiss').on('click.enableSearchDismiss', function (e) {
        if (!$(e.target).closest($results).length && !$(e.target).is($input)) {
            $results.empty().hide();
        }
    });
}

// -----------------------------
// ۷. اجرا در بارگذاری DOM
// -----------------------------
document.addEventListener("DOMContentLoaded", function () {
    initShipmentCalculations();
    initSelectableCards();
    initExplanations();

    // فعال‌سازی search AJAX با URL هایی که از template ارسال شدن
    enableSearch("receiver-input", "receiver-results", "receiver-id", urls.searchCustomer);
    enableSearch("sender-input", "sender-results", "sender-id", urls.searchCustomer);
    enableSearch("driver-input", "driver-results", "driver-id", urls.searchDriver, {
        fillPlateField: "vehicle-plate",
        updateVehicleAjax: urls.getVehicleByDriver
    });
    enableSearch("vehicle-input", "vehicle-results", "vehicle-id", urls.searchVehicle);
});
