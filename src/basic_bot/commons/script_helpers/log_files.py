import datetime


def get_log_time():
    return f"{datetime.datetime.now():%Y%m%d-%H%M%S}"
