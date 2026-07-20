from django.urls import path

from .views.cluster_views import cluster_detail, scan_duplicates_ui
from .views.duplicate_audit_views import duplicate_audit_list
from .views.snapshot_status import update_snapshot_status

app_name = "duplicate_audit"

urlpatterns = [
    path("list/", duplicate_audit_list, name="duplicate_audit_list"),
    path("<int:cluster_id>/", cluster_detail, name="cluster_detail"),
    path("scan/", scan_duplicates_ui, name="scan_duplicates_ui"),
    path("update/<int:snapshot_id>/<str:decision>/",
         update_snapshot_status,
         name="update_snapshot_status"),
]
