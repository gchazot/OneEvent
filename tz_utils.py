import logging
import os
import pytz
import time
from datetime import date
from datetime import datetime
from datetime import timedelta

DSTADJUST = 'adjust'
DSTKEEP = 'keep'
DSTAUTO = 'auto'
MAX32 = int(2 ** 31 - 1)

logger = logging.getLogger('plone.event')


def validated_timezone(timezone, fallback=None):
    """ Validate a given timezone identifier. If a fallback is given, return it
        when the given timezone is not a valid pytz zone. Else raise an
        ValueError exception.

    :param timezone: Timezone identifier to be validated against pytz.
    :type timezone: string

    :param fallback: A fallback timezone identifier.
    :type fallback: string

    :returns: A valid pytz timezone identifier.
    :rtype: string
    :raises: ValueError

    >>> from plone.event.utils import validated_timezone

    Validate a valid timezone:
    >>> validated_timezone('Europe/Vienna')
    'Europe/Vienna'

    Validate an invalid timezone with fallback:
    >>> validated_timezone('NOTVALID', 'UTC')
    'UTC'

    Validate an invalid timezone without fallback:
    >>> validated_timezone('NOTVALID')
    Traceback (most recent call last):
    ...
    ValueError: The timezone NOTVALID ...

    The fallback itself isn't validated:
    >>> validated_timezone('NOTVALID', 'NOTVALID')
    'NOTVALID'

    """
    try:
        # following statement ensures, that timezone is a valid pytz/Olson zone
        return pytz.timezone(timezone).zone
    except:
        if fallback:
            logger.warn('The timezone %s is not a valid timezone from the '
                        'Olson database or pytz. Falling back to %s.'
                        % (timezone, fallback))
            return fallback
        else:
            raise ValueError('The timezone %s is not a valid timezone from '
                             'the Olson database or pytz.' % timezone)


def default_timezone(fallback='UTC'):
    """ Retrieve the timezone from the server.
        Default Fallback: UTC

        :param fallback: A fallback timezone identifier.
        :type fallback: string

        :returns: A timezone identifier.
        :rtype: string

        >>> from plone.event.utils import default_timezone
        >>> import os
        >>> import time
        >>> timetz = time.tzname
        >>> ostz = 'TZ' in os.environ.keys() and os.environ['TZ'] or None

        >>> os.environ['TZ'] = "Europe/Vienna"
        >>> default_timezone()
        'Europe/Vienna'

        Timezone from time module
        >>> os.environ['TZ'] = ""
        >>> time.tzname = ('CET', 'CEST')
        >>> default_timezone()
        'CET'

        Invalid timezone
        >>> os.environ['TZ'] = "PST"
        >>> default_timezone()
        'UTC'

        Invalid timezone with defined fallback
        >>> os.environ['TZ'] = ""
        >>> time.tzname = None
        >>> default_timezone(fallback='CET')
        'CET'

        Restore the system timezone
        >>> time.tzname = timetz
        >>> if ostz:
        ...     os.environ['TZ'] = ostz
        ... else:
        ...     del os.environ['TZ']

    """

    timezone = None
    if 'TZ' in os.environ.keys():
        # Timezone from OS env var
        timezone = os.environ['TZ']
    if not timezone:
        # Timezone from python time
        zones = time.tzname
        if zones and len(zones) > 0:
            timezone = zones[0]
        else:
            # Default fallback = UTC
            logger.warn("Operating system's timezone cannot be found. "
                        "Falling back to UTC.")
    return validated_timezone(timezone, fallback)


# Display helpers
def is_same_time(start, end, exact=False):
    """ Test if event starts and ends at same time.

    :param start: The start datetime.
    :type start: Python datetime or Zope DateTime
    :param end: The end datetime.
    :type end: Python datetime or Zope DateTime
    :param exact: If True, the resolution goes down to microseconds. If False,
                  the resolution are seconds. Default is False.
    :type exact: Boolean
    :returns: True, if start and end have the same time, otherwise False.
    :rtype: Boolean.

    >>> from plone.event.utils import is_same_time, pydt
    >>> from datetime import datetime, timedelta

    >>> is_same_time(datetime.now(), datetime.now()+timedelta(hours=1))
    False

    >>> is_same_time(datetime.now(), datetime.now()+timedelta(days=1))
    True

    Resolution is one second
    >>> is_same_time(datetime(2013, 5, 21, 10, 59, 58),
    ...              datetime(2013, 5, 21, 10, 59, 59),
    ...              exact=False)
    False

    Exact:
    >>> now = datetime.now()
    >>> is_same_time(now, now, exact=True)
    True

    """
    start = pydt(start, exact=exact).time()
    end = pydt(end, exact=exact).time()
    if exact:
        return start == end
    else:
        return start.hour == end.hour and\
            start.minute == end.minute and\
            start.second == end.second


