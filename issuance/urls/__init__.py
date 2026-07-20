from django.urls import path, include

urlpatterns = [
    # مسیرهای CRUD (ایجاد و ویرایش مشتری، راننده، وسیله نقلیه و ...)
    path('', include('issuance.urls.crud_urls')),

    # مسیرهای جستجو و AJAX
    path('', include('issuance.urls.search_urls')),

    # مسیرهای مربوط به QR بارنامه
    path('', include('issuance.urls.qr_urls')),

    # مسیرهای تایید و رد بارنامه توسط مدیریت
    path('', include('issuance.urls.bijak_approval_urls')),

    # مسیرهای مربوط به مدیریت بارنامه
    path('manager/', include('issuance.urls.manager_urls')),

    # مسیرهای مربوط به گزارش‌ها
    path('report/', include('report.urls')),
]
