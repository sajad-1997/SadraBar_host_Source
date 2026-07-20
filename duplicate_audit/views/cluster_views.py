from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from ..models.cluster import DuplicateCluster
from ..services.apply_service import apply_cluster
from ..services.scan_service import scan_duplicates


def is_admin_or_manager(user):
    return user.groups.filter(name__in=["admin", "manager"]).exists()


# @user_passes_test(is_admin_or_manager)
def cluster_list(request):
    clusters = DuplicateCluster.objects.all().order_by("-created_at")
    return render(request, "duplicate_audit/cluster_list.html", {"clusters": clusters})


# @user_passes_test(is_admin_or_manager)
def cluster_detail(request, cluster_id):
    cluster = get_object_or_404(DuplicateCluster, id=cluster_id)
    snapshots = cluster.duplicatewaybillsnapshot_set.all()
    has_undecided = snapshots.filter(final_decision__isnull=True).exists()
    if request.method == "POST":
        apply_cluster(cluster, request.user)
        return redirect("duplicate_audit:duplicate_audit_list")
    return render(request, "duplicate_audit/cluster_detail.html", {
        "cluster": cluster,
        "snapshots": snapshots,
        "has_undecided": has_undecided
    })

@require_POST
# @user_passes_test(is_admin_or_manager)
def scan_duplicates_ui(request):
    clusters = scan_duplicates()
    messages.success(request, f"{len(clusters)} Cluster جدید ساخته شد.")
    return redirect('duplicate_audit:duplicate_audit_list')
