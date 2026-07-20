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


def forbidden_view(request):
    return render(request, 'accounts/forbidden.html', status=403)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('', include('homePage.urls')),
    path('issuance/', include(('issuance.urls', 'issuance'), namespace='issuance')),
    # path('duplicate/', include('duplicate_audit.urls', namespace='duplicate_audit')),
    path('report/', include(('report.urls', 'report'), namespace='report')),
    path('forbidden/', forbidden_view, name='forbidden'),
    # path('publish/', include('publish.urls', namespace='publish')),
    path('otp/', include(('otp_verification.urls', 'otp_verification'), namespace='otp_verification')),
    path('printing/', include(('printing.urls', 'printing'), namespace='printing'))


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)