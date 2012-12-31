import datetime
from datetime import timedelta
import json
import logging
import time
from dateutil import parser
import random
import string

import pytz
import requests
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import now as d_now
from django.core.urlresolvers import reverse
from mako.template import Template
from django.utils.html import strip_tags
from social_auth.models import UserSocialAuth
from bs4 import BeautifulSoup
from twilio.rest import TwilioRestClient

from wxwarn.models import LocationSource, UserLocation, UserProfile, WeatherAlert, WeatherAlertType, UserWeatherAlert, County, UGC

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
    print 'Inserting user location data'
    print data
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
    (weather_alert_type, created) = WeatherAlertType.objects.get_or_create(
            name=parsed_alert.find('cap:event').text)
    return {
        'source_created': parser.parse(parsed_alert.published.text),
        'source_updated': parser.parse(parsed_alert.updated.text),
        'effective': parser.parse(parsed_alert.find('cap:effective').text),
        'expires': parser.parse(parsed_alert.find('cap:expires').text),
        'event': parsed_alert.find('cap:event').text,
        'weather_alert_type': weather_alert_type,
        'title': parsed_alert.title.text,
        'summary': parsed_alert.summary.text,
        'url': parsed_alert.link['href'],
        'fips': parsed_alert.find('cap:geocode').findChildren('value')[0].text,
        'ugc': parsed_alert.find('cap:geocode').findChildren('value')[1].text
    }


def check_users_weather_alerts():
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
        #print current_located_user
        for current_weather_alert in current_weather_alerts:
            #print current_weather_alert
            for (ugc, polygon) in current_weather_alert.shapes:
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
                                'weather_alert_ugc': ugc
                            })
                    if created:
                        new_user_weather_alerts.append(user_weather_alert)
                    break
    """
    Gathering of new user alerts complete, send emails
    """
    send_bulk_weather_alerts(new_user_weather_alerts)


def send_bulk_weather_alerts(user_weather_alerts):
    user_weather_alerts_to_email = filter(lambda uwa: uwa.user.get_profile().send_email_alerts, user_weather_alerts)
    user_weather_alerts_to_sms = filter(lambda uwa: uwa.user.get_profile().send_sms_alerts, user_weather_alerts)

    send_bulk_weather_email_alerts(user_weather_alerts_to_email)
    send_bulk_weather_sms_alerts(user_weather_alerts_to_sms)


def send_bulk_weather_email_alerts(user_weather_alerts):
    for user_weather_alert in user_weather_alerts:
        print 'Sending email for UserWeatherAlert: %s' % user_weather_alert.id
        body_template = Template(filename='templates/email/user_weather_alert.html')
        body_html = body_template.render(
            event=user_weather_alert.weather_alert.event,
            title=user_weather_alert.weather_alert.title,
            summary=user_weather_alert.weather_alert.summary.lower(),
            static_map_url=user_weather_alert.static_map_url(),
            weather_alert_short_url='http://wxwarn.me%s' % reverse('user_weather_alert_short', kwargs={'user_weather_alert_short_url': user_weather_alert.short_url_id}),
            )
        body_text = strip_tags(body_html)
        _from = 'Weather Alert <weatheralert@wxwarn.me>'
        to = (user_weather_alert.user.email, )
        subject = user_weather_alert.weather_alert.event

        msg = EmailMultiAlternatives(subject, body_text, _from, to)
        msg.attach_alternative(body_html, 'text/html')
        msg.send()


def send_bulk_weather_sms_alerts(user_weather_alerts):
    client = TwilioRestClient()
    for user_weather_alert in user_weather_alerts:
        print 'Sending SMS alert for UserWeatherAlert: %s' % user_weather_alert.id
        sms_number = user_weather_alert.user.get_profile().sms_number
        if sms_number[:2] != '+1':
            sms_number = '+1%s' % sms_number
        weather_alert_short_url = 'http://wxwarn.me%s' % reverse('user_weather_alert_short', kwargs={'user_weather_alert_short_url': user_weather_alert.short_url_id})
        sms_message = "We've detected a %s near your current location. Details: %s" %\
                (user_weather_alert.weather_alert.event, weather_alert_short_url)
        message = client.sms.messages.create(to=sms_number, from_=settings.TWILIO_FROM_NUMBER, body=sms_message)


def create_fake_weather_alert(user_id):
    user_profile = User.objects.get(id=user_id).get_profile()
    last_location = user_profile.last_location
    print 'I\'m going to create a fake alert near %s, %s.' % (last_location.geojson['coordinates'][0], last_location.geojson['coordinates'][1])
    for ugc in UGC.objects.all():
        if ugc.shape.contains(last_location.shape):
            print 'Found you at %s. UGC: %s' % (ugc.name, ugc.id)
            now = d_now()
            fake_weather_alert = WeatherAlert(
                    nws_id=''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6)),
                    source_created=now,
                    source_updated=now,
                    effective=now-timedelta(minutes=10),
                    expires=now+timedelta(hours=2),
                    event='Winter Weather Advisory',
                    title='Winter Weather Advisory issued November 26 at 4:17AM AKST until November 26 at 12:00PM AKST by NWS',
                    summary='...WINTER WEATHER ADVISORY REMAINS IN EFFECT UNTIL NOON AKST TODAY... A WINTER WEATHER ADVISORY REMAINS IN EFFECT UNTIL NOON AKST TODAY. * SNOW...ADDITIONAL ACCUMULATIONS OF 1 TO 3 INCHES THROUGH NOON MONDAY. STORM TOTAL ACCUMULATION OF 5 TO 8 INCHES SINCE SUNDAY',
                    url='http://wxwarn.me',
                    ugc=ugc.id,
                    fake=True)
            fake_weather_alert.save()
            break
    check_users_weather_alerts()


def grouper(n, iterable, fillvalue=None):
    from itertools import izip_longest
    "Collect data into fixed-length chunks or blocks"
    # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)
