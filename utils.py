from datetime import timedelta

def seconds_to_hms(x, pos):
    hours, remainder = divmod(int(x), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02}'


def format_timedelta_hms(delta):
    """Formats a timedelta object into HH:MM:SS."""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"