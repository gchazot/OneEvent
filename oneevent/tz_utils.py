import pytz
from datetime import date
from datetime import datetime
from datetime import timedelta

DSTADJUST = "adjust"
DSTKEEP = "keep"
DSTAUTO = "auto"
MAX32 = int(2 ** 31 - 1)


def add_to_zones_map(tzmap, tzid, dt):
    """
    From
    https://github.com/plone/plone.app.event/blob/2.0/plone/app/event/ical/exporter.py#L91

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

    if tzid.lower() == "utc" or not is_datetime(dt):
        # no need to define UTC nor timezones for date objects.
        return tzmap
    null = datetime(1, 1, 1)
    tz = pytz.timezone(tzid)
    transitions = getattr(tz, "_utc_transition_times", None)
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
    transition = max(transitions, key=lambda item: item <= dtzl and item or null)

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
        "dst": transition.dst() > timedelta(0),
        "name": transition.tzname(),
        "tzoffsetfrom": prev_transition.utcoffset(),
        "tzoffsetto": transition.utcoffset(),
        # TODO: recurrence rule
    }
    return tzmap


# Timezone helpers
def utctz():
    """ Return the UTVC zone as a pytz.UTC instance.

    >>> from plone.event.utils import utctz
    >>> utctz()
    <UTC>

    """
    return pytz.timezone("UTC")


def utc(dt):
    """ Convert Python datetime to UTC.

    >>> from datetime import datetime
    >>> from plone.event.utils import utc
    >>> utc(datetime(2011,11,11,11,11))
    datetime.datetime(2011, 11, 11, 11, 11, tzinfo=<UTC>)

    >>> import pytz
    >>> at = pytz.timezone('Europe/Vienna')
    >>> dta = datetime(2011,11,11,11,11,tzinfo=at)
    >>> utc(dta)
    datetime.datetime(2011, 11, 11, 10, 11, tzinfo=<UTC>)

    utc'ing None returns None
    >>> utc(None)==None
    True

    """
    if dt is None:
        return None
    dt = pydt(dt)
    return dt.astimezone(utctz())


def utcoffset_normalize(date, delta=None, dstmode=DSTAUTO):
    """Fixes invalid UTC offsets from recurrence calculations.

    :param date: datetime instance to normalize.

    :param delta: datetime.timedelta instance.
                  Mode DSTADJUST: When crossing daylight saving time changes,
                  the start time of the date before DST change will be the same
                  in value as afterwards.  It is adjusted relative to UTC. So
                  8:00 GMT+1 before will also result in 8:00 GMT+2 afterwards.
                  This is what humans might expect when recurring rules are
                  defined.
                  Mode DSTKEEP: When crossing daylight saving time changes, the
                  start time of the date before and after DST change will be
                  the same relative to UTC.  So, 8:00 GMT+1 before will result
                  in 7:00 GMT+2 afterwards. This behavior might be what
                  machines expect, when recurrence rules are defined.
                  Mode DSTAUTO: If the relative delta between two occurences of
                  a reucurrence sequence is less than a day, DSTKEEP will be
                  used - otherwise DSTADJUST. This behavior is the default.
    """
    try:
        assert bool(date.tzinfo)
    except AssertionError:
        raise TypeError("Cannot normalize timezone naive dates")
    assert dstmode in [DSTADJUST, DSTKEEP, DSTAUTO]
    if delta:
        assert isinstance(delta, timedelta)  # Easier in Java
        delta = delta.seconds + delta.days * 24 * 3600  # total delta in secs
        if dstmode == DSTAUTO and delta < 24 * 60 * 60:
            dstmode = DSTKEEP
        elif dstmode == DSTAUTO:
            dstmode = DSTADJUST

    try:
        if dstmode == DSTKEEP:
            return date.tzinfo.normalize(date)
        else:  # DSTADJUST
            return date.replace(tzinfo=date.tzinfo.normalize(date).tzinfo)
    except ValueError:
        # TODO: python-datetime converts e.g RDATE:20100119T230000Z to
        # datetime.datetime(2010, 1, 19, 23, 0, tzinfo=tzutc())
        # should that be a real utc zoneinfo?
        # anyways, return UTC date as-is
        return date


def tzdel(dt):
    """ Create timezone naive datetime from a timezone aware one by removing
    the timezone component.

    >>> from plone.event.utils import tzdel, utctz
    >>> from datetime import datetime
    >>> dt = utctz().localize(datetime(2011, 05, 21, 12, 25))

    Remove the timezone:
    >>> tzdel(dt)
    datetime.datetime(2011, 5, 21, 12, 25)

    Using tzdel on a dt instance doesn't alter it:
    >>> dt
    datetime.datetime(2011, 5, 21, 12, 25, tzinfo=<UTC>)

    """
    if dt:
        return dt.replace(tzinfo=None)
    else:
        return None


def is_datetime(value):
    """Checks, if given value is a datetime.

    :param value: The value to check.
    :type value: object
    :returns: True, if value is a datetime (and not a date), false otherwise.
    :rtype: Boolean

    >>> from plone.event.utils import is_datetime
    >>> from datetime import datetime, date
    >>> is_datetime(date.today())
    False
    >>> is_datetime(datetime.now())
    True
    >>> is_datetime(42)
    False
    """
    return type(value) is datetime


def pydt(dt, missing_zone=None, exact=False):
    """Converts a Zope's Products.DateTime in a Python datetime.

    :param dt: date, datetime or DateTime object
    :type dt: Python date, datetime or Zope DateTime
    :param missing_zone: A pytz zone to be used, if no timezone is present.
    :type missing_zone: String
    :param exact: If True, the resolution goes down to microseconds. If False,
                  the resolution are seconds. Default is False.
    :type exact: Boolean
    :returns: Python datetime with timezone information.
    :rtype: Python datetime

    >>> from plone.event.utils import pydt
    >>> from datetime import date, datetime
    >>> import pytz

    >>> at = pytz.timezone('Europe/Vienna')
    >>> pydt(at.localize(datetime(2010,10,30)))
    datetime.datetime(2010, 10, 30, 0, 0, tzinfo=<DstTzInfo \
    'Europe/Vienna' CEST+2:00:00 DST>)

    >>> pydt(date(2010,10,30))
    datetime.datetime(2010, 10, 30, 0, 0, tzinfo=<UTC>)

    pytz cannot handle GMT offsets.
    >>> from DateTime import DateTime
    >>> pydt(DateTime('2011/11/11 11:11:11 GMT+1'))
    datetime.datetime(2011, 11, 11, 10, 11, 11, tzinfo=<UTC>)

    >>> pydt(DateTime('2011/11/11 11:11:11 Europe/Vienna'))
    datetime.datetime(2011, 11, 11, 11, 11, 11, tzinfo=<DstTzInfo \
    'Europe/Vienna' CET+1:00:00 STD>)

    >>> pydt(DateTime('2005/11/07 18:00:00 Brazil/East'))
    datetime.datetime(2005, 11, 7, 18, 0, tzinfo=<DstTzInfo \
    'Brazil/East' BRST-1 day, 22:00:00 DST>)

    Test with exact set to True
    >>> pydt(DateTime('2012/10/10 10:10:10.123456 Europe/Vienna'), exact=True)
    datetime.datetime(2012, 10, 10, 10, 10, 10, 123456, tzinfo=<DstTzInfo \
    'Europe/Vienna' CEST+2:00:00 DST>)

    Test with exact set to False
    >>> pydt(DateTime('2012/10/10 10:10:10.123456 Europe/Vienna'), exact=False)
    datetime.datetime(2012, 10, 10, 10, 10, 10, tzinfo=<DstTzInfo 'Europe/Vienna' \
    CEST+2:00:00 DST>)

    >>> pydt(datetime(2012, 10, 10, 20, 20, 20, 123456, tzinfo=at), exact=False)
    datetime.datetime(2012, 10, 10, 20, 20, 20, tzinfo=<DstTzInfo 'Europe/Vienna' \
    CEST+2:00:00 DST>)

    """
    if dt is None:
        return None

    ret = None

    if missing_zone is None:
        missing_zone = utctz()

    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime(dt.year, dt.month, dt.day)

    if isinstance(dt, datetime):
        tznaive = not bool(getattr(dt, "tzinfo", False))
        if tznaive:
            ret = missing_zone.localize(dt)
        else:
            ret = utcoffset_normalize(dt, dstmode=DSTADJUST)

    if "DateTime" in str(dt.__class__):
        # Zope DateTime
        # TODO: do we need to support subclasses of DateTime too? the check
        #       above would fail.
        tz = guesstz(dt)
        if tz is None:
            dt = dt.toZone(missing_zone.zone)
            tz = missing_zone

        year, month, day, hour, mins, sec = dt.parts()[:6]

        # seconds (parts[6]) is a float, so we do modulo for microseconds and
        # map then to int
        #
        # there are precision problems when doing the modulo math
        # (Python 2.7.3 on Ubuntu 12.04):
        # >>> 10.123456%1*1000000
        # 123455.99999999913
        # >>> round(10.123456%1*1000000,0)
        # 123456.0
        micro = int(round(sec % 1 * 1000000))
        sec = int(sec)

        # There is a problem with timezone Europe/Paris
        # tz is equal to <DstTzInfo 'Europe/Paris' PMT+0:09:00 STD>
        dt = datetime(year, month, day, hour, mins, sec, micro, tzinfo=tz)
        # before:
        # datetime.datetime(2011, 3, 14, 14, 19, \
        # tzinfo=<DstTzInfo 'Europe/Paris' PMT+0:09:00 STD>)
        # dt = dt.tzinfo.normalize(dt)
        # after: datetime.datetime(2011, 3, 14, 15, 10, \
        # tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>
        dt = utcoffset_normalize(dt, dstmode=DSTADJUST)
        # after: datetime.datetime(2011, 3, 14, 19, \
        # tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>
        ret = dt

    if ret and not exact:
        ret = ret.replace(microsecond=0)

    return ret


def guesstz(DT):
    """'Guess' pytz from a zope DateTime.

    !!! theres no real good method to guess the timezone.
    DateTime was build somewhere in 1998 long before python had a working
    datetime implementation available and still stucks with this incomplete
    implementation.

    >>> from DateTime import DateTime
    >>> from plone.event.utils import guesstz

    Timezones with the same name as in the Olson DB can easily be guessed.
    >>> guesstz(DateTime('2010-01-01 Europe/Vienna'))
    <DstTzInfo 'Europe/Vienna' CET+1:00:00 STD>

    GMT timezones which are popular with DateTime cannot be guessed,
    unfortunatly
    >>> guesstz(DateTime('2010-01-01 GMT+1'))
    """
    tzname = DT.timezone()

    # Please note, the GMT offset based timezone informations in DateTime are
    # not compatible with Etc/GMT based from pytz. They have different offsets.
    try:
        tz = pytz.timezone(tzname)
        return tz
    except KeyError:
        pass
    return None
