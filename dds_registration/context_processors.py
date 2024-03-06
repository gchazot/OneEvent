# -*- coding:utf-8 -*-
from django.conf import settings
#  from django.contrib.sites.shortcuts import get_current_site

#  # Logging demo
#  import logging
#  LOG = logging.getLogger(__name__)
#  LOG.info('test')

def common_values(request):

    data = {}

    data['settings'] = settings.PASS_VARIABLES

    #  # Fetch predefined attributes for production mode...
    #  fetch_attr = (
    #      'GOOGLE_ANALYTICS_PROPERTY_ID',
    #      'GOOGLE_SITE_VERIFICATION_ID',
    #  )
    #  for id in fetch_attr:
    #      attr = getattr(settings, id, False)
    #      if not settings.LOCAL and not settings.DEBUG and attr:
    #          data[id] = attr

    #  # Pass some site parameters
    #  current_site = get_current_site(request)
    #  data['site'] = 'http://%s' % current_site.domain

    return data
