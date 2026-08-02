from django.urls import path

from issuance.views.manager.approval import send_for_approval, approve_bijak, reject_bijak
from issuance.views.manager.manager_preview import manager_preview_page
from issuance.views.manager.bijak_print import bijak_print
from issuance.views.manager.review_pending_list import waiting_list
from issuance.views.manager.review_status_list import final_status_list
from issuance.views.manager.manager_status import manager_set_final_status
from issuance.views.driver_views import driver_list

app_name = 'manager'

urlpatterns = [
    # مدیر
    path('waiting/', waiting_list, name='waiting_list'),
    path('status/', final_status_list, name='status_list'),
    path('bijak/<int:pk>/preview/', manager_preview_page, name="manager_preview"),
    path('bijaks/<int:pk>/status', manager_set_final_status, name='manager_status'),
    # path('bijaks/status', bijak_status_list, name='manager_status'),
    # path('bijaks/<int:pk>/update_status/', bijak_update_status, name='bijak_update_status'),
    # path('bijaks/<int:pk>/quick/<str:status>/', bijak_quick_status, name='bijak_quick_status'),
    path('<int:bijak_id>/send/', send_for_approval, name='send_for_approval'),
    path('<int:bijak_id>/approve/', approve_bijak, name='approve_bijak'),
    path('<int:bijak_id>/reject/', reject_bijak, name='reject_bijak'),
    path("drivers/", driver_list, name="driver_list"),
    # چاپ بارنامه
    path('<int:bijak_id>/print/', bijak_print, name='bijak_print'),
]
