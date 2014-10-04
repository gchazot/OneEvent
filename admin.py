'''
Created on 5 Jun 2014

@author: germs
'''
from django.contrib import admin
from models import (Event, EventChoice, EventChoiceOption, ParticipantBooking,
                    ParticipantOption)

admin.site.register(Event)
admin.site.register(EventChoice)
admin.site.register(EventChoiceOption)
admin.site.register(ParticipantBooking)
admin.site.register(ParticipantOption)