def is_same_day(start, end):
    """ Test if event starts and ends at same day.

    >>> from plone.event.utils import is_same_day, utc
    >>> from datetime import datetime, timedelta

    >>> is_same_day(
    ...     datetime(2013, 11, 6, 10, 0, 0),
    ...     datetime(2013, 11, 6, 10, 0, 0) + timedelta(hours=1)
    ... )
    True

    >>> is_same_day(
    ...     datetime(2013, 11, 6, 10, 0, 0),
    ...     datetime(2013, 11, 6, 10, 0, 0) + timedelta(days=1)
    ... )
    False

    >>> is_same_day(datetime(2011, 11, 11, 0, 0, 0,),
    ...             datetime(2011, 11, 11, 23, 59, 59))
    True

    Now with one localized (UTC) datetime:
    >>> is_same_day(
    ...     utc(datetime(2013, 11, 6, 10, 0, 0)),
    ...     datetime(2013, 11, 6, 10, 0, 0)
    ... )
    True
    """
    start = pydt(start)
    end = pydt(end)
    return start.date() == end.date()


# Timezone helpers
def utctz():
    """ Return the UTVC zone as a pytz.UTC instance.

    >>> from plone.event.utils import utctz
    >>> utctz()
    <UTC>

    """
    return pytz.timezone('UTC')


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
        assert(bool(date.tzinfo))
    except:
        raise TypeError('Cannot normalize timezone naive dates')
    assert(dstmode in [DSTADJUST, DSTKEEP, DSTAUTO])
    if delta:
        assert(isinstance(delta, timedelta))  # Easier in Java
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
    except:
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


def is_date(value):
    """Checks, if given value is a date.

    :param value: The value to check.
    :type value: object
    :returns: True, if value is a date (and not a datetime), false otherwise.
    :rtype: Boolean

    >>> from plone.event.utils import is_date
    >>> from datetime import datetime, date
    >>> is_date(date.today())
    True
    >>> is_date(datetime.now())
    False
    >>> is_date(42)
    False
    """
    return type(value) is date


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


