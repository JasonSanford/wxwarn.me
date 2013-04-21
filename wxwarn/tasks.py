import logging

from django.conf import settings
import celery
import requests
from bs4 import BeautifulSoup

from wxwarn.utils import get_users_location
from wxwarn.utils import get_weather_alerts as _get_weather_alerts
from wxwarn.utils import check_users_weather_alerts as _check_users_weather_alerts
from wxwarn.models import WeatherAlert

logger = logging.getLogger(__name__)


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


@celery.task(name='tasks.get_weather_alert_details', rate_limit='30/m')
def get_weather_alert_details(id):
    if settings.DEBUG:
        # No sense getting all weather alert details locally. It takes a long time.
        logger.info('Skipping fetch of weather alert details')
        return
    try:
        weather_alert = WeatherAlert.objects.get(id=id)
    except WeatherAlert.DoesNotExist:
        return

    response = requests.get(weather_alert.nws_id)
    soup = BeautifulSoup(response.text)
    description = soup.description.text
    weather_alert.summary = description
    weather_alert.save()
    logger.info('Updated weather alert %s with a better summary' % weather_alert.id)
