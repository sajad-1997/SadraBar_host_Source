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

// -----------------------------
// تبدیل عدد به حروف فارسی
// -----------------------------
function numberToPersianWords(num, unit = 'rial') {
    let isNegative = false;
    let cleanStr = num.toString();

    // مدیریت اعداد منفی
    if (cleanStr.startsWith('-')) {
        isNegative = true;
        cleanStr = cleanStr.slice(1);
    }

    // پاکسازی ورودی (حذف نقطه، کاما، فاصله و تبدیل اعداد فارسی/عربی به انگلیسی)
    cleanStr = cleanStr
        .replace(/[.,\s]/g, '')
        .replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
        .replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));

    if (!cleanStr || parseInt(cleanStr) === 0) {
        if (unit === 'rial') return "صفر ریال";
        if (unit === 'toman') return "صفر تومان";
        return "صفر";
    }

    const ones = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه'];
    const teens = ['ده', 'یازده', 'دوازده', 'سیزده', 'چهارده', 'پانزده', 'شانزده', 'هفده', 'هجده', 'نوزده'];
    const tens = ['', '', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود'];
    const hundreds = ['', 'یکصد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد'];
    const scales = ['', 'هزار', 'میلیون', 'میلیارد', 'تریلیون'];

    function convertThreeDigits(n) {
        if (n === 0) return '';

        let parts = [];
        const h = Math.floor(n / 100);
        const remainder = n % 100;

        if (h > 0) parts.push(hundreds[h]);

        if (remainder > 0) {
            if (remainder < 10) {
                parts.push(ones[remainder]);
            } else if (remainder < 20) {
                parts.push(teens[remainder - 10]);
            } else {
                const t = Math.floor(remainder / 10);
                const o = remainder % 10;
                if (o > 0) parts.push(tens[t] + ' و ' + ones[o]);
                else parts.push(tens[t]);
            }
        }
        // استفاده از join برای قرار دادن خودکار " و " بین اجزای یک عدد سه رقمی
        return parts.join(' و ');
    }

    const groups = [];
    for (let i = cleanStr.length; i > 0; i -= 3) {
        const start = Math.max(0, i - 3);
        groups.unshift(parseInt(cleanStr.slice(start, i)));
    }

    const validParts = [];
    for (let i = 0; i < groups.length; i++) {
        const groupValue = groups[i];
        if (groupValue > 0) {
            const groupWords = convertThreeDigits(groupValue);
            const scaleIndex = groups.length - 1 - i;
            if (scaleIndex > 0) validParts.push(groupWords + ' ' + scales[scaleIndex]);
            else validParts.push(groupWords);
        }
    }

    const unitText = unit === 'rial' ? ' ریال' : unit === 'toman' ? ' تومان' : '';
    let result = validParts.join(' و ').trim() + unitText;

    return isNegative ? 'منفی ' + result : result;
}

// -----------------------------
// تبدیل عدد به حروف فارسی با نمایش همزمان ریال و تومان
// -----------------------------
function numberToPersianWordsBoth(num) {
    if (!num || num === 0) return "صفر ریال - صفر تومان";

    const rialWords = numberToPersianWords(num, 'rial');
    const tomanValue = Math.floor(num / 10);
    const tomanWords = numberToPersianWords(tomanValue, 'toman');

    return rialWords + ' - ' + tomanWords;
}

function parseNumber(value) {
    if (!value) return 0;
    value = toEnglishNumber(value.toString());
    // حذف تمام جداکننده‌ها (کاما انگلیسی و فارسی)
    const cleanedValue = value.replace(/[,٬]/g, "");
    const num = Number(cleanedValue);
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

        // اگر مقدار معتبر است، فرمت کن
        if (rawValue >= 0) {
            field.value = formatNumber(rawValue);
            let newLength = field.value.length;
            cursorPos += newLength - originalLength;
            // اطمینان از اینکه کرسر در محدوده مجاز است
            cursorPos = Math.max(0, Math.min(cursorPos, newLength));
            field.setSelectionRange(cursorPos, cursorPos);
        }

        // به‌روزرسانی نمایش حروفی
        updateWordDisplay(field, rawValue);

        if (callback) callback();
    });
}

// -----------------------------
// افزودن نمایش حروفی به فیلدهای ریالی
// -----------------------------
function attachWordDisplay(field) {
    // ایجاد عنصر نمایش حروفی بعد از فیلد
    const wordDisplay = document.createElement('div');
    wordDisplay.className = 'amount-in-words';
    wordDisplay.style.fontSize = '0.85rem';
    wordDisplay.style.color = '#6c757d';
    wordDisplay.style.marginTop = '4px';
    wordDisplay.style.fontWeight = '500';
    field.parentNode.insertBefore(wordDisplay, field.nextSibling);

    // ذخیره عنصر نمایش در فیلد برای دسترسی آسان
    field._wordDisplay = wordDisplay;

    // به‌روزرسانی اولیه
    const initialValue = parseNumber(field.value);
    updateWordDisplay(field, initialValue);
}

