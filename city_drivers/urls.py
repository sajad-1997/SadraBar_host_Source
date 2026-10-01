from django.urls import path

from . import views
from .views import driver_dashboard

app_name = 'city_drivers'

urlpatterns = [
    # داشبورد
    path('', views.dashboard, name='dashboard'),
    path('report/daily/', views.managers_daily_report, name='managers_daily_report'),

    # داشبورد راننده
    path('driver/login/', driver_dashboard.driver_login, name='driver_login'),
    path('driver/logout/', driver_dashboard.driver_logout, name='driver_logout'),
    path('driver/dashboard/', driver_dashboard.driver_dashboard, name='driver_dashboard'),
    path('driver/service/<int:service_id>/update/', driver_dashboard.update_service_status, name='driver_update_status'),
    path('driver/api/queue/', driver_dashboard.api_driver_queue, name='driver_api_queue'),

    # مشتریان شهری
    path('customers/', views.urban_customer_list, name='urban_customer_list'),
    path('customers/add/', views.urban_customer_create, name='urban_customer_create'),
    path('customers/<int:pk>/edit/', views.urban_customer_edit, name='urban_customer_edit'),
    path('customers/search/', views.urban_customer_search, name='urban_customer_search'),

    # درخواست‌های سرویس
    path('requests/', views.urban_request_list, name='urban_request_list'),
    path('requests/add/', views.urban_request_create, name='urban_request_create'),
    path('requests/<int:pk>/edit/', views.urban_request_edit, name='urban_request_edit'),
    path('requests/<int:pk>/assign/', views.urban_request_assign, name='urban_request_assign'),
    path('requests/<int:pk>/status/', views.urban_request_status, name='urban_request_status'),

    # نوبت و حضور رانندگان
    path('queue/', views.urban_queue, name='urban_queue'),
    path('queue/attendance/', views.urban_queue_set_attendance, name='urban_queue_set_attendance'),

    # نرخ‌نامه و محاسبه کرایه
    path('rates/', views.urban_rate_list, name='urban_rate_list'),
    path('rates/add/', views.urban_rate_create, name='urban_rate_create'),
    path('rates/<int:pk>/edit/', views.urban_rate_edit, name='urban_rate_edit'),
    path('rates/<int:pk>/toggle/', views.urban_rate_toggle, name='urban_rate_toggle'),
    path('rates/calculator/', views.urban_fare_calculator, name='urban_fare_calculator'),

    # موقعیت رانندگان
    path('locations/', views.urban_locations_map, name='urban_locations_map'),
    path('api/locations/', views.api_locations, name='api_locations'),
    path('api/locations/update/', views.api_update_location, name='api_update_location'),

    # بدهی کمیسیون
    path('debts/', views.urban_debts_list, name='urban_debts_list'),
    path('debts/<int:pk>/settle/', views.urban_debt_settle, name='urban_debt_settle'),
]
