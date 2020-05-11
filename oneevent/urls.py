from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("events/mine", views.events_list_mine, name="events_list_mine"),
    path("events/future", views.events_list_future, name="events_list_future"),
    path("events/past", views.events_list_past, name="events_list_past"),
    path("events/all", views.events_list_all, name="events_list_all"),
    path("events/archive", views.events_list_archived, name="events_list_archived"),
    path("event/create", views.event_create, name="event_create"),
    path("event/<int:event_id>/update", views.event_update, name="event_update"),
    path(
        "event/<int:event_id>/update_categories",
        views.event_update_categories,
        name="event_update_categories",
    ),
    path(
        "event/<int:event_id>/update_sessions",
        views.event_update_sessions,
        name="event_update_sessions",
    ),
    path("event/<int:event_id>/manage", views.event_manage, name="event_manage"),
    path(
        "event/<int:event_id>/options_summary",
        views.event_download_options_summary,
        name="event_download_options_summary",
    ),
    path(
        "event/<int:event_id>/participants_list",
        views.event_download_participants_list,
        name="event_download_participants_list",
    ),
    path("choice/create/<int:event_id>", views.choice_create, name="choice_create"),
    path("choice/<int:choice_id>/update", views.choice_update, name="choice_update"),
    path("choice/<int:choice_id>/delete", views.choice_delete, name="choice_delete"),
    path("booking/create/<int:event_id>", views.booking_create, name="booking_create"),
    path(
        "booking/create_on_behalf/<int:event_id>",
        views.booking_create_on_behalf,
        name="booking_create_on_behalf",
    ),
    path(
        "booking/<int:booking_id>/update", views.booking_update, name="booking_update"
    ),
    path(
        "booking/<int:booking_id>/session",
        views.booking_session_update,
        name="booking_session_update",
    ),
    path(
        "booking/<int:booking_id>/cancel", views.booking_cancel, name="booking_cancel"
    ),
    path(
        "booking/<int:booking_id>/payment/confirm",
        views.booking_payment_confirm,
        name="booking_payment_confirm",
    ),
    path(
        "booking/<int:booking_id>/payment/cancel",
        views.booking_payment_confirm,
        name="booking_payment_cancel",
        kwargs={"cancel": True},
    ),
    path(
        "booking/<int:booking_id>/payment/exempt",
        views.booking_payment_exempt,
        name="booking_payment_exempt",
    ),
    path(
        "booking/<int:booking_id>/payment/unexempt",
        views.booking_payment_exempt,
        name="booking_payment_unexempt",
        kwargs={"cancel": True},
    ),
    path(
        "booking/<int:booking_id>/send_invite",
        views.booking_send_invite,
        name="booking_send_invite",
    ),
    path("accounts/delete", views.user_delete, name="user_delete"),
]
