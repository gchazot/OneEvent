from django.conf import settings


def customise_navbar(_request):
    """
    Defines some site-wide variables for use in oneevent templates
    """
    return {
        "site_brand": settings.ONEEVENT_SITE_BRAND,
        "navbar_color": settings.ONEEVENT_NAVBAR_COLOR,
    }
