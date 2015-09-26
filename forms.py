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
from django.forms import Form
from django.forms.fields import ChoiceField
from OneEvent.models import Event, Choice, Option, Booking, BookingOption, Message
from django.forms.models import ModelForm, inlineformset_factory, ModelMultipleChoiceField,\
    ModelChoiceField
from django.core.urlresolvers import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Reset, Layout, Field, Div, HTML, Button
from crispy_forms.bootstrap import TabHolder, Tab, FormActions
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group


class SessionChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_label()


class BookingSessionForm(ModelForm):
    session = SessionChoiceField(label='Select your session', queryset=None, required=True)

    class Meta:
        model = Booking
        fields = ['session']

    def __init__(self, target_url, *args, **kwargs):
        super(BookingSessionForm, self).__init__(*args, **kwargs)

        self.fields['session'].queryset = self.instance.event.sessions.all()

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse(target_url,
                                          kwargs={'booking_id': self.instance.id})
        self.helper.layout = Layout('session',
                                    FormActions(Submit('save', 'Confirm',
                                                       css_class='btn btn-success'),
                                                Reset('reset', 'Reset',
                                                      css_class='btn btn-warning')))


class BookingChoicesForm(Form):
    choice_id_stem = 'choice_'
    session_field = 'session'

    def __init__(self, booking, *args, **kwargs):
        super(BookingChoicesForm, self).__init__(*args, **kwargs)
        self.booking = booking

        # Adding form fields for each choice in the event
        choice_field_names = []
        for choice in booking.event.choices.all():
            field_name = (self.choice_id_stem + '{0}').format(choice.id)
            choice_field_names.append(field_name)
            options = list(choice.options.all())
            options.sort(key=self._scoreOption)
            options_choices = [(opt.id, opt.title) for opt in options]
            self.fields[field_name] = ChoiceField(label=choice.title,
                                                  choices=options_choices)

        # Define the Crispy Form helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('booking_update',
                                          kwargs={'booking_id': self.booking.id})
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(Div(*choice_field_names),
                                    FormActions(Submit('save', 'Save',
                                                       css_class='btn btn-success'),
                                                Reset('reset', 'Reset',
                                                      css_class='btn btn-warning')))

    def _scoreOption(self, option):
        '''
        Give a "score" to the given option to allow sorting in the option selection drop-down
        If the option is the selected one, the score is 0.
        If it is the default, the score is 1.
        Otherwise the score is 2.
        '''
        try:
            self.booking.options.get(option=option)
            return 0
        except BookingOption.DoesNotExist:
            if option.default:
                return 1
        return 2

    def save(self):
        '''
        Update Booking with details selected in the validated form
        '''
        for name, value in self.cleaned_data.items():
            if name.startswith(self.choice_id_stem):
                choice_id = int(name[len(self.choice_id_stem):])
                bk_option, _ = self.booking.options.get_or_create(option__choice=choice_id)
                bk_option.option = Option.objects.get(id=value)
                bk_option.save()


class EventForm(ModelForm):
    employees_groups = ModelMultipleChoiceField(required=False,
                                                queryset=Group.objects.all().order_by('name'))
    contractors_groups = ModelMultipleChoiceField(required=False,
                                                  queryset=Group.objects.all().order_by('name'))

    class Meta:
        model = Event

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if self.instance.pk:
            self.helper.form_action = reverse('event_update',
                                              kwargs={'event_id': self.instance.id})
        else:
            self.helper.form_action = reverse('event_create')

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-6'
        self.helper.layout = TabHolder(
            Tab('Basics', 'title', 'start', 'end', 'city', 'pub_status'),
            Tab('Description', 'description'),
            Tab('Venue', 'location_name', 'location_address'),
            Tab('Organisers', 'owner', 'organisers'),
            Tab('Booking limits', 'max_participant', 'booking_close', 'choices_close'),
            Tab('Prices', 'price_for_employees', 'price_for_contractors', 'price_currency'),
            Tab('Employee/Contractor Groups', 'employees_groups', 'contractors_groups')
        )
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Reset('reset', 'Reset'))


class ChoiceForm(ModelForm):
    class Meta:
        model = Choice
        fields = ['title']

    def __init__(self, *args, **kwargs):
        super(ChoiceForm, self).__init__(*args, **kwargs)

        self.fields['title'].label = 'Choice Title'

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('title'),
            FormActions(
                Submit('save', 'Save', css_class='btn-success'),
                Reset('reset', 'Reset', css_class='btn-warning'),
                HTML('<a href="{0}" class="btn btn-danger">Cancel</a>'.format(
                    reverse('event_update', kwargs={'event_id': self.instance.event.id}))),
                css_class='text-center'
            )
        )
        self.helper.label_class = 'col-xs-3'
        self.helper.field_class = 'col-xs-7'


OptionFormSetBase = inlineformset_factory(Choice, Option,
                                          extra=3, can_delete=True)


class OptionFormSet(OptionFormSetBase):
    def clean(self):
        '''
        Validate that the overall set of options is valid
        '''
        super(OptionFormSet, self).clean()
        # If any error in underlying forms, don't bother
        if any(self.errors):
            return

        # Check that a single "Default" Option will remain and store it
        self.new_default = None
        for form in self.forms:
            if form.instance.default and not form.cleaned_data['DELETE']:
                if self.new_default is not None:
                    raise ValidationError("You can not have more than one Default Option.")
                else:
                    self.new_default = form.instance
        if self.new_default is None:
            raise ValidationError("You must have one Default Option.")

        # Store the deleted Options
        self.deleted_options = [form.instance
                                for form in self.deleted_forms
                                if form.instance.pk]


class OptionFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(OptionFormSetHelper, self).__init__(*args, **kwargs)

        self.form_tag = False
        self.layout = Layout(
            Div(
                Div(
                    HTML('Option #{{ forloop.counter }}'),
                    css_class='panel-heading'
                ),
                Div(
                    Div(
                        Field('title'),
                        css_class='row'
                    ),
                    Div(
                        Div(css_class='col-xs-2'),
                        Div(
                            Field('default'),
                            css_class='col-xs-2'
                        ),
                        Div(
                            Field('DELETE'),
                            css_class='col-xs-2'
                        ),
                        css_class='row'
                    ),
                    css_class='panel-body'
                ),
                css_class='panel panel-info'
            )
        )
        self.label_class = 'col-xs-2'
        self.field_class = 'col-xs-9'


class CreateBookingOnBehalfForm(Form):
    username = ChoiceField(label='Create a booking for',
                           choices=((u.username, u.get_full_name())
                                    for u in User.objects.order_by('last_name', 'first_name')))

    def __init__(self, event_id, *args, **kwargs):
        super(CreateBookingOnBehalfForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('booking_create_on_behalf',
                                          kwargs={'event_id': event_id})
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-6'
        self.helper.add_input(Submit('submit', 'Create Booking'))


class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['category', 'title', 'text']


class ReplyMessageForm(MessageForm):
    class Meta(MessageForm.Meta):
        fields = ['text']
