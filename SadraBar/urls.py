"""
URL configuration for SadraBar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from homePage import pwa_views




def forbidden_view(request, exception=None):
    return render(request, 'errors/403.html', {'exception': exception}, status=403)


urlpatterns = [
    path('manifest.webmanifest', pwa_views.manifest, name='pwa_manifest'),
    path('sw.js', pwa_views.service_worker, name='pwa_service_worker'),
    path('offline/', pwa_views.offline, name='pwa_offline'),
    path('pwa/queued/', pwa_views.queued, name='pwa_queued'),
    path('pwa/sync/ping/', pwa_views.sync_ping, name='pwa_sync_ping'),
    path('pwa/sync/status/', pwa_views.sync_status, name='pwa_sync_status'),
    path('browserconfig.xml', pwa_views.browserconfig, name='pwa_browserconfig'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('', include('homePage.urls')),
    path('issuance/', include(('issuance.urls', 'issuance'), namespace='issuance')),
    path('captions/', include(('captions.urls', 'captions'), namespace='captions')),
    path('cargo/', include(('cargo.urls', 'cargo'), namespace='cargo')),
    path('customers/', include(('customers.urls', 'customers'), namespace='customers')),
    path('drivers/', include(('drivers.urls', 'drivers'), namespace='drivers')),
    path('fleet/', include(('fleet.urls', 'fleet'), namespace='fleet')),
    path('duplicate/', include('duplicate_audit.urls', namespace='duplicate_audit')),
    path('report/', include(('report.urls', 'report'), namespace='report')),
    path('forbidden/', forbidden_view, name='forbidden'),
    # path('publish/', include('publish.urls', namespace='publish')),
    path('otp/', include(('otp_verification.urls', 'otp_verification'), namespace='otp_verification')),
    path('printing/', include(('printing.urls', 'printing'), namespace='printing')),
    path('driver-queue/', include(('driver_queue.urls', 'driver_queue'), namespace='driver_queue')),
    path('user-management/', include(('user_management.urls', 'user_management'), namespace='user_management')),
    path('system-control/', include(('system_control.urls', 'system_control'), namespace='system_control')),
    path('city-drivers/', include(('city_drivers.urls', 'city_drivers'), namespace='city_drivers')),

]

handler403 = forbidden_view

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
