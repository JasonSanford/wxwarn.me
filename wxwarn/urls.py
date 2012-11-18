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
    # url(r'^wxwarn/', include('wxwarn.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social_auth.urls')),
    url(r'^googlea7b7e9db0856207d.html$', 'wxwarn.views.google_verification', name='google_verification'),
)
