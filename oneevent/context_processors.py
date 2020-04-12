from django.conf import settings


def customise_navbar(_request):
    '''
    Defines some site-wide variables for use in oneevent templates
    '''
    result = {}

    try:
        result['site_brand'] = settings.ONEEVENT_SITE_BRAND
    except AttributeError:
        pass

    try:
        result['navbar_color'] = settings.ONEEVENT_NAVBAR_COLOR
    except AttributeError:
        pass

    return result
