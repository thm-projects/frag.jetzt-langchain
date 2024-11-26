import pytz
from datetime import datetime

from app.ai_conversation.utils import date_from_db


def entity(clazz):
    code = clazz.__init__.__code__

    @staticmethod
    def load_from_db(row):
        dictionary = {}
        timezone = None
        if "timezone" in row:
            timezone = pytz.timezone(row["timezone"])
        for i in range(1, code.co_argcount):
            key = code.co_varnames[i]
            value = row[key]
            if (
                isinstance(value, datetime)
                and timezone
                and key not in ["created_at", "updated_at"]
            ):
                value = date_from_db(value, timezone)
            dictionary[key] = value
        return clazz(**dictionary)

    clazz.load_from_db = load_from_db
    return clazz
