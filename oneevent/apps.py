from django.apps import AppConfig
from django.conf import settings
from django.contrib import messages


class OneEventConfig(AppConfig):
    name = "oneevent"
    verbose_name = "OneEvent"

    def ready(self):
        # Default customisable settings
        site_brand = getattr(settings, "ONEEVENT_SITE_BRAND", self.verbose_name)
        setattr(settings, "ONEEVENT_SITE_BRAND", site_brand)

        navbar_color = getattr(settings, "ONEEVENT_NAVBAR_COLOR", None)
        setattr(settings, "ONEEVENT_NAVBAR_COLOR", navbar_color)

        calendar_invite_from = getattr(settings, "ONEEVENT_CALENDAR_INVITE_FROM", None)
        setattr(settings, "ONEEVENT_CALENDAR_INVITE_FROM", calendar_invite_from)

        # add context processors
        template_engines = getattr(settings, "TEMPLATES", [])
        for template_engine in template_engines:
            if (
                template_engine["BACKEND"]
                == "django.template.backends.django.DjangoTemplates"
            ):
                template_engine["OPTIONS"]["context_processors"].append(
                    "oneevent.context_processors.customise_navbar"
                )
        setattr(settings, "TEMPLATES", template_engines)

        # Override the "error" message level to match the bootstrap "danger" class
        message_tags = getattr(settings, "MESSAGE_TAGS", {})
        message_tags.setdefault(messages.ERROR, "danger")
        setattr(settings, "MESSAGE_TAGS", message_tags)

        # Define template pack for django-crispy-forms
        crispy_template_pack = getattr(settings, "CRISPY_TEMPLATE_PACK", "bootstrap3")
        setattr(settings, "CRISPY_TEMPLATE_PACK", crispy_template_pack)
