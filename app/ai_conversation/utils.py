from datetime import datetime

import pytz


def date_to_db(date: datetime, timezone: pytz.timezone) -> datetime:
    if date is None:
        return None
    if date.tzinfo is None:
        date = pytz.utc.localize(date)
    date = timezone.normalize(date)
    return date.replace(tzinfo=None)


def date_from_db(date: datetime, timezone: pytz.timezone) -> datetime:
    if date is None:
        return None
    return timezone.localize(date)
