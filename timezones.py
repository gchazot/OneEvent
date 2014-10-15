'''
Created on 13 Oct 2014

@author: gchazot
'''
from pytz import timezone

# A map of available cities to the corresponding timezone code
TIMEZONE_CODES = {
    'Boston': 'US/Eastern',
    'Erding': 'Europe/Berlin',
    'London': 'Europe/London',
    'Miami': 'US/Eastern',
    'Munich': 'Europe/Berlin',
    'Nice': 'Europe/Paris',
    'Sydney': 'Australia/Sydney',
    'Toronto': 'America/Toronto',
    'UTC': 'UTC'
}

# A map of available cities to the corresponding tzinfo object
TIMEZONES = {city: timezone(code) for city, code in TIMEZONE_CODES.items()}

# Choices for the available cities
CITY_CHOICES = [(city, city) for city in sorted(TIMEZONE_CODES.keys())]


def get_tzinfo(city):
    '''
    Returns a tzinfo object for the given city
    '''
    return timezone(TIMEZONE_CODES[city])
#     return TIMEZONES[city]
