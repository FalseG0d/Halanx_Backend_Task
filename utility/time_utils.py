from datetime import datetime, timedelta

import humanize
from django.utils import timezone


def get_datetime(raw_date):
    if raw_date in [None, '']:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return timezone.make_aware(datetime.strptime(raw_date, fmt), timezone.get_default_timezone())
        except ValueError:
            pass
    raise ValueError('no valid date format found')


def get_natural_datetime(datetime_obj):
    if timezone.now() - datetime_obj < timedelta(hours=24):
        return humanize.naturaltime(timezone.localtime(timezone.now()) - datetime_obj)
    elif timezone.localtime(timezone.now()).year == timezone.localtime(datetime_obj).year:
        return timezone.localtime(datetime_obj).strftime("%d %b at %I:%M %p")
    else:
        return timezone.localtime(datetime_obj).strftime("%d %b, %Y at %I:%M %p")


def is_valid_datetime(datetime_str, fmt):
    try:
        datetime.strptime(datetime_str, fmt)
        return True
    except ValueError:
        return False


def get_date_str(datetime_obj):
    return datetime_obj.strftime('%d %b, %Y')
