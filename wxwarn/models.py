import json

from django.db import models
from django.contrib.auth.models import User
from jsonfield.fields import JSONField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.timezone import now as d_now
from shapely.geometry import asShape

import short_url


class County(models.Model):
    id = models.CharField(max_length=6, primary_key=True) # 6 digit fips
    name = models.CharField(max_length=200)
    state_name = models.CharField(max_length=100)
    state_fips = models.CharField(max_length=6)
    county_fips = models.CharField(max_length=6)
    geometry = models.TextField()

    @property
    def shape(self): # via Shapely
        return asShape(json.loads(self.geometry))

    @property
    def geojson(self):
        return {
            'id': self.id,
            'type': 'Feature',
            'properties': {
                'name': self.name,
                'state_name': self.state_name,
                'state_fips': self.state_fips,
                'county_fips': self.county_fips,
            },
            'geometry': json.loads(self.geometry)
        }

    def __unicode__(self):
        return '%s County, %s' % (self.name, self.state_name)


class UGC(models.Model):
    id = models.CharField(max_length=6, primary_key=True) # 6 digit UGC code
    name = models.CharField(max_length=1000)
    time_zone = models.CharField(max_length=3)
    fe_area = models.CharField(max_length=3)
    geometry = models.TextField()

    @property
    def shape(self): # via Shapely
        return asShape(json.loads(self.geometry))

    @property
    def geojson(self):
        return {
            'id': self.id,
            'type': 'Feature',
            'properties': {
                'name': self.name,
                'time_zone': self.time_zone,
                'fe_area': self.fe_area
            },
            'geometry': json.loads(self.geometry)
        }

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
    title = models.CharField(max_length=200)
    summary = models.TextField()
    url = models.CharField(max_length=1028)
    fips = models.TextField()
    ugc = models.TextField()
    fake = models.BooleanField(default=False)

    @property
    def geojson(self):
        ugc_codes = self.ugc.split(' ')
        ugcs = UGC.objects.filter(id__in=ugc_codes)
        return {
            'type': 'FeatureCollection',
            'features': [ugc.geojson for ugc in ugcs]
        }

    @property
    def shapes(self):
        polygons = [(feature['id'], asShape(feature['geometry'])) for feature in self.geojson['features']]
        return polygons

    @property
    def active(self):
        now = d_now()
        return self.effective <= now <= self.expires

    def __unicode__(self):
        return self.event


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    active = models.BooleanField(default=True)
    premium = models.BooleanField(default=False)
    sms_number = models.CharField(max_length=50, null=True)
    send_sms_alerts = models.BooleanField(default=False)
    send_email_alerts = models.BooleanField(default=True)

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
            'geometries': [user_location.geojson for user_location in user_locations]
        }

    def __unicode__(self):
        return 'UserProfile: %s' % self.user.username

class LocationSource(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class UserLocation(models.Model):
    user = models.ForeignKey(User)
    source = models.ForeignKey(LocationSource)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created = models.DateTimeField(auto_now_add=True)
    source_created = models.DateTimeField()
    source_data = JSONField()

    @property
    def shape(self):
        return asShape(self.geojson)

    @property
    def geojson(self):
        return dict(
            type = 'Point',
            coordinates = [self.longitude, self.latitude])

    def __unicode__(self):
        # TODO: Add datetime
        return '%s at %s, %s' % (self.user.username,
                                 self.latitude, self.longitude)


class UserWeatherAlert(models.Model):
    user = models.ForeignKey(User)
    user_location = models.ForeignKey(UserLocation)
    weather_alert = models.ForeignKey(WeatherAlert)
    weather_alert_ugc = models.CharField(max_length=6)

    @property
    def weather_alert_shape(self): # A user is only in one ugc while some alerts cover multiple.
        ugc = UGC.objects.get(id=self.weather_alert_ugc)
        return ugc.shape

    def static_map_url(self, width=560, height=450, zoom=10):
        _coords = []
        was = self.weather_alert_shape.simplify(0.005)
        if hasattr(was, 'exterior'): # A Polygon
            coords = list(was.exterior.coords)
            coords = map(lambda coord: (coord[1], coord[0]), coords)
            _coords.append(coords)
        else: # A MultiPolygon
            for polygon in was:
                coords = list(polygon.exterior.coords)
                coords = map(lambda coord: (coord[1], coord[0]), coords)
                _coords.append(coords)
        url = 'http://maps.googleapis.com/maps/api/staticmap?center=%s,%s&zoom=%s&size=%sx%s&sensor=false&markers=color:blue|label:S|%s,%s' %\
                (self.user_location.latitude, self.user_location.longitude, zoom, width, height, self.user_location.latitude, self.user_location.longitude)
        for coords_set in _coords:
            url += '&path=color:0xff0000ff|weight:1|fillcolor:0xFF000033|%s' % '|'.join((','.join((str("{0:.4f}".format(y)) for y in x)) for x in coords_set))
        return url

    @property
    def short_url_id(self):
        return short_url.encode_url(self.id)

    def __unicode__(self):
        return 'UserWeatherAlert: %s for %s' % (self.weather_alert, self.user_location)


def create_user_profile(sender, instance, created, **kwargs):  
    if created:
       profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User) 