from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .. import services
from ..models import CommissionDebt
from ..permissions import urban_access_required, urban_permissions_map
from .dashboard import REMAINING_EXPR


@urban_access_required('can_urban_manage_settlements')
def urban_debts_list(request):
    """لیست بدهکاران کمیسیون پرداخت‌نشده به آژانس"""
    show_settled = request.GET.get('all') == '1'
    qs = CommissionDebt.objects.select_related('driver', 'service_request')
    if not show_settled:
        qs = qs.filter(is_settled=False)
    debts = qs.annotate(remaining=REMAINING_EXPR)

    total_debt = (CommissionDebt.objects.filter(is_settled=False)
                  .annotate(remaining=REMAINING_EXPR)
                  .aggregate(total=Sum('remaining'))['total'] or Decimal(0))

    context = {
        'urban_perms': urban_permissions_map(request.user),
        'debts': debts,
        'total_debt': total_debt,
        'show_settled': show_settled,
    }
    return render(request, 'city_drivers/debts/urban_debts.html', context)


@require_POST
@urban_access_required('can_urban_manage_settlements')
def urban_debt_settle(request, pk):
    """تسویه (کامل یا قسمتی) بدهی کمیسیون"""
    debt = get_object_or_404(CommissionDebt, pk=pk)
    try:
        amount = Decimal(request.POST.get('amount') or 0)
    except InvalidOperation:
        messages.error(request, 'مبلغ پرداخت نامعتبر است.')
        return redirect('city_drivers:urban_debts_list')

    try:
        services.settle_debt(debt, amount, user=request.user,
                             note=request.POST.get('note') or '')
        messages.success(request, 'پرداخت بدهی با موفقیت ثبت شد.')
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect('city_drivers:urban_debts_list')
