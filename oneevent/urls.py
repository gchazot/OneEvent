from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^events/mine$', views.events_list_mine, name='events_list_mine'),
    url(r'^events/future$', views.events_list_future, name='events_list_future'),
    url(r'^events/past$', views.events_list_past, name='events_list_past'),
    url(r'^events/all$', views.events_list_all, name='events_list_all'),
    url(r'^events/archive$', views.events_list_archived, name='events_list_archived'),

    url(r'^event/create$', views.event_create, name='event_create'),
    url(r'^event/(?P<event_id>\d+)/update$', views.event_update, name='event_update'),
    url(r'^event/(?P<event_id>\d+)/update_categories$', views.event_update_categories,
        name='event_update_categories'),
    url(r'^event/(?P<event_id>\d+)/update_sessions$', views.event_update_sessions,
        name='event_update_sessions'),
    url(r'^event/(?P<event_id>\d+)/manage$', views.event_manage, name='event_manage'),
    url(r'^event/(?P<event_id>\d+)/options_summary$', views.event_download_options_summary,
        name='event_download_options_summary'),
    url(r'^event/(?P<event_id>\d+)/participants_list$', views.event_download_participants_list,
        name='event_download_participants_list'),

    url(r'^choice/create/(?P<event_id>\d+)$', views.choice_create, name='choice_create'),
    url(r'^choice/(?P<choice_id>\d+)/update$', views.choice_update, name='choice_update'),
    url(r'^choice/(?P<choice_id>\d+)/delete$', views.choice_delete, name='choice_delete'),

    url(r'^booking/create/(?P<event_id>\d+)$', views.booking_create, name='booking_create'),
    url(r'^booking/create_on_behalf/(?P<event_id>\d+)$', views.booking_create_on_behalf,
        name='booking_create_on_behalf'),
    url(r'^booking/(?P<booking_id>\d+)/update$', views.booking_update, name='booking_update'),
    url(r'^booking/(?P<booking_id>\d+)/session$', views.booking_session_update, name='booking_session_update'),
    url(r'^booking/(?P<booking_id>\d+)/cancel$', views.booking_cancel, name='booking_cancel'),
    url(r'^booking/(?P<booking_id>\d+)/payment/confirm$', views.booking_payment_confirm,
        name='booking_payment_confirm'),
    url(r'^booking/(?P<booking_id>\d+)/payment/cancel$', views.booking_payment_confirm,
        name='booking_payment_cancel', kwargs={'cancel': True}),
    url(r'^booking/(?P<booking_id>\d+)/payment/exempt$', views.booking_payment_exempt,
        name='booking_payment_exempt'),
    url(r'^booking/(?P<booking_id>\d+)/payment/unexempt$', views.booking_payment_exempt,
        name='booking_payment_unexempt', kwargs={'cancel': True}),
    url(r'^booking/(?P<booking_id>\d+)/send_invite$', views.booking_send_invite,
        name='booking_send_invite'),

    url(r'^messages/$', views.messages_list, name='messages_list'),
    url(r'^message/create/$', views.message_create, name='message_create'),
    url(r'^message/create/(?P<thread_id>\d+)/$', views.message_create, name='message_reply'),
]
