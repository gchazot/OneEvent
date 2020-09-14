from django.forms import Form
from django.forms.fields import ChoiceField, SplitDateTimeField
from .models import Event, Session, Category, Choice, Option, Booking, BookingOption
from django.forms.models import ModelForm, inlineformset_factory, ModelChoiceField
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Reset, Layout, Field, Div, HTML
from crispy_forms.bootstrap import TabHolder, Tab, FormActions
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


def datetime_help_string():
    from datetime import datetime
    from django.conf import settings

    now = datetime(1969, 0o7, 20, 20, 17, 40)
    return "manual formats: {0} and {1}".format(
        now.strftime(settings.DATE_INPUT_FORMATS[0]),
        now.strftime(settings.TIME_INPUT_FORMATS[0]),
    )


class MySplitDateTimeField(SplitDateTimeField):
    """A field with separate date and time elements and using HTML5 input types"""

    def __init__(self, *args, **kwargs):
        super(MySplitDateTimeField, self).__init__(*args, **kwargs)
        self.widget.widgets[0].input_type = "date"
        self.widget.widgets[1].input_type = "time"


class SessionChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_label()


class BookingSessionForm(ModelForm):
    session = SessionChoiceField(
        label="Select your session", queryset=None, required=True
    )

    class Meta:
        model = Booking
        fields = ["session"]

    def __init__(self, target_url, *args, **kwargs):
        super(BookingSessionForm, self).__init__(*args, **kwargs)

        self.fields["session"].queryset = self.instance.event.sessions.all()

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse(
            target_url, kwargs={"booking_id": self.instance.id}
        )
        self.helper.layout = Layout(
            "session",
            FormActions(
                Submit("save", "Confirm", css_class="btn btn-success"),
                Reset("reset", "Reset", css_class="btn btn-warning"),
            ),
        )


class BookingChoicesForm(Form):
    choice_id_stem = "choice_"
    session_field = "session"

    def __init__(self, booking, *args, **kwargs):
        super(BookingChoicesForm, self).__init__(*args, **kwargs)
        self.booking = booking

        # Adding form fields for each choice in the event
        choice_field_names = []
        for choice in booking.event.choices.all():
            field_name = (self.choice_id_stem + "{0}").format(choice.id)
            choice_field_names.append(field_name)
            options = list(choice.options.all())
            options.sort(key=self._scoreOption)
            options_choices = [(opt.id, opt.title) for opt in options]
            self.fields[field_name] = ChoiceField(
                label=choice.title, choices=options_choices
            )

        # Define the Crispy Form helper
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse(
            "booking_update", kwargs={"booking_id": self.booking.id}
        )
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-3"
        self.helper.field_class = "col-lg-9"
        self.helper.layout = Layout(
            Div(*choice_field_names),
            FormActions(
                Submit("save", "Save", css_class="btn btn-success"),
                Reset("reset", "Reset", css_class="btn btn-warning"),
            ),
        )

    def _scoreOption(self, option):
        """
        Give a "score" to the given option for sorting in the option selection drop-down
        If the option is the selected one, the score is 0.
        If it is the default, the score is 1.
        Otherwise the score is 2.
        """
        try:
            self.booking.options.get(option=option)
            return 0
        except BookingOption.DoesNotExist:
            if option.default:
                return 1
        return 2

    def save(self):
        """
        Update Booking with details selected in the validated form
        """
        for name, value in self.cleaned_data.items():
            if name.startswith(self.choice_id_stem):
                choice_id = int(name[len(self.choice_id_stem) :])
                bk_option, _ = self.booking.options.get_or_create(
                    option__choice=choice_id
                )
                bk_option.option = Option.objects.get(id=value)
                bk_option.save()


class EventForm(ModelForm):
    start = MySplitDateTimeField(
        required=True,
        help_text="Local start date and time ({0})".format(datetime_help_string()),
    )
    end = MySplitDateTimeField(
        required=False,
        help_text="Local end date and time ({0})".format(datetime_help_string()),
    )
    booking_close = MySplitDateTimeField(
        required=False,
        help_text="Limit date and time for registering ({0})".format(
            datetime_help_string()
        ),
    )
    choices_close = MySplitDateTimeField(
        required=False,
        help_text="Limit date and time for changing choices ({0})".format(
            datetime_help_string()
        ),
    )

    class Meta:
        model = Event
        fields = [
            "title",
            "start",
            "end",
            "timezone",
            "description",
            "pub_status",
            "location_name",
            "location_address",
            "owner",
            "organisers",
            "booking_close",
            "choices_close",
            "max_participant",
            "price_currency",
        ]

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        if self.instance.pk:
            self.helper.form_action = reverse(
                "event_update", kwargs={"event_id": self.instance.id}
            )
        else:
            self.helper.form_action = reverse("event_create")

        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-3"
        self.helper.field_class = "col-lg-6"
        self.helper.layout = TabHolder(
            Tab("Basics", "title", "start", "end", "timezone", "pub_status"),
            Tab("Description", "description"),
            Tab("Venue", "location_name", "location_address"),
            Tab("Organisers", "owner", "organisers"),
            Tab("Booking limits", "max_participant", "booking_close", "choices_close"),
            Tab("Settings", "price_currency"),
        )
        self.helper.add_input(Submit("submit", "Save"))
        self.helper.add_input(Reset("reset", "Reset"))


