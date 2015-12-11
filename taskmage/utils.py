import datetime

def rounded_now():
    # TODO Allow rounding to configured mark
    # Return current UTC time rounded to 5 minute mark
    now = datetime.datetime.utcnow()
    discard = datetime.timedelta(
        minutes=now.minute % 5,
        seconds=now.second,
        microseconds=now.microsecond
    )
    now -= discard
    if discard >= datetime.timedelta(minutes=2.5):
        now += datetime.timedelta(minutes=5)
    return now


def current_sheet():
    '''
    Current timesheet is the current month by default
    '''
    return datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m")


def time_from_seconds(seconds, show_seconds=False):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if show_seconds:
        return "%d:%02d:%02d" % (h, m, s)
    return "%d:%02d" % (h, m)




