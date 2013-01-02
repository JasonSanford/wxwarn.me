import logging
import json
import copy

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
from wxwarn.models import UserWeatherAlert, UserProfile, WeatherAlert, State, WeatherAlertType, UserWeatherAlertTypeExclusion
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

    Show how this whole thing works
    """
    return render_to_response('how_it_works.html', {}, context_instance=RequestContext(request))


def premium(request):
    """
    GET /premium/

    Show the premium upsell page
    """
    return render_to_response('premium.html', {}, context_instance=RequestContext(request))


def signup(request):
    """
    GET /signup/

    Explain that we'll need access to your Google account and Latitdue oauth stuff
    """
    return render_to_response('signup.html', {}, context_instance=RequestContext(request))


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

    Account landing/status page
    """
    user_weather_alerts = UserWeatherAlert.objects.filter(user=request.user)
    user_profile = request.user.get_profile()
    return render_to_response('account/status.html',
            {
                'page': 'landing'
            }, context_instance=RequestContext(request))


@login_required
def account_settings(request):
    """
    GET /account/settings/

    Account landing page
    """
    user_profile = request.user.get_profile()
    weather_alert_types = WeatherAlertType.objects.all().order_by('name')
    weather_alert_type_exclusions = [wat.weather_alert_type.id for wat in UserWeatherAlertTypeExclusion.objects.filter(user=request.user)]
    return render_to_response('account/settings.html',
            {
                'page': 'settings',
                'user_profile_form': UserProfileForm(instance=user_profile),
                'user_profile_id': user_profile.id,
                'weather_alert_types': weather_alert_types,
                'weather_alert_type_exclusions': weather_alert_type_exclusions,
            }, context_instance=RequestContext(request))


@login_required
def user_weather_alerts(request):
    """
    GET /account/my_weather_alerts/

    Account landing page
    """
    user_weather_alerts = UserWeatherAlert.objects.filter(user=request.user)
    user_profile = request.user.get_profile()
    return render_to_response('account/my_weather_alerts.html',
            {
                'page': 'my_weather_alerts',
                'user_weather_alerts': user_weather_alerts,
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
def user_weather_alert_type_exclusions(request):
    # TODO: Make this less ... ugly?
    try:
        weather_alert_settings_dict = json.loads(request.raw_post_data)
    except ValueError:
        return HttpResponseBadRequest(json.dumps({'status': 'error', 'message': 'POSTed data was not JSON serializable.'}))
    for key in weather_alert_settings_dict:
        weather_alert_settings_dict[key]['weather_alert_type'] = WeatherAlertType.objects.get(id=key)
        if weather_alert_settings_dict[key]['value']: # A weather alert type is checked
            try:
                uwate = UserWeatherAlertTypeExclusion.objects.get(user=request.user, weather_alert_type=weather_alert_settings_dict[key]['weather_alert_type'])
            except UserWeatherAlertTypeExclusion.DoesNotExist:
                """
                The weather alert type was checked, but there was no entry
                indicating we should exclude this type. Move along.
                """
                continue
            """
            The weather alert type was checked, and there was an entry indicating
            we should exclude this type. Let's delete it so we send notifications
            for this type of weather alert
            """
            uwate.delete()
        else: # A weather alert type is unchecked
            uwate, created = UserWeatherAlertTypeExclusion.objects.get_or_create(user=request.user, weather_alert_type=weather_alert_settings_dict[key]['weather_alert_type'])
    return HttpResponse(json.dumps({'status': 'success'}), mimetype='application/json')


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
    states = State.objects.all().order_by('name')
    return render_to_response('weather_alerts.html',
            {
                'states': states
            }, context_instance=RequestContext(request))


def weather_alerts_all(request):
    """
    GET /weather_alerts/all/

    View list of all weather alerts
    """
    now = d_now()
    current_weather_alerts = WeatherAlert.objects.filter(effective__lte=now, expires__gte=now)
    states = State.objects.all()
    weather_alerts_by_state = {}
    for state in states:
        weather_alerts_by_state[state.code] = {'name': state.name}
    for current_weather_alert in current_weather_alerts:
        for ugc in current_weather_alert.ugc.split(' '):
            state_code = ugc[:2]
            state = weather_alerts_by_state[state_code]
            state.setdefault('weather_alert_ids', [])
            state.setdefault('weather_alerts', [])
            if not current_weather_alert.id in state['weather_alert_ids']:
                state['weather_alert_ids'].append(current_weather_alert.id)
                state['weather_alerts'].append(current_weather_alert)
    weather_alerts_by_state = sorted(weather_alerts_by_state.items(), key=lambda x: x[1])
    weather_alerts_by_state.sort(key=lambda st:st[1]['name'])
    return render_to_response('weather_alerts_all.html',
            {
                'weather_alert_count': len(current_weather_alerts),
                'weather_alerts_by_state': weather_alerts_by_state,
            }, context_instance=RequestContext(request))


def weather_alerts_state(request, state_code):
    """
    GET /weather_alerts/<state_code>/

    View list of weather alerts for a state
    """
    state_code = state_code.upper()
    try:
        state = State.objects.get(code=state_code)
    except State.DoesNotExist:
        raise Http404
    now = d_now()
    current_weather_alerts = WeatherAlert.objects.filter(effective__lte=now, expires__gte=now)
    current_weather_alerts_for_state = []
    current_weather_alerts_json = {}
    current_weather_alerts_ids = []
    for current_weather_alert in current_weather_alerts:
        for ugc in current_weather_alert.ugc.split(' '):
            ugc_state_code = ugc[:2]
            if ugc_state_code == state_code and current_weather_alert.id not in current_weather_alerts_ids:
                current_weather_alerts_for_state.append(current_weather_alert)
                current_weather_alerts_json[current_weather_alert.id] = {
                    'geojson': current_weather_alert.geojson,
                    'ugc': current_weather_alert.ugc,
                }
                current_weather_alerts_ids.append(current_weather_alert.id)

    return render_to_response('weather_alerts_state.html',
            {
                'weather_alerts': current_weather_alerts_for_state,
                'weather_alerts_json': current_weather_alerts_json,
                'state': {
                    'code': state.code,
                    'name': state.name
                },
                'leaflet': True
            }, context_instance=RequestContext(request))


def weather_alert(request, weather_alert_id):
    """
    GET /weather_alerts/<id>/

    View weather alert details
    """
    try:
        a_weather_alert = WeatherAlert.objects.get(id=weather_alert_id)
    except WeatherAlert.DoesNotExist:
        raise Http404
    return render_to_response('weather_alert.html',
            {
                'weather_alert': a_weather_alert,
                'leaflet': True
            }, context_instance=RequestContext(request))


def weather_alert_geojson(request, weather_alert_id):
    """
    GET /weather_alerts/<id>.geojson

    View weather alert GeoJSON
    """
    try:
        a_weather_alert = WeatherAlert.objects.get(id=weather_alert_id)
    except WeatherAlert.DoesNotExist:
        raise Http404
    return HttpResponse(json.dumps(a_weather_alert.geojson), mimetype='application/json')

