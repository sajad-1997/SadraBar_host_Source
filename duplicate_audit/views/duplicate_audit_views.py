from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from duplicate_audit.models.cluster import DuplicateCluster
from duplicate_audit.models.snapshot import DuplicateWaybillSnapshot


def parse_amount(value):
    if not value:
        return 0
    try:
        return int(str(value).replace(",", "").strip())
    except:
        return 0


@login_required
def duplicate_audit_list(request):

    clusters = DuplicateCluster.objects.prefetch_related("snapshots")

    duplicates_cargo = []
    duplicates_fare = []
    duplicates_info = []

    for cluster in clusters:
        snapshots = list(cluster.snapshots.all())
        n = len(snapshots)

        for i in range(n):
            s1 = snapshots[i]

            weight1 = s1.cargo_weight
            freight1 = parse_amount(s1.freight_amount)
            value1 = parse_amount(s1.cargo_value)
            loading1 = parse_amount(s1.loading_cost)
            unloading1 = parse_amount(s1.unloading_cost)
            scale1 = parse_amount(s1.scale_cost)

            for j in range(i + 1, n):
                s2 = snapshots[j]

                weight2 = s2.cargo_weight
                freight2 = parse_amount(s2.freight_amount)
                value2 = parse_amount(s2.cargo_value)
                loading2 = parse_amount(s2.loading_cost)
                unloading2 = parse_amount(s2.unloading_cost)
                scale2 = parse_amount(s2.scale_cost)

                # 1️⃣ محموله متفاوت
                if (
                    weight1 != weight2 and
                    s1.sender_name == s2.sender_name and
                    s1.receiver_name == s2.receiver_name and
                    s1.driver_name == s2.driver_name
                ):
                    if s1 not in duplicates_cargo:
                        duplicates_cargo.append(s1)
                    if s2 not in duplicates_cargo:
                        duplicates_cargo.append(s2)

                # 2️⃣ هزینه متفاوت (فقط تایید شده)
                elif (
                    (freight1 != freight2 or value1 != value2 or
                     loading1 != loading2 or unloading1 != unloading2 or scale1 != scale2)
                    and s1.final_decision is None
                    and s2.final_decision is None
                    and s1.sender_name == s2.sender_name
                    and s1.receiver_name == s2.receiver_name
                    and s1.driver_name == s2.driver_name
                ):
                    if s1 not in duplicates_fare:
                        duplicates_fare.append(s1)
                    if s2 not in duplicates_fare:
                        duplicates_fare.append(s2)

                # 3️⃣ اطلاعات متفاوت
                elif (
                    (s1.sender_name != s2.sender_name or
                     s1.receiver_name != s2.receiver_name or
                     s1.driver_name != s2.driver_name)
                    and s1.final_decision is None
                    and s2.final_decision is None
                ):
                    if s1 not in duplicates_info:
                        duplicates_info.append(s1)
                    if s2 not in duplicates_info:
                        duplicates_info.append(s2)

    context = {
        "duplicates_cargo": duplicates_cargo,
        "duplicates_fare": duplicates_fare,
        "duplicates_info": duplicates_info,
    }

    return render(request, "duplicate_audit/cluster_list.html", context)