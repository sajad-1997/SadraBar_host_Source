from django.db import transaction
from issuance.models import Bijak as Waybill
from ..models.snapshot import DuplicateWaybillSnapshot
from ..models.apply_log import DuplicateApplyLog
from ..models.released_code import ReleasedTrackingCode

def apply_snapshot(snapshot, user):
    waybill = Waybill.objects.select_for_update().get(id=snapshot.original_waybill_id)

    old_type = waybill.type
    old_tracking = waybill.tracking_code

    new_type = None
    new_tracking = old_tracking

    if snapshot.final_decision == "customer_copy":
        new_type = "draft"
        new_tracking = f"{snapshot.customer_id}-{old_tracking}"

    elif snapshot.final_decision == "inactive_duplicate":
        ReleasedTrackingCode.objects.create(code=old_tracking, cluster=snapshot.cluster)
        new_type = "inactive"
        new_tracking = "----"

    elif snapshot.final_decision == "sent":
        new_type = "sent"

    elif snapshot.final_decision == "canceled":
        new_type = "canceled"

    Waybill.objects.filter(id=waybill.id).update(
        type=new_type,
        tracking_code=new_tracking
    )

    DuplicateApplyLog.objects.create(
        original_waybill_id=waybill.id,
        old_status=old_type,
        new_status=new_type,
        old_tracking_code=old_tracking,
        new_tracking_code=new_tracking,
        applied_by=user
    )

def apply_cluster(cluster, user):
    from ..models.snapshot import DuplicateWaybillSnapshot

    if cluster.is_resolved:
        raise Exception("این Cluster قبلاً اعمال شده است.")

    undecided = cluster.duplicatewaybillsnapshot_set.filter(final_decision__isnull=True)
    if undecided.exists():
        raise Exception("تمام بارنامه‌ها باید تعیین تکلیف شوند.")

    with transaction.atomic():
        for snapshot in cluster.duplicatewaybillsnapshot_set.all():
            apply_snapshot(snapshot, user)
        cluster.is_resolved = True
        cluster.save(update_fields=["is_resolved"])