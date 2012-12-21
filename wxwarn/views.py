import logging
import json

from djangomako.shortcuts import render_to_response
from django.shortcuts import redirect, render
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils.timezone import now as d_now
from social_auth.models import UserSocialAuth

import short_url
from wxwarn.utils import get_user_location
from wxwarn.models import UserWeatherAlert, UserProfile, WeatherAlert
from wxwarn.forms import UserProfileForm


def home(request):
    """
    GET /

    Show the home page
    """
    if request.user.is_authenticated():
        return redirect('account_landing')
    return render_to_response('index.html', {}, context_instance=RequestContext(request))


def how_it_works(request):
    """
    GET /how_it_works/

    Show the home page
    """
    return render_to_response('how_it_works.html', {}, context_instance=RequestContext(request))


def logout(request):
    """
    GET /logout/

    Log the current user out
    """
    auth_logout(request)
    return redirect('wxwarn.views.home')


@login_required
def account_landing(request):
    """
    GET /account/

    Account landing page
    """
    user_weather_alerts = UserWeatherAlert.objects.filter(user=request.user)
    user_profile = request.user.get_profile()
    return render_to_response('account_landing.html',
            {
                'leaflet': True,
                'user_weather_alerts': user_weather_alerts,
                'user_profile_form': UserProfileForm(instance=user_profile),
                'user_profile_id': user_profile.id
            }, context_instance=RequestContext(request))


def user_weather_alert(request, user_weather_alert_id=None, user_weather_alert_short_url=None):
    if not (user_weather_alert_id or user_weather_alert_short_url):
        return redirect('wxwarn.views.home')
    if user_weather_alert_short_url:
        try:
            user_weather_alert_id = short_url.decode_url(user_weather_alert_short_url)
        except: # No good exception to catch, library complains of substring error
            raise Http404

    try:
        a_user_weather_alert = UserWeatherAlert.objects.get(id=user_weather_alert_id)
    except UserWeatherAlert.DoesNotExist:
        raise Http404
    return render_to_response('user_weather_alert.html',
            {
                'user': a_user_weather_alert.user,
                'user_location': a_user_weather_alert.user_location,
                'weather_alert': a_user_weather_alert.weather_alert,
                'weather_alert_ugc': a_user_weather_alert.weather_alert_ugc,
                'leaflet': True,
            }, context_instance=RequestContext(request))


@login_required
@require_POST
def user_profile(request):
    if request.user.id != int(request.POST['id']):
        return HttpResponseForbidden()
    a_user_profile = UserProfile.objects.get(id=request.POST['id'])
    form = UserProfileForm(request.POST, instance=a_user_profile)
    if form.is_valid():
        form.save()
        return HttpResponse(json.dumps({'status': 'success'}), mimetype='application/json')
    else:
        message = ''
        for field, errors in form.errors.items():
            for error in errors:
                message += 'Field %s: %s' % (field, error)
        return HttpResponseBadRequest(json.dumps({'status': 'error', 'message': message}), mimetype='application/json')


def weather_alerts(request):
    now = d_now()
    current_weather_alerts = WeatherAlert.objects.filter(effective__lte=now, expires__gte=now)
    return render_to_response('weather_alerts.html',
            {
                'current_weather_alerts': current_weather_alerts
            }, context_instance=RequestContext(request))


def weather_alert(request, weather_alert_id):
    try:
        a_weather_alert = WeatherAlert.objects.get(id=weather_alert_id)
    except WeatherAlert.DoesNotExist:
        raise Http404
    return render_to_response('weather_alert.html',
            {
                'weather_alert': a_weather_alert,
                'leaflet': True
            }, context_instance=RequestContext(request))

