'''
Created on 22 Sep 2014

@author: gchazot
'''
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'OneEvent.views',
    url(r'^$', 'index', name='index'),
    url(r'^events/mine$', 'my_events', name='my_events'),
    url(r'^events/future$', 'future_events', name='future_events'),
    url(r'^events/past$', 'past_events', name='past_events'),
    url(r'^events/all$', 'all_events', name='all_events'),

    url(r'^event/new$', 'event_create', name='event_create'),
    url(r'^event/(?P<event_id>\d+)$', 'manage_event', name='manage_event'),
    url(r'^event/(?P<event_id>\d+)/edit$', 'edit_event', name='edit_event'),
    url(r'^event/(?P<event_id>\d+)/options_summary$', 'dl_event_options_summary',
        name='dl_event_options_summary'),
    url(r'^event/(?P<event_id>\d+)/participants_list$', 'dl_participants_list',
        name='dl_participants_list'),
    url(r'^event/(?P<event_id>\d+)/book$', 'create_booking', name='create_booking'),
    url(r'^event/(?P<event_id>\d+)/book_on_behalf$', 'create_booking_on_behalf',
        name='create_booking_on_behalf'),
    url(r'^event/(?P<event_id>\d+)/new_choice$', 'add_choice', name='add_choice'),

    url(r'^choice/(?P<choice_id>\d+)$', 'edit_choice', name='edit_choice'),
    url(r'^choice/(?P<choice_id>\d+)/delete$', 'delete_choice', name='delete_choice'),

    url(r'^booking/(?P<booking_id>\d+)$', 'update_booking', name='update_booking'),
    url(r'^booking/(?P<booking_id>\d+)/cancel$', 'cancel_booking', name='cancel_booking'),
    url(r'^booking/(?P<booking_id>\d+)/payment/confirm$', 'confirm_payment',
        name='confirm_payment'),
    url(r'^booking/(?P<booking_id>\d+)/payment/cancel$', 'confirm_payment',
        name='cancel_payment', kwargs={'cancel': True}),
    url(r'^booking/(?P<booking_id>\d+)/payment/exempt$', 'confirm_exempt',
        name='confirm_exempt'),
    url(r'^booking/(?P<booking_id>\d+)/payment/unexempt$', 'confirm_exempt',
        name='cancel_exempt', kwargs={'cancel': True}),
    url(r'^booking/(?P<booking_id>\d+)/send_invite$', 'send_booking_invite',
        name='send_booking_invite'),
    # This one is kept for backward compatibility
    url(r'^create_booking/(?P<event_id>\d+)/$', 'create_booking', name='create_booking'),

    url(r'^messages/$', 'view_messages', name='view_messages'),
    url(r'^messages/new/$', 'create_message', name='create_message'),
    url(r'^messages/reply/(?P<thread_id>\d+)/$', 'create_message', name='reply_message'),
)
