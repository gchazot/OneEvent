from django.contrib import admin
from .models import (
    Event,
    Session,
    Choice,
    Option,
    Booking,
    BookingOption,
    Category,
)
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib.admin.utils import unquote


class EditLinkToInlineObjectMixin(object):
    """
    Mixin to allow having a link to the admin page of another Model
    From http://stackoverflow.com/a/22113967
    """

    def edit_link(self, instance):
        url = reverse(
            "admin:%s_%s_change"
            % (instance._meta.app_label, instance._meta.module_name),
            args=[instance.pk],
        )
        if instance.pk:
            return mark_safe('<a href="{u}">edit</a>'.format(u=url))
        else:
            return ""


class LimitedAdminInlineMixin(object):
    """
    InlineAdmin mixin limiting the selection of related items according to
    criteria which can depend on the current parent object being edited.

    A typical use case would be selecting a subset of related items from
    other inlines, ie. images, to have some relation to other inlines.

    Use as follows::

        class MyInline(LimitedAdminInlineMixin, admin.TabularInline):
            def get_filters(self, obj):
                return (('<field_name>', dict(<filters>)),)

    From https://gist.github.com/dokterbob/828117
    """

    @staticmethod
    def limit_inline_choices(formset, field, empty=False, **filters):
        """
        This function fetches the queryset with available choices for a given
        `field` and filters it based on the criteria specified in filters,
        unless `empty=True`. In this case, no choices will be made available.
        """
        assert field in formset.form.base_fields

        qs = formset.form.base_fields[field].queryset
        if empty:
            formset.form.base_fields[field].queryset = qs.none()
        else:
            qs = qs.filter(**filters)

            formset.form.base_fields[field].queryset = qs

    def get_formset(self, request, obj=None, **kwargs):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        formset = super(LimitedAdminInlineMixin, self).get_formset(
            request, obj, **kwargs
        )

        for (field, filters) in self.get_filters(obj):
            if obj:
                self.limit_inline_choices(formset, field, **filters)
            else:
                self.limit_inline_choices(formset, field, empty=True)

        return formset

    def get_filters(self, _):
        """
        Return filters for the specified fields. Filters should be in the
        following format::

            (('field_name', {'categories': obj}), ...)

        For this to work, we should either override `get_filters` in a
        subclass or define a `filters` property with the same syntax as this
        one.
        """
        return getattr(self, "filters", ())


class OptionInline(admin.TabularInline):
    model = Option
    fields = (
        "title",
        "default",
    )


class ChoiceAdmin(admin.ModelAdmin):
    fields = (
        "event",
        "title",
    )
    readonly_fields = ("event",)
    inlines = [OptionInline]
    list_display = ("event", "title")


class ChoiceInline(admin.TabularInline, EditLinkToInlineObjectMixin):
    model = Choice
    fields = (
        "title",
        "edit_link",
    )
    readonly_fields = ("edit_link",)


class SessionInline(admin.TabularInline):
    model = Session
    fields = ("title", "start", "end", "max_participant")
    extra = 1


class CategoryInline(admin.TabularInline):
    model = Category
    fields = ("order", "name", "price", "groups1", "groups2")
    extra = 1


class EventAdmin(admin.ModelAdmin):
    fields = (
        ("title", "pub_status"),
        ("start", "end"),
        "timezone",
        ("location_name", "location_address"),
        ("owner", "organisers"),
        ("booking_close", "choices_close"),
        "max_participant",
        "price_currency",
    )
    inlines = (
        SessionInline,
        CategoryInline,
        ChoiceInline,
    )
    list_display = ("title", "timezone", "start_local", "end_local")

    dt_format = "%a, %d %b %Y %H:%M:%S %Z"

    def start_local(self, event):
        """ Display the start datetime in its local timezone """
        tz = event.timezone
        dt = event.start.astimezone(tz)
        return dt.strftime(self.dt_format)

    def end_local(self, event):
        """ Display the end datetime in its local timezone """
        if event.end is None:
            return None
        tz = event.timezone
        dt = event.end.astimezone(tz)
        return dt.strftime(self.dt_format)

    def add_view(self, request, form_url="", extra_context=None):
        """
        Override add view so we can peek at the timezone they've entered and
        set the current timezone accordingly before the form is processed
        """
        if request.method == "POST":
            tz_form = self.get_form(request)(request.POST)
            if tz_form.is_valid():
                tz = tz_form.cleaned_data["timezone"]
                timezone.activate(tz)

        return super(EventAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """
        Override change view so we can peek at the timezone they've entered and
        set the current timezone accordingly before the form is processed
        """
        event = self.get_object(request, unquote(object_id))

        if request.method == "POST":
            tz_form = self.get_form(request, event)(request.POST, instance=event)
            if tz_form.is_valid():
                tz = tz_form.cleaned_data["timezone"]
                timezone.activate(tz)
        else:
            timezone.activate(event.timezone)

        return super(EventAdmin, self).change_view(
            request, object_id, form_url, extra_context
        )


class BookingOptionInline(LimitedAdminInlineMixin, admin.TabularInline):
    model = BookingOption

    def get_filters(self, obj):
        if obj:
            return (("option", {"choice__event": obj.event}),)
        return []


class BookingAdmin(admin.ModelAdmin):
    inlines = (BookingOptionInline,)
    list_display = ("event", "person", "cancelledBy", "cancelledOn", "confirmedOn")


admin.site.register(Event, EventAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Booking, BookingAdmin)
