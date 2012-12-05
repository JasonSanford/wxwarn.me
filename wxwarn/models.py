import json

from django.db import models
from django.contrib.auth.models import User
from jsonfield.fields import JSONField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from shapely.geometry import asShape


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
    fake = models.BooleanField(default=False)

    @property
    def geojson(self):
        fips_codes = self.fips.split(' ')
        counties = County.objects.filter(id__in=fips_codes)
        return {
            'type': 'FeatureCollection',
            'features': [county.geojson for county in counties]
        }

    @property
    def shapes(self):
        polygons = [(feature['id'], asShape(feature['geometry'])) for feature in self.geojson['features']]
        return polygons

    def __unicode__(self):
        return self.event


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    active = models.BooleanField(default=True)
    premium = models.BooleanField(default=False)

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
    weather_alert_fips = models.CharField(max_length=6)

    @property
    def weather_alert_shape(self): # A user is only in one county while some alerts cover multiple.
        county = County.objects.get(id=self.weather_alert_fips)
        return county.shape

    @property
    def static_map_url(self, width=560, height=450, zoom=10):
        coords = list(self.weather_alert_shape.exterior.coords)
        coords = map(lambda coord: (coord[1], coord[0]), coords)
        path_str = '|'.join((','.join((str(y) for y in x)) for x in coords))
        return 'http://maps.googleapis.com/maps/api/staticmap?center=%s,%s&zoom=%s&size=%sx%s&sensor=false&path=color:0xff0000ff|weight:1|fillcolor:0xFF000033|%s&markers=color:blue|label:S|%s,%s' %\
                (self.user_location.latitude, self.user_location.longitude, zoom, width, height, path_str, self.user_location.latitude, self.user_location.longitude)

    def __unicode__(self):
        return 'UserWeatherAlert: %s for %s' % (self.weather_alert, self.user_location)


def create_user_profile(sender, instance, created, **kwargs):  
    if created:
       profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User) 