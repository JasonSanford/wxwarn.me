from django.contrib import admin
from wxwarn.models import UserProfile, UserLocation, UserLocationStatus


admin.site.register(UserProfile)
admin.site.register(UserLocation)
admin.site.register(UserLocationStatus)
