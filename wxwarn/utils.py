from datetime import timedelta
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
from bs4 import BeautifulSoup
from twilio.rest import TwilioRestClient

from wxwarn.models import UserLocation, UserProfile, WeatherAlert, WeatherAlertType, UserWeatherAlert, County, UGC, UserWeatherAlertTypeExclusion, LocationType, Marine

#WEATHER_ALERTS_URL = 'http://localhost:8000/static/weather_alerts.xml'
WEATHER_ALERTS_URL = 'http://alerts.weather.gov/cap/us.php?x=0'
MARINE_WEATHER_ALERTS_URL = 'http://alerts.weather.gov/cap/mzus.php?x=0'

USER_LOCATION_MAX_AGE = 60 * 12


def localize_datetime(user, datetime):
    if user.is_authenticated():
        user_profile = user.get_profile()
        try:
            local_tz = pytz.timezone(user_profile.timezone.name)
            converted = datetime.astimezone(local_tz)
        except pytz.UnknownTimeZoneError:
            print 'UnknownTimeZoneError thrown for user %s, %s' % (user, user_profile.timezone.name)
            converted = datetime
    else:
        # TODO: Guess at timezone for unauth'd users
        converted = datetime
    # TODO: Customizable datetime format
    return converted.strftime('%a, %d %b %Y %H:%M')


def get_users_location(premium=False):
    user_profiles = UserProfile.objects.filter(premium=premium, active=True)

    for user_profile in user_profiles:
        user_profile.get_location()


def get_weather_alerts():
    weather_alert_categories = {
        'land': WEATHER_ALERTS_URL,
        'marine': MARINE_WEATHER_ALERTS_URL,
    }
    for weather_alert_category in weather_alert_categories:
        response = requests.get(weather_alert_categories[weather_alert_category])
        soup = BeautifulSoup(response.text)
        parsed_alerts = soup.find_all('entry')
        insert_count = 0
        update_count = 0
        print 'Total %s alerts from NWS: %s' % (weather_alert_category, len(parsed_alerts))
        for parsed_alert in parsed_alerts:
            data_dict = _create_data_dict(parsed_alert, weather_alert_category)
            (weather_alert, created) = WeatherAlert.objects.get_or_create(
                    nws_id=parsed_alert.id.text,
                    defaults=data_dict)
            if not created and data_dict['source_updated'] > weather_alert.source_updated:
                weather_alert.__dict__.update(data_dict)
                weather_alert.save()
                update_count += 1
            if created:
                insert_count += 1
        print 'New %s alerts: %s' % (weather_alert_category, insert_count)
        print 'Updated %s alerts: %s' % (weather_alert_category, update_count)


def _create_data_dict(parsed_alert, weather_alert_category):
    (weather_alert_type, created) = WeatherAlertType.objects.get_or_create(name=parsed_alert.find('cap:event').text)

    fips = parsed_alert.find('cap:geocode').findChildren('value')[0].text
    ugc = parsed_alert.find('cap:geocode').findChildren('value')[1].text
    ugcs = ugc.split(' ')

    if weather_alert_category == 'land':
        if ugcs[0][2] == 'C':
            # It seems all flood types use C, so use county instead :/
            location_type_name = 'FIPS'
            location_ids = fips
        else:
            # It's a normal UGC zone
            location_type_name = 'UGC'
            location_ids = ugc
    elif weather_alert_category == 'marine':
        location_type_name = 'Marine'
        location_ids = ugc

    location_type = LocationType.objects.get(name=location_type_name)

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
        'fips': fips,
        'ugc': ugc,
        'location_type': location_type,
        'location_ids': location_ids,
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
            .filter(created__gte=now - timedelta(minutes=USER_LOCATION_MAX_AGE))\
            .distinct('user')\
            .order_by('user', '-created')
    print 'Current located user count: %s' % len(current_located_users)
    new_user_weather_alerts = []
    for current_located_user in current_located_users:
        weather_alert_type_exclusions = [uwate.weather_alert_type.id for uwate in UserWeatherAlertTypeExclusion.objects.filter(user=current_located_user.user)]
        for current_weather_alert in current_weather_alerts:
            for (location_id, bbox) in current_weather_alert.shapes(bbox=True):
                if bbox.contains(current_located_user.shape):
                    """
                    The user is in at least the bounding box of a weather
                    alert. Let's see if the actually polygon contains
                    the user.
                    """
                    if current_weather_alert.location_type.name == 'UGC':
                        TheModel = UGC
                    elif current_weather_alert.location_type.name == 'FIPS':
                        TheModel = County
                    elif current_weather_alert.location_type.name == 'Marine':
                        TheModel = Marine

                    weather_alert_shape = TheModel.objects.get(id=location_id).shape

                    if weather_alert_shape.contains(current_located_user.shape):
                        """
                        The user is in a weather alert polygon
                        Let's see if we've already alerted them.
                        """
                        (user_weather_alert, created) = UserWeatherAlert.objects.get_or_create(
                                user=current_located_user.user,
                                weather_alert=current_weather_alert,
                                defaults={
                                    'user_location': current_located_user,
                                    'weather_alert_location_id': location_id
                                })
                        if created and current_weather_alert.weather_alert_type.id not in weather_alert_type_exclusions:
                            new_user_weather_alerts.append(user_weather_alert)
                        break
    """
    Gathering of new user alerts complete, send emails and texts
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
    user = User.objects.get(id=user_id)
    last_location = UserLocation.objects.filter(user=user).order_by('-created')[0]
    print 'I\'m going to create a fake alert near %s, %s.' % (last_location.geojson()['geometry']['coordinates'][0], last_location.geojson()['geometry']['coordinates'][1])
    for ugc in UGC.objects.all():
        if ugc.shape.contains(last_location.shape):
            print 'Found you at %s. UGC: %s' % (ugc.name, ugc.id)
            now = d_now()
            fake_weather_alert = WeatherAlert(
                    nws_id=''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6)),
                    source_created=now,
                    source_updated=now,
                    effective=now - timedelta(minutes=10),
                    expires=now + timedelta(hours=2),
                    event='Winter Weather Advisory',
                    title='Winter Weather Advisory issued November 26 at 4:17AM AKST until November 26 at 12:00PM AKST by NWS',
                    summary='...WINTER WEATHER ADVISORY REMAINS IN EFFECT UNTIL NOON AKST TODAY... A WINTER WEATHER ADVISORY REMAINS IN EFFECT UNTIL NOON AKST TODAY. * SNOW...ADDITIONAL ACCUMULATIONS OF 1 TO 3 INCHES THROUGH NOON MONDAY. STORM TOTAL ACCUMULATION OF 5 TO 8 INCHES SINCE SUNDAY',
                    url='http://wxwarn.me',
                    ugc=ugc.id,
                    location_type=LocationType.objects.get(name='UGC'),
                    location_ids=ugc.id,
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
