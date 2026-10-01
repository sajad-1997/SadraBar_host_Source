from django.urls import path

from . import panel_views, views

app_name = "driver_queue"

urlpatterns = [
    # بخش رانندگان
    path("", views.landing, name="landing"),
    path("identify/", views.identify, name="identify"),
    path("register/", views.register, name="register"),
    path("register/done/", views.register_done, name="register_done"),
    path("room/", views.queue, name="queue"),
    path("join/", views.join, name="join"),
    path("status/", views.queue_status_api, name="status_api"),
    path("announce/<uuid:token>/<str:action>/", views.announce_respond, name="announce_respond"),
    path("location/", views.report_location, name="report_location"),

    # پنل کارکنان و مدیریت
    path("panel/", panel_views.dashboard, name="panel_dashboard"),
    path("panel/tickets/add/", panel_views.ticket_add, name="panel_ticket_add"),
    path("panel/tickets/<int:pk>/loaded/", panel_views.ticket_loaded, name="panel_ticket_loaded"),
    path("panel/tickets/<int:pk>/remove/", panel_views.ticket_remove, name="panel_ticket_remove"),
    path("panel/drivers/<int:pk>/", panel_views.driver_detail, name="panel_driver_detail"),
    path("panel/drivers/<int:pk>/approve/", panel_views.driver_approve, name="panel_driver_approve"),
    path("panel/users/", panel_views.users_list, name="panel_users"),
    path("panel/users/add/", panel_views.user_add, name="panel_user_add"),
    path("panel/users/<int:pk>/toggle/", panel_views.user_toggle, name="panel_user_toggle"),
    path("panel/users/<int:pk>/remove/", panel_views.user_remove, name="panel_user_remove"),
]