from django.urls import path
from . import views

app_name = 'printing'
urlpatterns = [
    path('request/', views.request_print_permission, name='request_print'),
    path('verify/', views.verify_otp, name='verify_otp'),
    # path('print/<str:waybill_number>/', views.print_waybill, name='print_waybill'),
    path('api/request-otp/', views.api_request_otp, name='api_request_otp'),
    path('api/verify-otp/', views.api_verify_otp, name='api_verify_otp'),
]
