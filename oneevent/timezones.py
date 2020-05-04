import pytz
import datetime
from .tz_utils import is_datetime, tzdel, utc

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
TIMEZONES = {city: pytz.timezone(code) for city, code in TIMEZONE_CODES.items()}

# Choices for the available cities
CITY_CHOICES = [(city, city) for city in sorted(TIMEZONE_CODES.keys())]


def get_tzinfo(city):
    '''
    Returns a tzinfo object for the given city
    '''
    return pytz.timezone(TIMEZONE_CODES[city])


def add_to_zones_map(tzmap, tzid, dt):
    """
    From https://github.com/plone/plone.app.event/blob/02233f03a6bdf1746760b67a8a78ee9afe9fb0ee/plone/app/event/ical/exporter.py#L92

    Build a dictionary of timezone information from a timezone identifier
    and a date/time object for which the timezone information should be
    calculated.
    :param tzmap: An existing dictionary of timezone information to be extended
                  or an empty dictionary.
    :type tzmap: dictionary
    :param tzid: A timezone identifier.
    :type tzid: string
    :param dt: A datetime object.
    :type dt: datetime
    :returns: A dictionary with timezone information needed to build VTIMEZONE
              entries.
    :rtype: dictionary
    """

    if tzid.lower() == 'utc' or not is_datetime(dt):
        # no need to define UTC nor timezones for date objects.
        return tzmap
    null = datetime.datetime(1, 1, 1)
    tz = pytz.timezone(tzid)
    transitions = getattr(tz, '_utc_transition_times', None)
    if not transitions:
        return tzmap  # we need transition definitions
    dtzl = tzdel(utc(dt))

    # get transition time, which is the dtstart of timezone.
    #     the key function returns the value to compare with. as long as item
    #     is smaller or equal like the dt value in UTC, return the item. as
    #     soon as it becomes greater, compare with the smallest possible
    #     datetime, which wouldn't create a match within the max-function. this
    #     way we get the maximum transition time which is smaller than the
    #     given datetime.
    transition = max(transitions,
                     key=lambda item: item <= dtzl and item or null)

    # get previous transition to calculate tzoffsetfrom
    idx = transitions.index(transition)
    prev_idx = idx > 0 and idx - 1 or idx
    prev_transition = transitions[prev_idx]

    def localize(tz, dt):
        if dt is null:
            # dummy time, edge case
            # (dt at beginning of all transitions, see above.)
            return null
        return pytz.utc.localize(dt).astimezone(tz)  # naive to utc + localize
    transition = localize(tz, transition)
    dtstart = tzdel(transition)  # timezone dtstart must be in local time
    prev_transition = localize(tz, prev_transition)

    if tzid not in tzmap:
        tzmap[tzid] = {}  # initial
    if dtstart in tzmap[tzid]:
        return tzmap  # already there
    tzmap[tzid][dtstart] = {
        'dst': transition.dst() > datetime.timedelta(0),
        'name': transition.tzname(),
        'tzoffsetfrom': prev_transition.utcoffset(),
        'tzoffsetto': transition.utcoffset(),
        # TODO: recurrence rule
    }
    return tzmap
