from django.urls import path

from issuance.views.manager.bijak_approval import (
    bijak_approve_view,
    bijak_approve_submit,
    bijak_list_waiting_approval,
)

app_name = 'bijak_approval'

urlpatterns = [
    path('bijak/approvals/', bijak_list_waiting_approval, name='bijak_list_waiting_approval'),
    path('bijak/<int:pk>/approve/', bijak_approve_view, name='bijak_approve'),
    path('bijak/<int:pk>/approve/submit/', bijak_approve_submit, name='bijak_approve_submit'),
]
