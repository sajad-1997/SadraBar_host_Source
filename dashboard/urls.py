from django.urls import path, include

from .views import admin_dashboard, manager_dashboard, staff_dashboard, home_dashboard

app_name = 'dashboard'


urlpatterns = [
    path('admin/', admin_dashboard, name='admin_dashboard'),
    path('manager/', manager_dashboard, name='manager_dashboard'),
    path('staff/', staff_dashboard, name='staff_dashboard'),
    path('home/', home_dashboard, name='home_dashboard'),
    path('issuance/', include('issuance.urls.crud_urls', namespace='issuance')),

]
