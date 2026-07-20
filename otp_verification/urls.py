from django.urls import path
from . import views

app_name = 'otp_verification'
urlpatterns = [
    path('request/', views.request_otp, name='request_otp'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('success/', views.success_page, name='success_page'),
]