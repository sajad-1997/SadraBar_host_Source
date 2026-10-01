// ================================================
// shipment_combined.js - نسخه ترکیبی و بهینه
// ================================================

// -----------------------------
// ۱. تبدیل اعداد فارسی/عربی و جداکننده سه‌تایی
// -----------------------------
function toEnglishNumber(str) {
    if (!str) return "";
    return str
        .replace(/[۰-۹]/g, d => String.fromCharCode(d.charCodeAt(0) - 1728))
        .replace(/[٠-٩]/g, d => String.fromCharCode(d.charCodeAt(0) - 1584));
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
// ۲. محاسبات بارنامه
// -----------------------------
function initShipmentCalculations() {
    function getField(name) {
        return document.querySelector(`[name="shipment-${name}"]`);
    }

    const valueField = getField("value");
    const insuranceField = getField("insurance");
    const loadingFeeField = getField("loading_fee");
    const totalFareField = getField("total_fare");
    const freightField = getField("freight");

    if (!valueField || !insuranceField || !loadingFeeField || !totalFareField || !freightField) {
        console.warn("یکی از فیلدهای فرم پیدا نشد!");
        return;
    }

    function updateInsurance() {
        const value = parseNumber(valueField.value);
        let insurance = 0;
        if (value > 0) {
            insurance = value <= 2000000000 ? 2000000 : Math.floor(value * 0.001);
        }
        insuranceField.value = formatNumber(insurance);
    }

    function updateFreight() {
        const totalFare = parseNumber(totalFareField.value);
        const insurance = parseNumber(insuranceField.value);
        const loadingFee = parseNumber(loadingFeeField.value);
        let freight = totalFare - (insurance + loadingFee);
        if (isNaN(freight) || freight < 0) freight = 0;
        freightField.value = formatNumber(freight);
    }

    [valueField, insuranceField, loadingFeeField, totalFareField].forEach(f => {
        attachNumericField(f, () => {
            updateInsurance();
            updateFreight();
        });
    });

    attachNumericField(freightField);

    [valueField, insuranceField, loadingFeeField, totalFareField, freightField].forEach(f => {
        if (f.value) f.value = formatNumber(parseNumber(f.value));
    });
    updateInsurance();
    updateFreight();
}

// -----------------------------
// ۳. selectable-card toggle
// -----------------------------
function initSelectableCards() {
    document.querySelectorAll('.selectable-card').forEach(card => {
        const checkbox = card.querySelector('input[type="checkbox"]');
        if (!checkbox) return;
        if (checkbox.checked) card.classList.add('selected');
        card.addEventListener('click', e => {
            if (e.target.tagName === 'INPUT') return;
            checkbox.checked = !checkbox.checked;
            card.classList.toggle('selected', checkbox.checked);
        });
    });
}

// -----------------------------
// ۴. توضیحات انتخابی + دستی
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
        selectedOptions.forEach(item => { html += `<li>${item}</li>` });
        customLines.forEach(item => { html += `<li>${item}</li>` });
        html += "</ul>";

        previewBox.innerHTML = html;
        hiddenSelected.value = JSON.stringify(selectedOptions);
        hiddenCustom.value = JSON.stringify(customLines);
    }

    Array.from(select.options).forEach(opt => {
        const toggleHandler = function (e) {
            e.preventDefault();
            const willSelect = !this.selected;
            Array.from(select.options).forEach(o => o.selected = false);
            this.selected = willSelect;
            updatePreview();
            return false;
        };
        opt.addEventListener('mousedown', toggleHandler);
        opt.addEventListener('click', toggleHandler);
        opt.addEventListener('touchstart', function (e) { e.preventDefault(); toggleHandler.call(this, e); }, {passive:false});
    });

    select.addEventListener('keydown', function (e) {
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            const idx = select.selectedIndex;
            if (idx >= 0) {
                const opt = select.options[idx];
                const willSelect = !opt.selected;
                Array.from(select.options).forEach(o => o.selected = false);
                opt.selected = willSelect;
                updatePreview();
            }
        }
    });

    if (customInput) customInput.addEventListener('input', updatePreview);
    updatePreview();
}

