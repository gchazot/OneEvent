from django.apps import AppConfig
from django.conf import settings
from django.contrib import messages


class OneEventConfig(AppConfig):
    name = 'oneevent'
    verbose_name = 'OneEvent'

    def ready(self):
        # Override the "error" message level to match the bootstrap "danger" class
        message_tags = getattr(settings, 'MESSAGE_TAGS', {})
        message_tags.setdefault(messages.ERROR, 'danger')
        setattr(settings, 'MESSAGE_TAGS', message_tags)

        # Define template pack for django-crispy-forms
        crispy_template_pack = getattr(settings, 'CRISPY_TEMPLATE_PACK', 'bootstrap3')
        setattr(settings, 'CRISPY_TEMPLATE_PACK', crispy_template_pack)


default_app_config = 'oneevent.OneEventConfig'
