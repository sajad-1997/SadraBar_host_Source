from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from issuance.models import Bijak as Waybill
from .models.cluster import DuplicateCluster
from .models.snapshot import DuplicateWaybillSnapshot


def parse_amount(value):
    if not value:
        return 0
    try:
        return int(str(value).replace(",", "").strip())
    except:
        return 0


@login_required
def duplicate_audit_list(request):

    # =========================
    # اگر دکمه اسکن زده شود
    # =========================
    if request.method == "POST":

        # پاکسازی اسکن قبلی
        DuplicateCluster.objects.all().delete()

        # پیدا کردن بارنامه‌های با tracking_code تکراری
        duplicates = (
            Waybill.objects
            .values("tracking_code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for item in duplicates:
            tracking = item["tracking_code"]

            waybills = Waybill.objects.filter(tracking_code=tracking)

            cluster = DuplicateCluster.objects.create()

            for wb in waybills:
                DuplicateWaybillSnapshot.objects.create(
                    cluster=cluster,
                    original_waybill=wb
                )

    # =========================
    # دسته‌بندی نتایج
    # =========================
    clusters = DuplicateCluster.objects.prefetch_related("snapshots__original_waybill")

    duplicates_cargo = []
    duplicates_fare = []
    duplicates_info = []

    for cluster in clusters:
        snapshots = list(cluster.snapshots.all())
        n = len(snapshots)

        for i in range(n):
            wb1 = snapshots[i].original_waybill

            weight1 = getattr(wb1.cargo, "weight", 0)
            freight1 = parse_amount(wb1.freight)
            value1 = parse_amount(wb1.value)
            loading1 = parse_amount(wb1.loading_fee)
            unloading1 = parse_amount(wb1.unloading_fee)
            scale1 = parse_amount(wb1.scale_fee)

            for j in range(i + 1, n):
                wb2 = snapshots[j].original_waybill

                weight2 = getattr(wb2.cargo, "weight", 0)
                freight2 = parse_amount(wb2.freight)
                value2 = parse_amount(wb2.value)
                loading2 = parse_amount(wb2.loading_fee)
                unloading2 = parse_amount(wb2.unloading_fee)
                scale2 = parse_amount(wb2.scale_fee)

                # 1️⃣ محموله متفاوت
                if (
                    weight1 != weight2 and
                    wb1.sender_id == wb2.sender_id and
                    wb1.receiver_id == wb2.receiver_id and
                    wb1.driver_id == wb2.driver_id
                ):
                    if wb1 not in duplicates_cargo:
                        duplicates_cargo.append(wb1)
                    if wb2 not in duplicates_cargo:
                        duplicates_cargo.append(wb2)

                # 2️⃣ هزینه / ارزش متفاوت (فقط تایید شده)
                elif (
                    (freight1 != freight2 or value1 != value2 or
                     loading1 != loading2 or unloading1 != unloading2 or scale1 != scale2)
                    and wb1.status == "approved"
                    and wb2.status == "approved"
                    and wb1.sender_id == wb2.sender_id
                    and wb1.receiver_id == wb2.receiver_id
                    and wb1.driver_id == wb2.driver_id
                ):
                    if wb1 not in duplicates_fare:
                        duplicates_fare.append(wb1)
                    if wb2 not in duplicates_fare:
                        duplicates_fare.append(wb2)

                # 3️⃣ اطلاعات متفاوت
                elif (
                    (wb1.sender_id != wb2.sender_id or
                     wb1.receiver_id != wb2.receiver_id or
                     wb1.driver_id != wb2.driver_id)
                    and wb1.status == "approved"
                    and wb2.status == "approved"
                ):
                    if wb1 not in duplicates_info:
                        duplicates_info.append(wb1)
                    if wb2 not in duplicates_info:
                        duplicates_info.append(wb2)

    context = {
        "duplicates_cargo": duplicates_cargo,
        "duplicates_fare": duplicates_fare,
        "duplicates_info": duplicates_info,
    }

    return render(request, "duplicate_audit/duplicate_audit_list.html", context)