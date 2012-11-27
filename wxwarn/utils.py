import datetime
from datetime import timedelta
import json
import logging
import time
from dateutil import parser

import pytz
import requests
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now as d_now
from social_auth.models import UserSocialAuth
from bs4 import BeautifulSoup

from wxwarn.models import LocationSource, UserLocation, UserProfile, WeatherAlert, UserWeatherAlert

#WEATHER_ALERTS_URL = 'http://localhost:8000/static/weather_alerts.xml'
WEATHER_ALERTS_URL = 'http://alerts.weather.gov/cap/us.php?x=0'

USER_LOCATION_MAX_AGE = 60 * 3

def get_user_location(social_auth_user):
    # TODO: support things other than Google Latitude here
    if social_auth_user.provider == 'google-oauth2':
        oauth_data = social_auth_user.extra_data

        if 'expiration_date' not in oauth_data.keys():
            oauth_data['expiration_date'] = 0
        if oauth_data['expiration_date'] < time.mktime(datetime.datetime.now().timetuple()):
            oauth_data = refresh_access_token(oauth_data)

        latitude_data = get_latitude_location(oauth_data)
        # TODO: Protect against user permissions
        # {u'error': {u'code': 403, u'message': u'The user is not opted in to Google Latitude.', u'errors': [{u'domain': u'global', u'message': u'The user is not opted in to Google Latitude.', u'reason': u'insufficientPermissions'}]}}
        # TODO: Protect against no location history
        # {u'data': {u'kind': u'latitude#location'}}
        # TODO: Protect against user revoked access
        # {u'error': {u'code': 401, u'message': u'Invalid Credentials', u'errors': [{u'locationType': u'header', u'domain': u'global', u'message': u'Invalid Credentials', u'reason': u'authError', u'location': u'Authorization'}]}}
        #print latitude_data
        insert_user_location(latitude_data, social_auth_user.user)

        social_auth_user.oauth_data = oauth_data
        social_auth_user.save()


def get_users_location(premium=False):
    user_profiles = UserProfile.objects.filter(premium=premium, active=True)
    
    for user_profile in user_profiles:
        social_auth_user = UserSocialAuth.objects.get(
                user = user_profile.user,
                provider = 'google-oauth2')

        get_user_location(social_auth_user)


def refresh_access_token(oauth_data):
    request = requests.post(
            'https://accounts.google.com/o/oauth2/token',
            data={
                'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                'refresh_token': oauth_data['refresh_token'],
                'grant_type': 'refresh_token'
                },
            )
    response = request.json
    oauth_data['access_token'] = response['access_token']
    oauth_data['id_token'] = response['id_token']
    oauth_data['expiration_date'] = time.mktime(datetime.datetime.now().timetuple()) + response['expires_in']
    return oauth_data


def get_latitude_location(oauth_data, granularity='best'):
    resource = 'https://www.googleapis.com/latitude/v1/currentLocation?granularity=%s' % granularity
    request = requests.get(
            resource,
            headers={
                'Authorization': 'Bearer ' + oauth_data['access_token']
                }
            )
    return request.json


def insert_user_location(data, user):
    gmt = pytz.timezone('GMT')
    logging.info(data)
    source_date = datetime.datetime.fromtimestamp(float(data['data']['timestampMs']) / 1000, gmt)
    (location_source, created) = LocationSource.objects.get_or_create(name='Google Latitude')

    user_location = UserLocation(
            user = user,
            latitude = data['data']['latitude'],
            longitude = data['data']['longitude'],
            source = location_source,
            source_data = data,
            source_created = source_date)
    user_location.save()


def get_weather_alerts():
    response = requests.get(WEATHER_ALERTS_URL)
    soup = BeautifulSoup(response.text)
    parsed_alerts = soup.find_all('entry')
    insert_count = 0
    update_count = 0
    print 'Total alerts from NWS: %s' % len(parsed_alerts)
    for parsed_alert in parsed_alerts:
        data_dict = _create_data_dict(parsed_alert)
        (weather_alert, created) = WeatherAlert.objects.get_or_create(
                nws_id=parsed_alert.id.text,
                defaults=data_dict)
        if not created and data_dict['source_updated'] > weather_alert.source_updated:
            weather_alert.__dict__.update(data_dict)
            weather_alert.save()
            update_count += 1
        if created:
            insert_count += 1
    print 'New alerts: %s' % insert_count
    print 'Updated alerts: %s' % update_count


def _create_data_dict(parsed_alert):
    return {
        'source_created': parser.parse(parsed_alert.published.text),
        'source_updated': parser.parse(parsed_alert.updated.text),
        'effective': parser.parse(parsed_alert.find('cap:effective').text),
        'expires': parser.parse(parsed_alert.find('cap:expires').text),
        'event': parsed_alert.find('cap:event').text,
        'title': parsed_alert.title.text,
        'summary': parsed_alert.summary.text,
        'url': parsed_alert.link['href'],
        'fips': parsed_alert.find('cap:geocode').value.text,
    }


def check_user_weather_alerts():
    now = d_now()
    #all = WeatherAlert.objects.all()
    #print 'All is %s' % len(all)
    current_weather_alerts = WeatherAlert.objects\
                                .filter(effective__lte=now)\
                                .filter(expires__gte=now)
    print 'Current alert count: %s' % len(current_weather_alerts)
    current_located_users = UserLocation.objects\
                                .filter(created__gte=now-timedelta(minutes=USER_LOCATION_MAX_AGE))\
                                .distinct('user')\
                                .order_by('user', '-created')
    print 'Current located user count: %s' % len(current_located_users)
    new_user_weather_alerts = []
    for current_located_user in current_located_users:
        print current_located_user
        for current_weather_alert in current_weather_alerts:
            #print current_weather_alert
            for polygon in current_weather_alert.shapes:
                if polygon.contains(current_located_user.shape):
                    """
                    The user is in a weather alert polygon
                    Let's see if we've already alerted them.
                    """
                    (user_weather_alert, created) = UserWeatherAlert.objects.get_or_create(
                            user=current_located_user.user,
                            weather_alert=current_weather_alert,
                            defaults={
                                'user_location': current_located_user,
                            })
                    if created:
                        new_user_weather_alerts.append(user_weather_alert)
                    break
    """
    Gathering of new user alerts complete, send emails
    """
    send_bulk_weather_alert_emails(new_user_weather_alerts)


def send_bulk_weather_alert_emails(user_weather_alerts):
    for user_weather_alert in user_weather_alerts:
        print 'Sending email for UserWeatherAlert: %s' % user_weather_alert.id