def date_to_datetime(value):
    """Converts date objects to datetime objects.

    :param value: Date to convert to datetime.
    :type value: date
    :returns: datetime.
    :rtype: datetime

    >>> from plone.event.utils import date_to_datetime
    >>> from datetime import datetime, date
    >>> date_to_datetime(date(2013,3,25))
    datetime.datetime(2013, 3, 25, 0, 0)

    >>> date_to_datetime(datetime(2013,3,25,10,10,10))
    datetime.datetime(2013, 3, 25, 10, 10, 10)

    >>> date_to_datetime(42)
    Traceback (most recent call last):
    ...
    ValueError: Value must be a date or datetime object.


    """

    if is_date(value):
        return datetime(value.year, value.month, value.day)
    elif is_datetime(value):
        return value
    else:
        raise ValueError("Value must be a date or datetime object.")


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
    datetime.datetime(2010, 10, 30, 0, 0, tzinfo=<DstTzInfo 'Europe/Vienna' CEST+2:00:00 DST>)

    >>> pydt(date(2010,10,30))
    datetime.datetime(2010, 10, 30, 0, 0, tzinfo=<UTC>)

    pytz cannot handle GMT offsets.
    >>> from DateTime import DateTime
    >>> pydt(DateTime('2011/11/11 11:11:11 GMT+1'))
    datetime.datetime(2011, 11, 11, 10, 11, 11, tzinfo=<UTC>)

    >>> pydt(DateTime('2011/11/11 11:11:11 Europe/Vienna'))
    datetime.datetime(2011, 11, 11, 11, 11, 11, tzinfo=<DstTzInfo 'Europe/Vienna' CET+1:00:00 STD>)

    >>> pydt(DateTime('2005/11/07 18:00:00 Brazil/East'))
    datetime.datetime(2005, 11, 7, 18, 0, tzinfo=<DstTzInfo 'Brazil/East' BRST-1 day, 22:00:00 DST>)

    Test with exact set to True
    >>> pydt(DateTime('2012/10/10 10:10:10.123456 Europe/Vienna'), exact=True)
    datetime.datetime(2012, 10, 10, 10, 10, 10, 123456, tzinfo=<DstTzInfo 'Europe/Vienna' CEST+2:00:00 DST>)

    Test with exact set to False
    >>> pydt(DateTime('2012/10/10 10:10:10.123456 Europe/Vienna'), exact=False)
    datetime.datetime(2012, 10, 10, 10, 10, 10, tzinfo=<DstTzInfo 'Europe/Vienna' CEST+2:00:00 DST>)

    >>> pydt(datetime(2012, 10, 10, 20, 20, 20, 123456, tzinfo=at), exact=False)
    datetime.datetime(2012, 10, 10, 20, 20, 20, tzinfo=<DstTzInfo 'Europe/Vienna' CEST+2:00:00 DST>)

    """
    if dt is None:
        return None

    ret = None

    if missing_zone is None:
        missing_zone = utctz()

    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime(dt.year, dt.month, dt.day)

    if isinstance(dt, datetime):
        tznaive = not bool(getattr(dt, 'tzinfo', False))
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
        # datetime.datetime(2011, 3, 14, 14, 19, tzinfo=<DstTzInfo 'Europe/Paris' PMT+0:09:00 STD>)
        # dt = dt.tzinfo.normalize(dt)
        # after: datetime.datetime(2011, 3, 14, 15, 10, tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>
        dt = utcoffset_normalize(dt, dstmode=DSTADJUST)
        # after: datetime.datetime(2011, 3, 14, 19, tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>
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


# Date as integer representation helpers
def dt2int(dt):
    """ Calculates an integer from a datetime, resolution is one minute.
    The datetime is always converted to the UTC zone.

    >>> from plone.event import utils
    >>> from datetime import datetime
    >>> utils.dt2int(datetime(2011,11,11,11,11,tzinfo=utils.utctz()))
    1077760031

    """
    if dt is None:
        return 0
    # TODO: if dt has not timezone information, guess and set it
    dt = utc(dt)
    value = (((dt.year * 12 + dt.month) * 31 + dt.day) * 24 + dt.hour) * 60 + dt.minute

    # TODO: unit test me
    if value > MAX32:
        # value must be integer fitting in the 32bit range
        raise OverflowError(
            """%s is not within the range of indexable dates,<<
            exceeding 32bit range.""" % dt
        )
    return value


def int2dt(dtint):
    """ Returns a datetime object from an integer representation with
    resolution of one minute. The datetime returned is in the UTC zone.

    >>> from plone.event.utils import int2dt
    >>> int2dt(1077760031)
    datetime.datetime(2011, 11, 11, 11, 11, tzinfo=<UTC>)

    Dateconversion with int2dt from anything else than integers does not work
    >>> int2dt(.0)
    Traceback (most recent call last):
    ...
    ValueError: int2dt expects integer values as arguments.

    """
    if not isinstance(dtint, int):
        raise ValueError('int2dt expects integer values as arguments.')
    minutes = dtint % 60
    hours = dtint / 60 % 24
    days = dtint / 60 / 24 % 31
    months = dtint / 60 / 24 / 31 % 12
    years = dtint / 60 / 24 / 31 / 12
    return datetime(years, months, days, hours, minutes, tzinfo=utctz())


def dt_to_zone(dt, tzstring):
    """ Return a datetime instance converted to the timezone given by the
    string.

    """
    return dt.astimezone(pytz.timezone(tzstring))


# RFC2445 export helpers
def rfc2445dt(dt, mode='utc', date=True, time=True):
    """ Convert a datetime or DateTime object into an RFC2445 compatible
    datetime string.

    @param dt: datetime or DateTime object to convert.

    @param mode: Conversion mode ('utc'|'local'|'float')
        Mode 'utc':   Return datetime string in UTC
        Mode 'local': Return datetime string as local
                      including a TZID component
        Mode 'float': Return datetime string as floating (local without TZID
                      component)

    @param date: Return date.

    @param time: Return time.

    Usage
    =====

    >>> from datetime import datetime
    >>> import pytz # this import actually takes quite a long time!
    >>> from plone.event.utils import rfc2445dt

    >>> at = pytz.timezone('Europe/Vienna')
    >>> dt = at.localize(datetime(2010,10,10,10,10))
    >>> dt
    datetime.datetime(2010, 10, 10, 10, 10, tzinfo=<DstTzInfo 'Europe/Vienna' CEST+2:00:00 DST>)

    >>> assert(rfc2445dt(dt) == rfc2445dt(dt, mode='utc'))
    >>> rfc2445dt(dt)
    '20101010T081000Z'

    >>> rfc2445dt(dt, mode='local')
    ('20101010T101000', 'Europe/Vienna')

    >>> rfc2445dt(dt, mode='float')
    '20101010T101000'

    >>> assert(rfc2445dt(dt, date=True, time=True) == rfc2445dt(dt))
    >>> rfc2445dt(dt, time=False)
    '20101010Z'
    >>> rfc2445dt(dt, date=False)
    '081000Z'

    RFC2445 dates from DateTime objects
    -----------------------------------
    >>> from DateTime import DateTime

    It's summer time! So TZ in Belgrade is GMT+2.
    >>> rfc2445dt(DateTime('2010/08/31 18:00:00 Europe/Belgrade'))
    '20100831T160000Z'

    GMT offsets are converted to UTC without any DST adjustments.
    >>> rfc2445dt(DateTime('2010/08/31 20:15:00 GMT+1'))
    '20100831T191500Z'

    """
    # TODO: rfc2445dt might not be necessary. drop me then.

    dt = pydt(dt)
    if mode == 'utc':
        dt = utc(dt)
    date = "%s%s%s%s" % (date and dt.strftime("%Y%m%d") or '',
                         date and time and 'T' or '',
                         time and dt.strftime("%H%M%S") or '',
                         mode == 'utc' and 'Z' or '')
    if mode == 'local':
        return date, dt.tzinfo.zone
    return date
