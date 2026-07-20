# qr_code/urls.py
from django.urls import path
from issuance.views.bijak_qr_views import bijak_qr

app_name = 'qr_code'

urlpatterns = [
    path("barnameh/<int:pk>/qr/", bijak_qr, name="bijak_qr"),
]
