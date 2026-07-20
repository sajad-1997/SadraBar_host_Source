from django.urls import path

from ..views import *

app_name = 'crud'

urlpatterns = [
    path('create_new/', create_new, name='create_new'),
    path('pending/', pending_bijaks, name='pending'),
    path('print/<int:pk>/', print_page, name='print'),
    # path('bijak/access/<str:token>/', access_view, name='bijak_access'),
    # path('bijak/print/<str:token>/', print_view, name='print'),
    path('preview/<int:pk>/', preview_page, name='preview'),

    path('add-customer/', add_customer, name='add_customer'),
    path('duplicate-customer/', duplicate_customer, name="duplicate_customer"),
    path('add-driver/', add_driver, name='add_driver'),
    path('add-vehicle/', add_vehicle, name='add_vehicle'),
    path('add-caption/', add_caption, name='add_caption'),

    path('customers/edit/<int:pk>/', edit_customer, name='edit_customer'),
    path('driver/edit/<int:driver_id>/', edit_driver, name='edit_driver'),
    path('edit-vehicle/', edit_vehicle, name='edit_vehicle'),
    path('edit-cargo/', edit_cargo, name='edit_cargo'),
    path('edit-bijak/<int:pk>/', edit_bijak, name='edit_bijak'),

    path("save-sender/", save_customer, name="save_customer"),
    path("save-driver/", save_driver, name="save_driver"),

    # path('report/', include(('report.urls', 'report_dashboard'), namespace='report')),

]
