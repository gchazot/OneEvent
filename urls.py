'''
Created on 22 Sep 2014

@author: gchazot
'''
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'OneEvent.views',
    url(r'^$', 'index', name='index'),
    url(r'^my_events/$', 'my_events', name='my_events'),
    url(r'^fut_events/$', 'future_events', name='future_events'),
    url(r'^past_events/$', 'past_events', name='past_events'),
    url(r'^all_events/$', 'all_events', name='all_events'),
    url(r'^manage_event/(?P<event_id>\d+)/$', 'manage_event', name='manage_event'),
    url(r'^dl_event_options_summary/(?P<event_id>\d+)/$', 'dl_event_options_summary', name='dl_event_options_summary'),
    url(r'^dl_participants_list/(?P<event_id>\d+)/$', 'dl_participants_list', name='dl_participants_list'),
    url(r'^confirm_payment/(?P<booking_id>\d+)/$', 'confirm_payment', name='confirm_payment'),
    url(r'^cancel_payment/(?P<booking_id>\d+)/$', 'confirm_payment', name='cancel_payment', kwargs={'cancel': True}),
    url(r'^create_booking/(?P<event_id>\d+)/$', 'create_booking', name='create_booking'),
    url(r'^update_booking/(?P<booking_id>\d+)/$', 'update_booking', name='update_booking'),
    url(r'^cancel_booking/(?P<booking_id>\d+)/$', 'cancel_booking', name='cancel_booking'),
)
