import json

from django.db import models
from django.contrib.auth.models import User
from jsonfield.fields import JSONField


class LocationSource(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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
    def geojson(self):
        repr = dict(
            type = 'Point',
            coordinates = [self.longitude, self.latitude]
        )
        return json.dumps(repr)

    def __unicode__(self):
        # TODO: Add datetime
        return '%s at %s, %s' % (self.user.username, self.latitude, self.longitude)
