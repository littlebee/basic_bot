import datetime


def get_log_time() -> str:
    return f"{datetime.datetime.now():%Y%m%d-%H%M%S}"
