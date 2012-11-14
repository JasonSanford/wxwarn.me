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


def get_user_location(social_auth_user):
    # TODO: support things other than latitude here
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
        print latitude_data
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
