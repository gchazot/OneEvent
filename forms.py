'''
Created on 23 Sep 2014

@author: germs
'''
from django.forms import Form
from django.forms.fields import ChoiceField
from OneEvent.models import ParticipantOption, EventChoiceOption, Event, Message
from django.forms.models import ModelForm


class BookingForm(Form):
    choice_id_stem = 'choice_'

    def __init__(self, booking, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        self.booking = booking

        for choice in booking.event.choices.all():
            field_name = (self.choice_id_stem + '{0}').format(choice.id)
            options = list(choice.options.all())
            options.sort(key=self._scoreOption)
            options_choices = [(opt.id, opt.title) for opt in options]
            self.fields[field_name] = ChoiceField(label=choice.title,
                                                  choices=options_choices)

    def _scoreOption(self, option):
        try:
            self.booking.options.get(option=option)
            return 0
        except ParticipantOption.DoesNotExist:
            if option.default:
                return 1
        return 2

    def save(self):
        for name, value in self.cleaned_data.items():
            if name.startswith(self.choice_id_stem):
                choice_id = int(name[len(self.choice_id_stem):])
                bk_option, _ = self.booking.options.get_or_create(option__choice=choice_id)
                bk_option.option = EventChoiceOption.objects.get(id=value)
                bk_option.save()


class EventForm(ModelForm):
    class Meta:
        model = Event


class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['category', 'title', 'text']


class ReplyMessageForm(MessageForm):
    class Meta(MessageForm.Meta):
        fields = ['text']
