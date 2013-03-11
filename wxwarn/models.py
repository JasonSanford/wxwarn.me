import json
import re
import urlparse
from urllib import urlencode

from django.db import models
from django.contrib.auth.models import User
from jsonfield.fields import JSONField
from django.db.models.signals import post_save
from django.utils.timezone import now as d_now
from shapely.geometry import asShape
import gpolyencode

import short_url


MAXIMUM_ENCODED_POINTS = 300
GOOGLE_API_HOST = 'maps.googleapis.com'
GOOGLE_STATIC_PATH = 'maps/api/staticmap'


class LocationType(models.Model):
    name = models.CharField(max_length=100)


class GeoModel(models.Model):
    @property
    def shape(self):  # via Shapely
        return asShape(json.loads(self.geometry))

    def geojson(self, bbox=False):
        properties = {}
        available_fields = [field.name for field in self._meta.fields]
        for display_field in self.display_fields:
            if display_field in available_fields:
                properties[display_field] = getattr(self, display_field)
        return {
            'id': self.id,
            'type': 'Feature',
            'properties': properties,
            'geometry': json.loads(self.geometry_bbox if bbox and 'bbox' in available_fields else self.geometry)
        }

    class Meta:
        abstract = True


class County(GeoModel):
    id = models.CharField(max_length=6, primary_key=True)  # 6 digit fips
    name = models.CharField(max_length=200)
    state_name = models.CharField(max_length=100)
    state_fips = models.CharField(max_length=6)
    county_fips = models.CharField(max_length=6)
    geometry = models.TextField()
    geometry_bbox = models.TextField(null=True)

    display_fields = ['name', 'state_name', 'state_fips']

    def __unicode__(self):
        return '%s County, %s' % (self.name, self.state_name)


class State(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=2)

    def __unicode__(self):
        return self.name


class UGC(GeoModel):
    id = models.CharField(max_length=6, primary_key=True)  # 6 digit UGC code
    name = models.CharField(max_length=1000)
    time_zone = models.CharField(max_length=3)
    fe_area = models.CharField(max_length=3)
    geometry = models.TextField()
    geometry_bbox = models.TextField(null=True)

    display_fields = ['name', 'time_zone', 'fe_area']

    def __unicode__(self):
        return self.name


class MarineZone(models.Model):
    name = models.CharField(max_length=500)
    slug = models.CharField(max_length=200)
    codes = models.CharField(max_length=100)


class Marine(GeoModel):
    id = models.CharField(max_length=6, primary_key=True)  # 6 digit GMZ Code
    name = models.CharField(max_length=1000)
    wfo = models.CharField(max_length=100)
    geometry = models.TextField()
    geometry_bbox = models.TextField(null=True)

    display_fields = ['name', 'wfo']

    def __unicode__(self):
        return self.name


