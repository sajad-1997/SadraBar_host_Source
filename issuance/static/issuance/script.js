function enableSearch(inputId, resultsId, hiddenId, searchUrl, extraCallback = null) {
    let selectedIndex = -1;

    $(`#${inputId}`).on('keyup', function (e) {
        let query = $(this).val().trim();

        if (e.keyCode === 38) {
            if (selectedIndex > 0) selectedIndex--;
            highlightItem();
            return;
        }
        if (e.keyCode === 40) {
            if (selectedIndex < $(`#${resultsId} .list-group-item`).length - 1) selectedIndex++;
            highlightItem();
            return;
        }
        if (e.keyCode === 13) {
            e.preventDefault();
            let selected = $(`#${resultsId} .list-group-item`).eq(selectedIndex);
            if (selected.length) {
                chooseItem(selected);
            }
            return;
        }

        if (query.length === 0) {
            $(`#${resultsId}`).empty().hide();
            selectedIndex = -1;
            return;
        }

        $.ajax({
            url: searchUrl,
            data: {q: query},
            success: function (data) {
                let html = "";
                if (data.results.length > 0) {
                    data.results.forEach(function (item) {
                        html += `<button type="button" 
                                    class="list-group-item list-group-item-action"
                                    data-id="${item.id}" 
                                    data-name="${item.name}" 
                                    data-plate="${item.plate || ''}">
                                    <strong>${item.name}</strong>
                                    ${item.phone ? " - " + item.phone : ""}
                                 </button>`;
                    });
                } else {
                    html = `<div class="list-group-item">نتیجه‌ای یافت نشد</div>`;
                }
                $(`#${resultsId}`).html(html).show();
                selectedIndex = -1;
            }
        });
    });

    function highlightItem() {
        $(`#${resultsId} .list-group-item`).removeClass('active');
        if (selectedIndex >= 0) {
            $(`#${resultsId} .list-group-item`).eq(selectedIndex).addClass('active');
        }
    }

    function chooseItem(item) {
        let name = item.data('name');
        let id = item.data('id');
        let plate = item.data('plate');
        $(`#${inputId}`).val(name);
        $(`#${hiddenId}`).val(id);
        $(`#${resultsId}`).empty().hide();

        if (extraCallback) {
            extraCallback({id, name, plate});
        }
    }

    $(document).on('click', `#${resultsId} .list-group-item`, function () {
        chooseItem($(this));
    });
}

// فعال‌سازی
$(document).ready(function () {
    enableSearch("driver-input", "driver-results", "driver-id", "{% url 'search_driver' %}", function (driver) {
        if (driver.plate) {
            $("#vehicle-input").val(driver.plate); // پر کردن فیلد vehicle
        }
    });

    enableSearch("receiver-input", "receiver-results", "receiver-id", "{% url 'search_receiver' %}");
    enableSearch("sender-input", "sender-results", "sender-id", "{% url 'search_sender' %}");
    enableSearch("vehicle-input", "vehicle-results", "vehicle-id", "{% url 'search_vehicle' %}");
});