// -----------------------------
// ۵. AJAX search عمومی با delegation + debounce
// -----------------------------
function enableSearch(inputId, resultsId, hiddenId, searchUrl, extraOptions = {}) {
    const $input = $(`#${inputId}`);
    const $results = $(`#${resultsId}`);
    const $hidden = $(`#${hiddenId}`);
    if (!$input.length || !$results.length || !$hidden.length) return;

    let selectedIndex = -1;

    function debounce(fn, wait) {
        let t = null;
        return function () {
            clearTimeout(t);
            t = setTimeout(() => fn.apply(this, arguments), wait);
        };
    }

    function doSearch(query) {
        if (!query || !query.trim().length) {
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
                        html += `<button type='button' class='list-group-item list-group-item-action' data-id='${item.id}' data-name='${item.name}' data-national='${item.national_id||''}' data-postal='${item.postal||''}' data-phone='${item.phone||''}' data-address='${item.address||''}'>${item.name} ${item.phone ? '-'+item.phone:''}</button>`;
                    });
                } else {
                    html = `<div class='list-group-item'>نتیجه‌ای یافت نشد</div>`;
                }
                $results.html(html).show();
                selectedIndex = -1;
            },
            error: function () { $results.html(`<div class='list-group-item text-muted'>خطا در جستجو</div>`).show(); }
        });
    }

    const debouncedSearch = debounce(function () {
        doSearch($input.val());
    }, 250);

    $input.off('.enableSearch').on('input.enableSearch', debouncedSearch);

    $input.off('keydown.enableSearch').on('keydown.enableSearch', function(e) {
        const items = $results.find('.list-group-item');
        if(e.keyCode === 38){ if(selectedIndex>0) selectedIndex--; highlightItem(); e.preventDefault(); return; }
        if(e.keyCode === 40){ if(selectedIndex<items.length-1) selectedIndex++; highlightItem(); e.preventDefault(); return; }
        if(e.keyCode === 13){ e.preventDefault(); items.eq(selectedIndex).click(); return; }

        function highlightItem(){ items.removeClass('active'); if(selectedIndex>=0) items.eq(selectedIndex).addClass('active'); }
    });

    $results.off('click.enableSearch').on('click.enableSearch', '.list-group-item', function () {
        const $item = $(this);
        $input.val($item.data('name'));
        $hidden.val($item.data('id'));
        if(extraOptions.fillPlateField && $item.data('plate')!==undefined) {
            $(`#${extraOptions.fillPlateField}`).val($item.data('plate'));
        }
        if(extraOptions.updateVehicleAjax) {
            $.ajax({url:extraOptions.updateVehicleAjax,data:{driver_id:$item.data('id')},success:function(res){
                if(res && res.success){
                    $("#first-number").text(res.vehicle.two_digit);
                    $("#letter").text(res.vehicle.alphabet);
                    $("#second-number").text(res.vehicle.three_digit);
                    $("#province").text(res.vehicle.series);
                } else {
                    $("#first-number").text("--"); $("#letter").text("-"); $("#second-number").text("---"); $("#province").text("**");
                }
            }, error:function(){ $("#first-number").text("--"); $("#letter").text("-"); $("#second-number").text("---"); $("#province").text("**"); }
            });
        }
        $results.empty().hide();
    });

    $(document).off('click.enableSearchDismiss').on('click.enableSearchDismiss', function (e) {
        if (!$(e.target).closest($results).length && !$(e.target).is($input)) {
            $results.empty().hide();
        }
    });
}

// -----------------------------
// ۶. فرم مشتری: submit + duplicate
// -----------------------------
function initCustomerForm() {
    $("#customer-form").on('submit', function(e){
        e.preventDefault();
        $.ajax({
            url: "{% url 'save_customer' %}",
            type: "POST",
            data: $(this).serialize(),
            headers: {"X-CSRFToken": "{{ csrf_token }}"},
            success: function(resp){
                $("#msg").text(resp.success ? `با موفقیت ذخیره شد (ID: ${resp.id})` : `خطا: ${resp.error}`);
            },
            error: function(){ $("#msg").text("مشکلی در ارتباط با سرور پیش آمد"); }
        });
    });

    $("#add-to-customer").on('click', function(){
        let customerId = $("#customer-id").val();
        if(!customerId){ $("#msg").text("ابتدا یک مشتری را انتخاب کنید."); return; }
        $.ajax({
            url: "{% url 'duplicate_customer' %}",
            type: "POST",
            data: $("#customer-form").serialize(),
            headers: {"X-CSRFToken": "{{ csrf_token }}"},
            success: function(resp){
                $("#msg").text(resp.success ? `رکورد جدید برای مشتری ایجاد شد (ID: ${resp.new_id})` : `خطا: ${resp.error}`);
                if(resp.success) $("#customer-id").val(resp.new_id);
            },
            error: function(){ $("#msg").text("مشکلی در ارتباط با سرور پیش آمد"); }
        });
    });
}

// -----------------------------
// ۷. اجرا در بارگذاری DOM
// -----------------------------
document.addEventListener("DOMContentLoaded", function () {
    initShipmentCalculations();
    initSelectableCards();
    initExplanations();

    enableSearch("receiver-input", "receiver-results", "receiver-id", urls.searchCustomer);
    enableSearch("sender-input", "sender-results", "sender-id", urls.searchCustomer);
    enableSearch("driver-input", "driver-results", "driver-id", urls.searchDriver, { fillPlateField: "vehicle-plate", updateVehicleAjax: urls.getVehicleByDriver });
    enableSearch("vehicle-input", "vehicle-results", "vehicle-id", urls.searchVehicle);
    enableSearch("customer-input", "customer-results", "customer-id", "{% url 'search_customer' %}");

    initCustomerForm();
});
