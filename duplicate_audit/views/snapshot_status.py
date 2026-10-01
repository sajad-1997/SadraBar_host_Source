from django.shortcuts import get_object_or_404, redirect

from duplicate_audit.models.snapshot import DuplicateWaybillSnapshot


def update_snapshot_status(request, snapshot_id, decision):
    snapshot = get_object_or_404(DuplicateWaybillSnapshot, id=snapshot_id)
    snapshot.final_decision = decision
    snapshot.save()
    return redirect('duplicate_audit:list')
