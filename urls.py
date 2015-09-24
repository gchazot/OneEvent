'''
Created on 22 Sep 2014

@author: gchazot
'''
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'oneevent.views',
    url(r'^$', 'index', name='index'),

    url(r'^events/mine$', 'events_list_mine', name='events_list_mine'),
    url(r'^events/future$', 'events_list_future', name='events_list_future'),
    url(r'^events/past$', 'events_list_past', name='events_list_past'),
    url(r'^events/all$', 'events_list_all', name='events_list_all'),
    url(r'^events/archive$', 'events_list_archived', name='events_list_archived'),

    url(r'^event/create$', 'event_create', name='event_create'),
    url(r'^event/(?P<event_id>\d+)/update$', 'event_update', name='event_update'),
    url(r'^event/(?P<event_id>\d+)/manage$', 'event_manage', name='event_manage'),
    url(r'^event/(?P<event_id>\d+)/options_summary$', 'event_download_options_summary',
        name='event_download_options_summary'),
    url(r'^event/(?P<event_id>\d+)/participants_list$', 'event_download_participants_list',
        name='event_download_participants_list'),

    url(r'^choice/create/(?P<event_id>\d+)$', 'choice_create', name='choice_create'),
    url(r'^choice/(?P<choice_id>\d+)/update$', 'choice_update', name='choice_update'),
    url(r'^choice/(?P<choice_id>\d+)/delete$', 'choice_delete', name='choice_delete'),

    url(r'^booking/create/(?P<event_id>\d+)$', 'booking_create', name='booking_create'),
    url(r'^booking/create_on_behalf/(?P<event_id>\d+)$', 'booking_create_on_behalf',
        name='booking_create_on_behalf'),
    url(r'^booking/(?P<booking_id>\d+)/update$', 'booking_update', name='booking_update'),
    url(r'^booking/(?P<booking_id>\d+)/session$', 'booking_session_update', name='booking_session_update'),
    url(r'^booking/(?P<booking_id>\d+)/cancel$', 'booking_cancel', name='booking_cancel'),
    url(r'^booking/(?P<booking_id>\d+)/payment/confirm$', 'booking_payment_confirm',
        name='booking_payment_confirm'),
    url(r'^booking/(?P<booking_id>\d+)/payment/cancel$', 'booking_payment_confirm',
        name='booking_payment_cancel', kwargs={'cancel': True}),
    url(r'^booking/(?P<booking_id>\d+)/payment/exempt$', 'booking_payment_exempt',
        name='booking_payment_exempt'),
    url(r'^booking/(?P<booking_id>\d+)/payment/unexempt$', 'booking_payment_exempt',
        name='booking_payment_unexempt', kwargs={'cancel': True}),
    url(r'^booking/(?P<booking_id>\d+)/send_invite$', 'booking_send_invite',
        name='booking_send_invite'),

    url(r'^messages/$', 'messages_list', name='messages_list'),
    url(r'^message/create/$', 'message_create', name='message_create'),
    url(r'^message/create/(?P<thread_id>\d+)/$', 'message_create', name='message_reply'),
)
