'''
@author: Germain CHAZOT

Copyright 2014-2015 Germain CHAZOT

This file is part of OneEvent.

OneEvent is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OneEvent is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OneEvent.  If not, see <http://www.gnu.org/licenses/>.
'''
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'OneEvent.views',
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
