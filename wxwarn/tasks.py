import logging

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


@celery.task(name='tasks.cancel_weather_alerts')
def cancel_weather_alerts(our_current_weather_alert_ids, their_current_weather_alert_ids):
    #print 'ours'
    #print our_current_weather_alert_ids
    #print 'theirs'
    #print their_current_weather_alert_ids
    for our_weather_alert_id in our_current_weather_alert_ids:
        if our_weather_alert_id not in their_current_weather_alert_ids:
            logger.info('Update weather alert %s. Cancelled.' % our_weather_alert_id)
            WeatherAlert.objects.filter(nws_id=our_weather_alert_id).update(cancelled=True)
