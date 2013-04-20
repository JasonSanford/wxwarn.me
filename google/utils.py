import time
import datetime

from django.conf import settings
import requests

from .exceptions import LatitudeNotOptedIn, LatitudeInvalidCredentials, LatitudeNoLocationHistory, LatitudeUnknown


def get_latitude_location(oauth_data, granularity='best'):
    resource = 'https://www.googleapis.com/latitude/v1/currentLocation?granularity=%s' % granularity
    request = requests.get(
        resource,
        headers={
            'Authorization': 'Bearer ' + oauth_data['access_token']
        }
    )
    data = request.json

    if 'error' in data:
        if data['error']['code'] == 403:
            # User hasn't granted permissions
            # {u'error': {u'code': 403, u'message': u'The user is not opted in to Google Latitude.', u'errors': [{u'domain': u'global', u'message': u'The user is not opted in to Google Latitude.', u'reason': u'insufficientPermissions'}]}}
            raise LatitudeNotOptedIn
        elif data['error']['code'] == 401:
            # User revoked access
            # {u'error': {u'code': 401, u'message': u'Invalid Credentials', u'errors': [{u'locationType': u'header', u'domain': u'global', u'message': u'Invalid Credentials', u'reason': u'authError', u'location': u'Authorization'}]}}
            raise LatitudeInvalidCredentials
        else:
            raise LatitudeUnknown
    elif not ('data' in data and ('timestampMs' in data['data'] and 'latitude' in data['data'] and 'longitude' in data['data'])):
        # No location history
        # {u'data': {u'kind': u'latitude#location'}}
        raise LatitudeNoLocationHistory

    return data


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
    # TODO: Deal with token revoked error
    # {u'error': u'invalid_grant'}
    oauth_data['access_token'] = response['access_token']
    oauth_data['id_token'] = response['id_token']
    oauth_data['expiration_date'] = time.mktime(datetime.datetime.now().timetuple()) + response['expires_in']
    return oauth_data
