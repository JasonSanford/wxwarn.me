import celery

from wxwarn.utils import get_users_location
from wxwarn.utils import get_weather_alerts as _get_weather_alerts
from wxwarn.utils import check_users_weather_alerts as _check_users_weather_alerts


@celery.task(name='tasks.update_locations')
def update_locations(premium=False):
    get_users_location(premium=premium)


@celery.task(name='tasks.get_weather_alerts')
def get_weather_alerts():
    _get_weather_alerts()


@celery.task(name='tasks.check_users_weather_alerts')
def check_users_weather_alerts():
    _check_users_weather_alerts()


@celery.task(name='tasks.get_user_location')
def get_user_location(user):
    user_profile = user.get_profile()
    user_profile.get_location()
