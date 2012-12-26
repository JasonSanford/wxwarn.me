from django.conf.urls import patterns, include, url
from django.contrib import admin

from social_auth.views import auth

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'wxwarn.views.home', name='home'),
    url(r'^how-it-works/$', 'wxwarn.views.how_it_works', name='how_it_works'),
    url(r'^login/$', auth, kwargs={'backend': 'google-oauth2'}, name='login'),
    url(r'^logout/$', 'wxwarn.views.logout', name='logout'),
    url(r'^account/$', 'wxwarn.views.account_landing', name='account_landing'),
    url(r'^account/my_weather_alerts/$', 'wxwarn.views.user_weather_alerts', name='user_weather_alerts'),
    url(r'^account/settings/$', 'wxwarn.views.account_settings', name='account_settings'),
    url(r'^user_profile/$', 'wxwarn.views.user_profile', name='user_profile'),
    url(r'^alert/(?P<user_weather_alert_id>\d+)/$', 'wxwarn.views.user_weather_alert', name='user_weather_alert'),
    url(r'^a/(?P<user_weather_alert_short_url>.+)/$', 'wxwarn.views.user_weather_alert', name='user_weather_alert_short'),
    url(r'^weather_alerts/$', 'wxwarn.views.weather_alerts', name='weather_alerts'),
    url(r'^weather_alerts/(?P<weather_alert_id>\d+)/$', 'wxwarn.views.weather_alert', name='weather_alert'),
    url(r'^weather_alerts/(?P<weather_alert_id>\d+).geojson$', 'wxwarn.views.weather_alert_geojson', name='weather_alert_geojson'),
    

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social_auth.urls')),
)