CategoryFormSetBase = inlineformset_factory(
    Event,
    Category,
    extra=2,
    can_delete=True,
    fields=["order", "name", "price", "groups1", "groups2"],
)


class CategoryFormSet(CategoryFormSetBase):
    def clean(self):
        super(CategoryFormSet, self).clean()

        if self.total_error_count() > 0:
            # don't bother checking if there are errors in underlying forms
            return

        # Validate that there is no duplicated order
        found_orders = set()
        duplicated_orders = set()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data["DELETE"]:
                # Ignore deleted and empty forms
                continue

            new_order = form.cleaned_data["order"]
            if new_order in found_orders:
                duplicated_orders.add(new_order)
            else:
                found_orders.add(new_order)
        if len(duplicated_orders) > 0:
            text = "Duplicated order(s) found: " + ", ".join(
                map(str, duplicated_orders)
            )
            raise ValidationError(text)


class CategoryFormSetHelper(FormHelper):
    def __init__(self, event, *args, **kwargs):
        super(CategoryFormSetHelper, self).__init__(*args, **kwargs)
        self.form_action = reverse(
            "event_update_categories", kwargs={"event_id": event.id}
        )
        self.template = "bootstrap/table_inline_formset.html"
        self.add_input(Submit("submit", "Save"))
        self.add_input(Reset("reset", "Reset"))


class SessionForm(ModelForm):
    start = MySplitDateTimeField(required=False, help_text="Start date and time")
    end = MySplitDateTimeField(required=False, help_text="End date and time")

    class Meta:
        model = Session
        fields = ["title", "start", "end", "max_participant"]


SessionFormSet = inlineformset_factory(
    Event, Session, extra=2, can_delete=True, form=SessionForm
)


class SessionFormSetHelper(FormHelper):
    def __init__(self, event, *args, **kwargs):
        super(SessionFormSetHelper, self).__init__(*args, **kwargs)
        self.form_action = reverse(
            "event_update_sessions", kwargs={"event_id": event.id}
        )
        self.template = "bootstrap/table_inline_formset.html"
        self.add_input(Submit("submit", "Save"))
        self.add_input(Reset("reset", "Reset"))


class ChoiceForm(ModelForm):
    class Meta:
        model = Choice
        fields = ["title"]

    def __init__(self, *args, **kwargs):
        super(ChoiceForm, self).__init__(*args, **kwargs)

        self.fields["title"].label = "Choice Title"

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("title"),
            FormActions(
                Submit("save", "Save", css_class="btn-success"),
                Reset("reset", "Reset", css_class="btn-warning"),
                HTML(
                    '<a href="{0}" class="btn btn-danger">Cancel</a>'.format(
                        reverse(
                            "event_update", kwargs={"event_id": self.instance.event.id}
                        )
                    )
                ),
                css_class="text-center",
            ),
        )
        self.helper.label_class = "col-xs-3"
        self.helper.field_class = "col-xs-7"


OptionFormSetBase = inlineformset_factory(
    Choice, Option, extra=3, can_delete=True, fields=["title", "default"]
)


class OptionFormSet(OptionFormSetBase):
    def clean(self):
        """
        Validate that the overall set of options is valid
        """
        super(OptionFormSet, self).clean()

        # Check that a single "Default" Option will remain and store it
        self.new_default = None
        for form in self.forms:
            if form.errors and not form.cleaned_data["DELETE"]:
                # If any error in underlying (non deleted) forms, don't bother
                return
            if form.instance.default and not form.cleaned_data["DELETE"]:
                if self.new_default is not None:
                    raise ValidationError(
                        "You can not have more than one Default Option."
                    )
                else:
                    self.new_default = form.instance
        if self.new_default is None:
            raise ValidationError("You must have one Default Option.")

        # Store the deleted Options
        self.deleted_options = [
            form.instance for form in self.deleted_forms if form.instance.pk
        ]


class OptionFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(OptionFormSetHelper, self).__init__(*args, **kwargs)

        self.form_tag = False
        self.layout = Layout(
            Div(
                Div(HTML("Option #{{ forloop.counter }}"), css_class="panel-heading"),
                Div(
                    Div(Field("title"), css_class="row"),
                    Div(
                        Div(css_class="col-xs-2"),
                        Div(Field("default"), css_class="col-xs-2"),
                        Div(Field("DELETE"), css_class="col-xs-2"),
                        css_class="row",
                    ),
                    css_class="panel-body",
                ),
                css_class="panel panel-info",
            )
        )
        self.label_class = "col-xs-2"
        self.field_class = "col-xs-9"


def all_username_choices():
    """Generates all pairs (username, full_name) for users sorted alphabetically"""
    all_users = get_user_model().objects.order_by("last_name", "first_name")
    for u in all_users:
        yield (u.username, u.get_full_name())


class CreateBookingOnBehalfForm(Form):
    username = ChoiceField(label="Create a booking for", choices=all_username_choices)

    def __init__(self, event_id, *args, **kwargs):
        super(CreateBookingOnBehalfForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse(
            "booking_create_on_behalf", kwargs={"event_id": event_id}
        )
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-3"
        self.helper.field_class = "col-lg-6"
        self.helper.add_input(Submit("submit", "Create Booking"))
