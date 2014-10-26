'''
Created on 23 Sep 2014

@author: germs
'''
from django.forms import Form
from django.forms.fields import ChoiceField
from OneEvent.models import ParticipantOption, EventChoiceOption, Event, Message
from django.forms.models import ModelForm
from django.core.urlresolvers import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Reset
from crispy_forms.bootstrap import TabHolder, Tab


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

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('manage_event',
                                          kwargs={'event_id': self.instance.id})

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-6'
        self.helper.layout = TabHolder(
            Tab('Basics', 'title', 'start', 'end', 'city', 'pub_status'),
            Tab('Venue', 'location_name', 'location_address'),
            Tab('Organisers', 'owner', 'organisers'),
            Tab('Closing Dates', 'booking_close', 'choices_close'),
            Tab('Prices', 'price_for_employees', 'price_for_contractors', 'price_currency'),
            Tab('Employee/Contractor Groups', 'employees_groups', 'contractors_groups')
        )
        self.helper.add_input(Submit('submit', 'Save Changes'))
        self.helper.add_input(Reset('reset', 'Reset'))


class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['category', 'title', 'text']


class ReplyMessageForm(MessageForm):
    class Meta(MessageForm.Meta):
        fields = ['text']
