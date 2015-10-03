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
