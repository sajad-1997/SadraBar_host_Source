from django.contrib import admin
from .models import Customer, Driver, Vehicle, Bijak, BijakApprovalLog
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.utils.safestring import mark_safe


class BijakApprovalLogInline(admin.TabularInline):
    model = BijakApprovalLog
    extra = 0
    readonly_fields = ('action', 'user', 'reason', 'timestamp')
    can_delete = False
    verbose_name = "تاریخچه تأیید/رد"
    verbose_name_plural = "تاریخچه تأیید/رد"


class BijakAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_code',
        'issuance_date',
        'sender',
        'receiver',
        'value',
        'approval_status',
        'approved_by',
    )

    readonly_fields = ('tracking_code', 'issuance_date', 'approved_by', 'approval_status')
    inlines = [BijakApprovalLogInline]
    list_filter = ('approval_status', 'issuance_date', 'sender', 'receiver')

    # ----------------------
    # لیست و آمار
    # ----------------------
    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)

        # گروه‌بندی روزانه
        daily_counts = qs.annotate(day=TruncDay('issuance_date')).values('day').annotate(
            count=Count('id'),
            total_freight=Sum('total_fare'),
            total_insurance=Sum('insurance')
        ).order_by('-day')

        # گروه‌بندی هفتگی
        weekly_counts = qs.annotate(week=TruncWeek('issuance_date')).values('week').annotate(
            count=Count('id'),
            total_freight=Sum('total_fare'),
            total_insurance=Sum('insurance')
        ).order_by('-week')

        # گروه‌بندی ماهانه
        monthly_counts = qs.annotate(month=TruncMonth('issuance_date')).values('month').annotate(
            count=Count('id'),
            total_freight=Sum('total_fare'),
            total_insurance=Sum('insurance')
        ).order_by('-month')

        # گروه‌بندی سالانه
        yearly_counts = qs.annotate(year=TruncYear('issuance_date')).values('year').annotate(
            count=Count('id'),
            total_freight=Sum('total_fare'),
            total_insurance=Sum('insurance')
        ).order_by('-year')

        # محاسبه مبلغ ۲۰ هزار تومان به ازای هر بارنامه
        for stat in (daily_counts, weekly_counts, monthly_counts, yearly_counts):
            for item in stat:
                item['extra_20k'] = (item['count'] or 0) * 20000

        # ایجاد HTML برای نمایش خلاصه آمار در بالا
        def render_summary(title, stats, date_field):
            html = f"<h4>{title}</h4><table border='1' cellpadding='5'><tr><th>{date_field}</th><th>تعداد بارنامه</th><th>جمع کرایه</th><th>جمع بیمه</th><th>۲۰ هزار تومان x تعداد</th></tr>"
            for item in stats:
                date_val = item.get(date_field.lower()) or ''
                html += f"<tr><td>{date_val}</td><td>{item['count'] or 0}</td><td>{item['total_freight'] or 0}</td><td>{item['total_insurance'] or 0}</td><td>{item['extra_20k']}</td></tr>"
            html += "</table><br>"
            return html

        summary_html = ""
        summary_html += render_summary("آمار روزانه", daily_counts, "day")
        summary_html += render_summary("آمار هفتگی", weekly_counts, "week")
        summary_html += render_summary("آمار ماهانه", monthly_counts, "month")
        summary_html += render_summary("آمار سالانه", yearly_counts, "year")

        extra_context = extra_context or {}
        extra_context['summary_html'] = mark_safe(summary_html)

        return super().changelist_view(request, extra_context=extra_context)
