import celery

from wxwarn.utils import get_users_location
from wxwarn.utils import get_weather_alerts as _get_weather_alerts

@celery.task(name='tasks.update_locations')
def update_locations(premium=False):
    get_users_location(premium=premium)


@celery.task(name='tasks.get_weather_alerts')
def get_weather_alerts():
    _get_weather_alerts()
