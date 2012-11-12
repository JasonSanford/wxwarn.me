import json

from django.db import models
from django.contrib.auth.models import User
from jsonfield.fields import JSONField
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class UserProfile(models.Model):

    user = models.OneToOneField(User)

    @property
    def last_location(self):
        try:
            user_location = UserLocation.objects\
                                .filter(user=self.user)\
                                .order_by('-source_created')[0]
        except IndexError:
            return None
        return user_location.geojson


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
    def geojson(self):
        return dict(
            type = 'Point',
            coordinates = [self.longitude, self.latitude])

    def __unicode__(self):
        # TODO: Add datetime
        return '%s at %s, %s' % (self.user.username,
                                 self.latitude, self.longitude)


def create_user_profile(sender, instance, created, **kwargs):  
    if created:
       profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User) 