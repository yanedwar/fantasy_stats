from api.client import get

def get_week_schedule(date):
    return get(f"schedule/{date}")