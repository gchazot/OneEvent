'''
Created on 23 Sep 2014

@author: germs
'''
from django.forms import Form
from django.forms.fields import ChoiceField
from OneEvent.models import Event, EventChoice, EventChoiceOption, ParticipantOption, Message
from django.forms.models import ModelForm, inlineformset_factory
from django.core.urlresolvers import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Reset, Layout, Field, Div, HTML
from crispy_forms.bootstrap import TabHolder, Tab, FormActions
from django.core.exceptions import ValidationError


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
        if self.instance.pk:
            self.helper.form_action = reverse('edit_event',
                                              kwargs={'event_id': self.instance.id})
        else:
            self.helper.form_action = reverse('event_create')

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
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Reset('reset', 'Reset'))


class ChoiceForm(ModelForm):
    class Meta:
        model = EventChoice
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
                    reverse('edit_event', kwargs={'event_id': self.instance.event.id}))),
                css_class='text-center'
            )
        )
        self.helper.label_class = 'col-xs-3'
        self.helper.field_class = 'col-xs-7'


OptionFormSetBase = inlineformset_factory(EventChoice, EventChoiceOption,
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


class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['category', 'title', 'text']


class ReplyMessageForm(MessageForm):
    class Meta(MessageForm.Meta):
        fields = ['text']