function updateWordDisplay(field, value) {
    if (field._wordDisplay) {
        const words = numberToPersianWordsBoth(value);
        field._wordDisplay.textContent = words;
    }
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

    if (!valueField || !insuranceField || !loadingFeeField || !unloadingFeeField || !scaleFeeField || !totalFareField || !freightField) {
        console.warn("یکی از فیلدهای فرم پیدا نشد!");
        return;
    }

    // افزودن نمایش حروفی به تمام فیلدهای ریالی
    [valueField, insuranceField, loadingFeeField, unloadingFeeField, scaleFeeField, totalFareField, freightField].forEach(f => {
        attachWordDisplay(f);
    });

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
        updateWordDisplay(insuranceField, insurance);
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
        updateWordDisplay(freightField, freight);
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
// ۸. فیلدهای عددی محموله (وزن، وزن دوم و تعداد بسته‌بندی) - مشابه فیلد کرایه
// -----------------------------

// تبدیل عدد به حروف فارسی بدون پسوند واحد
function numberToPersianWordsPlain(num) {
    return numberToPersianWords(num, 'none');
}

// نمایش حروفی وزن - هر ۱۰۰۰ کیلوگرم = ۱ تن
function weightToPersianWords(kg) {
    kg = Math.floor(Math.abs(parseNumber(kg)));
    if (!kg || kg === 0) return "صفر";

    const tons = Math.floor(kg / 1000);
    const remainingKg = kg % 1000;
    const parts = [];

    if (tons > 0) parts.push(numberToPersianWordsPlain(tons) + ' تن');
    if (remainingKg > 0) parts.push(numberToPersianWordsPlain(remainingKg) + ' کیلوگرم');

    return parts.join(' و ');
}

// نمایش حروفی تعداد بسته‌بندی
function countToPersianWords(count) {
    count = Math.floor(Math.abs(parseNumber(count)));
    if (!count || count === 0) return "صفر";
    return numberToPersianWordsPlain(count) + ' عدد';
}

// اتصال رفتار فیلدهای عددی (جداکننده سه‌تایی + نمایش حروفی) مشابه فیلد کرایه
function attachCargoNumericField(field, wordsFn) {
    if (!field) return;

    // عنصر نمایش حروفی زیر فیلد (مشابه فیلد کرایه)
    const wordDisplay = document.createElement('div');
    wordDisplay.className = 'amount-in-words';
    wordDisplay.style.fontSize = '0.85rem';
    wordDisplay.style.color = '#6c757d';
    wordDisplay.style.marginTop = '4px';
    wordDisplay.style.fontWeight = '500';
    field.parentNode.insertBefore(wordDisplay, field.nextSibling);
    field._wordDisplay = wordDisplay;

    const updateDisplay = function () {
        const rawValue = parseNumber(field.value);
        wordDisplay.textContent = wordsFn(rawValue);
    };

    // اعمال جداکننده سه‌تایی روی ورودی با حفظ موقعیت کرسر
    field.addEventListener("input", function () {
        let cursorPos = field.selectionStart;
        let originalLength = field.value.length;
        const rawValue = parseNumber(field.value);

        field.value = formatNumber(rawValue);

        let newLength = field.value.length;
        cursorPos += newLength - originalLength;
        cursorPos = Math.max(0, Math.min(cursorPos, newLength));
        field.setSelectionRange(cursorPos, cursorPos);

        updateDisplay();
    });

    // مقداردهی اولیه (مثلاً در حالت ویرایش که مقدار عددی خام از سرور می‌آید)
    if (field.value) {
        field.value = formatNumber(parseNumber(field.value));
    }
    updateDisplay();
}

function initCargoNumericFields() {
    attachCargoNumericField(
        document.querySelector('[name="cargo-weight"]'),
        weightToPersianWords
    );
    attachCargoNumericField(
        document.querySelector('[name="cargo-weight_2"]'),
        weightToPersianWords
    );
    attachCargoNumericField(
        document.querySelector('[name="cargo-number_of_packaging"]'),
        countToPersianWords
    );
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

    // کش آخرین نتایج جستجو (برای دسترسی به تمام آدرس‌های مشتری انتخاب‌شده)
    let lastResults = [];

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
                    // کش نتایج برای نمایش تمام آدرس‌های مشتری انتخاب‌شده بعد از کلیک
                    lastResults = data.results;

                    data.results.forEach(item => {
                        const addresses = (item.addresses && item.addresses.length > 0) ? item.addresses : [];

                        // نمایش شماره تلفن اصلی (مثلاً برای راننده) در صورت فعال بودن گزینه showPhone
                        let phoneHtml = "";
                        if (extraOptions.showPhone && item.phone) {
                            phoneHtml = `<span class='address-phone'>📞 ${item.phone}</span>`;
                        }

                        if (addresses.length > 0) {
                            // هر آدرس مشتری به‌صورت یک نتیجه انتخابی مستقل نمایش داده می‌شود
                            // (یک مشتری با چند آدرس => چند نتیجه، هر کدام با نام مشتری و یکی از آدرس‌های او)
                            addresses.forEach(addr => {
                                let addrHtml = "";
                                if (addr.address) {
                                    addrHtml += `<span class='address-text'>${addr.address}</span>`;
                                }
                                if (addr.phone) {
                                    addrHtml += `<span class='address-phone'>📞 ${addr.phone}</span>`;
                                }

                                html += `<button type="button"
                                                class="list-group-item list-group-item-action"
                                                data-id="${item.id}"
                                                data-name="${item.name}"
                                                data-address="${addr.address || ''}"
                                                data-phone="${item.phone || ''}"
                                                data-plate="${item.plate || ''}">
                                                <strong>${item.name}</strong>
                                                ${addrHtml}
                                         </button>`;
                            });
                        } else {
                            // بدون آدرس (مثلاً راننده): یک نتیجه ساده
                            html += `<button type="button"
                                            class="list-group-item list-group-item-action"
                                            data-id="${item.id}"
                                            data-name="${item.name}"
                                            data-phone="${item.phone || ''}"
                                            data-plate="${item.plate || ''}">
                                            <strong>${item.name}</strong>
                                            ${phoneHtml}
                                     </button>`;
                        }
                    });
                } else {
                    lastResults = [];
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
    $results.off('click.enableSearch').on('click.enableSearch', '.list-group-item.list-group-item-action', function () {
        const $item = $(this);
        const id = $item.data('id');
        const name = $item.data('name') || "";
        const plate = $item.data('plate');
        // آدرس انتخاب‌شده از روی همان نتیجه‌ای که کلیک شده خوانده می‌شود
        const selectedAddress = $item.data('address') || "";

        // مقدار متن ورودی را با همان مقداری که عنصر پیشنهاد می‌دهد پر می‌کنیم
        $input.val(name);
        $hidden.val(id);

        if (extraOptions.fillPlateField && plate !== undefined) {
            $(`#${extraOptions.fillPlateField}`).val(plate);
        }

        // نمایش تمام آدرس‌های مشتری انتخاب‌شده (به‌صورت پایدار زیر فیلد)
        // آدرسی که کاربر روی آن کلیک کرده، هایلایت می‌شود
        const selectedItem = lastResults.find(r => String(r.id) === String(id));
        const selectedAddresses = (selectedItem && selectedItem.addresses) ? selectedItem.addresses : [];

        if (selectedAddresses.length > 0) {
            let addressListHtml = "<div class='address-list'>";
            selectedAddresses.forEach(addr => {
                const isSelected = selectedAddress && addr.address && String(addr.address) === String(selectedAddress);
                addressListHtml += `<div class='address-item${isSelected ? ' selected' : ''}'>`;
                if (addr.address) {
                    addressListHtml += `<span class='address-text'>${addr.address}</span>`;
                }
                if (addr.phone) {
                    addressListHtml += `<span class='address-phone'>📞 ${addr.phone}</span>`;
                }
                addressListHtml += `</div>`;
            });
            addressListHtml += "</div>";

            $results.html(
                `<div class="list-group-item no-action"><strong>${name}</strong>${addressListHtml}</div>`
            ).show();
        } else {
            $results.empty().hide();
        }

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
    initCargoNumericFields();
    initSelectableCards();
    initExplanations();

    // فعال‌سازی search AJAX با URL هایی که از template ارسال شدن
    enableSearch("receiver-input", "receiver-results", "receiver-id", urls.searchCustomer);
    enableSearch("sender-input", "sender-results", "sender-id", urls.searchCustomer);
    enableSearch("driver-input", "driver-results", "driver-id", urls.searchDriver, {
        fillPlateField: "vehicle-plate",
        updateVehicleAjax: urls.getVehicleByDriver,
        showPhone: true
    });
    enableSearch("vehicle-input", "vehicle-results", "vehicle-id", urls.searchVehicle);
});
