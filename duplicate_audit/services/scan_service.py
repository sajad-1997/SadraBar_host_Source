from django.db import models
from issuance.models import Bijak as Waybill
from ..models.cluster import DuplicateCluster
from ..models.snapshot import DuplicateWaybillSnapshot

def scan_duplicates():
    """
    اسکن بارنامه ها و ایجاد Cluster و Snapshot بر اساس فیلدهای واقعی Waybill
    کاملاً امن و بدون خطای ValidationError
    """

    clusters = []

    # پیدا کردن رکوردهای تکراری بر اساس sender, receiver, driver
    duplicates = (
        Waybill.objects.values("sender", "receiver", "driver")
        .annotate(count=models.Count("id"))
        .filter(count__gt=1)
    )

    for dup in duplicates:
        # ایجاد Cluster جدید
        cluster = DuplicateCluster.objects.create(
            description=f"Duplicate for sender:{dup['sender']} - receiver:{dup['receiver']} - driver:{dup['driver']}"
        )

        # گرفتن تمام بارنامه‌های مربوط به این Cluster
        waybills = Waybill.objects.filter(
            sender_id=dup["sender"],
            receiver_id=dup["receiver"],
            driver_id=dup["driver"]
        )

        for wb in waybills:
            # ایجاد Snapshot
            DuplicateWaybillSnapshot.objects.create(
                cluster=cluster,
                original_waybill_id=wb.id,
                tracking_code=wb.tracking_code,
                issuer_name=getattr(wb.created_by, "username", "") if hasattr(wb, "created_by") else "",
                sender_name=wb.sender.name if wb.sender else "",
                receiver_name=wb.receiver.name if wb.receiver else "",
                driver_name=wb.driver.name if wb.driver else "",
                cargo_name=wb.cargo.name if wb.cargo else "",
                cargo_weight=getattr(wb.cargo, "weight", 0),
                freight_amount=wb.freight,       # ذخیره رشته بدون تبدیل
                cargo_value=wb.value,            # ذخیره رشته بدون تبدیل
                loading_cost=wb.loading_fee,
                unloading_cost=wb.unloading_fee,
                scale_cost=wb.scale_fee,
                description=getattr(wb, "final_description", "")
            )

        clusters.append(cluster)

    return clusters