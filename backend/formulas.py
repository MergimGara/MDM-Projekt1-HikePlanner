import datetime

def din33466(uphill, downhill, distance):
    """
    Calculate hiking time based on DIN 33466 standard.
    """
    km = distance / 1000.0
    vertical = downhill / 500.0 + uphill / 300.0
    horizontal = km / 4.0
    return 3600.0 * (min(vertical, horizontal) / 2 + max(vertical, horizontal))

def sac(uphill, downhill, distance):
    """
    Calculate hiking time based on the Swiss Alpine Club (SAC) formula.
    """
    km = distance / 1000.0
    return 3600.0 * (uphill / 400.0 + km / 4.0)

def timedelta_minutes(seconds):
    """
    Convert seconds into a HH:MM:SS string rounded to minutes.
    """
    rounded_minutes = int(round(seconds / 60.0))
    return str(datetime.timedelta(minutes=rounded_minutes))