class WeatherAlertType(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name


class WeatherAlert(models.Model):
    nws_id = models.CharField(max_length=1000, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    source_created = models.DateTimeField()
    source_updated = models.DateTimeField()
    effective = models.DateTimeField()
    expires = models.DateTimeField()
    event = models.CharField(max_length=200)
    weather_alert_type = models.ForeignKey(WeatherAlertType, default=1)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    url = models.CharField(max_length=1028)
    fips = models.TextField()
    ugc = models.TextField()
    fake = models.BooleanField(default=False)
    location_type = models.ForeignKey(LocationType, default=1)
    location_ids = models.TextField(default='')

    def geojson(self, bbox=False):

        location_ids = self.location_ids.split(' ')

        if self.location_type.name == 'UGC':
            TheModel = UGC
        elif self.location_type.name == 'FIPS':
            TheModel = County
        elif self.location_type.name == 'Marine':
            TheModel = Marine

        features = TheModel.objects.filter(id__in=location_ids)
        if bbox:
            features.defer('geometry')
        return {
            'type': 'FeatureCollection',
            'features': [feature.geojson(bbox=bbox) for feature in features]
        }

    def shapes(self, bbox=False):
        polygons = [(feature['id'], asShape(feature['geometry'])) for feature in self.geojson(bbox=bbox)['features']]
        return polygons

    @property
    def active(self):
        now = d_now()
        return self.effective <= now <= self.expires

    @property
    def category(self):
        event = self.event

        regex_cold = re.compile('freeze|frost|chill', re.IGNORECASE | re.DOTALL)
        regex_fire = re.compile('fire|red flag', re.IGNORECASE | re.DOTALL)
        regex_flood = re.compile('flood|water', re.IGNORECASE | re.DOTALL)
        regex_snow = re.compile('winter|blizzard|snow|avalanche', re.IGNORECASE | re.DOTALL)
        regex_heat = re.compile('heat', re.IGNORECASE | re.DOTALL)
        regex_thunder = re.compile('thunder', re.IGNORECASE | re.DOTALL)
        regex_tornado = re.compile('tornado', re.IGNORECASE | re.DOTALL)
        regex_wind = re.compile('wind', re.IGNORECASE | re.DOTALL)

        if regex_cold.search(event):
            return 'cold'
        if regex_fire.search(event):
            return 'fire'
        if regex_flood.search(event):
            return 'flood'
        if regex_heat.search(event):
            return 'heat'
        if regex_snow.search(event):
            return 'snow'
        if regex_thunder.search(event):
            return 'thunder'
        if regex_tornado.search(event):
            return 'tornado'
        if regex_wind.search(event):
            return 'wind'
        return None

    def __unicode__(self):
        return self.event


class Timezone(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    active = models.BooleanField(default=True)
    premium = models.BooleanField(default=False)
    sms_number = models.CharField(max_length=50, null=True)
    send_sms_alerts = models.BooleanField(default=False)
    send_email_alerts = models.BooleanField(default=True)
    timezone = models.ForeignKey(Timezone, default=18)  # default to America/Denver

    @property
    def last_location(self):
        try:
            user_location = UserLocation.objects\
                                .filter(user=self.user)\
                                .order_by('-source_created')[0]
        except IndexError:
            return None
        return user_location

    @property
    def all_locations(self):
        user_locations = UserLocation.objects.filter(user=self.user)
        return {
            'type': 'GeometryCollection',
            'geometries': [user_location.geojson() for user_location in user_locations]
        }

    def __unicode__(self):
        return 'UserProfile: %s' % self.user.username


class LocationSource(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class UserLocation(GeoModel):
    user = models.ForeignKey(User)
    source = models.ForeignKey(LocationSource)
    created = models.DateTimeField(auto_now_add=True)
    source_created = models.DateTimeField()
    source_data = JSONField()
    geometry = models.TextField(default=json.dumps({'type': 'Point', 'coordinates': [0, 0]}))

    display_fields = ['']

    def __unicode__(self):
        # TODO: Add datetime
        geojson = json.loads(self.geometry)
        return '%s at %s, %s' % (self.user.username,
                                 geojson['coordinates'][1], geojson['coordinates'][0])


class UserWeatherAlert(models.Model):
    user = models.ForeignKey(User)
    user_location = models.ForeignKey(UserLocation)
    weather_alert = models.ForeignKey(WeatherAlert)
    weather_alert_location_id = models.CharField(max_length=6, null=True)

    @property
    def weather_alert_shape(self):  # A user is only in one location_id while some alerts cover multiple.
        if self.weather_alert.location_type.name == 'UGC':
            TheModel = UGC
        elif self.weather_alert.location_type.name == 'FIPS':
            TheModel = County
        elif self.weather_alert.location_type.name == 'Marine':
            TheModel = Marine
        location = TheModel.objects.get(id=self.weather_alert_location_id)
        return location.shape

    def static_map_url(self, width=560, height=450, zoom=10):
        user_location_geojson = self.user_location.geojson()
        longitude = user_location_geojson['geometry']['coordinates'][0]
        latitude = user_location_geojson['geometry']['coordinates'][1]

        url = 'http://api.tiles.mapbox.com/v3/jcsanford.map-vita0cry/pin-l-star+ff6633(%s,%s)/%s,%s,%s/%sx%s.png' %\
                (longitude, latitude, longitude, latitude, zoom, width, height)

        return url

    @property
    def short_url_id(self):
        return short_url.encode_url(self.id)

    def __unicode__(self):
        return 'UserWeatherAlert: %s for %s' % (self.weather_alert, self.user_location)


class UserWeatherAlertTypeExclusion(models.Model):
    user = models.ForeignKey(User)
    weather_alert_type = models.ForeignKey(WeatherAlertType)

    def __unicode__(self):
        return self.weather_alert_type.name


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
