import datetime
import json
import logging
import time

import pytz
import requests
from django.contrib.auth.models import User
from django.conf import settings
from social_auth.models import UserSocialAuth

from wxwarn.models import LocationSource, UserLocation, UserProfile

def get_user_location(user, location_source):
    pass

def get_users_location(premium=False):
    if premium:
        user_profiles = UserProfile.objects.filter(premium=True)
    else:
        user_profiles = UserProfile.objects.all()
    
    for user_profile in user_profiles:
        social_auth_user = UserSocialAuth.objects.get(
                user = user_profile.user,
                provider = 'google-oauth2')
        extra_data = social_auth_user.extra_data

        if 'expiration_date' not in extra_data.keys():
            extra_data['expiration_date'] = 0
        if extra_data['expiration_date'] < time.mktime(datetime.datetime.now().timetuple()):
            extra_data = refresh_access_token(extra_data)

        latitude_data = get_current_location(extra_data)
        # TODO: Protect against user permissions
        # {u'error': {u'code': 403, u'message': u'The user is not opted in to Google Latitude.', u'errors': [{u'domain': u'global', u'message': u'The user is not opted in to Google Latitude.', u'reason': u'insufficientPermissions'}]}}
        print latitude_data
        insert_user_location(latitude_data, user_profile.user)

        social_auth_user.extra_data = extra_data
        social_auth_user.save()


def refresh_access_token(data):
    r = requests.post(
            'https://accounts.google.com/o/oauth2/token',
            data={
                'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                'refresh_token': data['refresh_token'],
                'grant_type': 'refresh_token'
                },
            )
    response = json.loads(r.text)
    data['access_token'] = response['access_token']
    data['id_token'] = response['id_token']
    data['expiration_date'] = time.mktime(datetime.datetime.now().timetuple()) + response['expires_in']
    return data


def get_current_location(data):
    r = requests.get(
            'https://www.googleapis.com/latitude/v1/currentLocation?granularity=best',
            headers={
                'Authorization': 'Bearer ' + data['access_token']
                }
            )
    response = json.loads(r.text)
    return response


def insert_user_location(data, user):
    gmt = pytz.timezone('GMT')
    logging.info(data)
    source_date = datetime.datetime.fromtimestamp(float(data['data']['timestampMs']) / 1000, gmt)
    (location_source, created) = LocationSource.objects.get_or_create(name='Google Latitude')

    user_location = UserLocation()
    user_location.user = user
    user_location.latitude = data['data']['latitude']
    user_location.longitude = data['data']['longitude']
    user_location.source = location_source
    user_location.source_data = data
    user_location.source_created = source_date
    user_location.save()
