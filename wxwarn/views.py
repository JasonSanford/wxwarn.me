import json
import random

from django.core.paginator import Paginator, EmptyPage as EmptyPageException
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils.timezone import now as d_now

import short_url
from wxwarn.models import UserWeatherAlert, UserProfile, WeatherAlert, State, WeatherAlertType, UserWeatherAlertTypeExclusion, MarineZone, UserLocationStatus
from wxwarn.forms import UserProfileForm, UserActivateForm
from wxwarn.utils import localize_datetime, grouper, cut_linestring
from geometry import dcr as dcr_geometry
from shapely.geometry import asShape, mapping


MILES_PER_DEGREE = 58.77836087838773


def dcr(request):
    jason = User.objects.get(id=1)
    last_location = json.loads(jason.get_profile().last_location.geometry)

    # TODO: Kill this hack to fake location on route before DCR day
    #last_location = {'type': 'Point', 'coordinates': [-105.25382995605467, 39.715109947757554]}

    last_location_shape = asShape(last_location)
    dcr_shape = asShape(dcr_geometry)

    linestrings = cut_linestring(dcr_shape, last_location_shape)

    enhanced_route = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': mapping(linestring),
                'properties': {
                    'span': 'past' if i == 0 else 'future',
                    'distance': linestring.length * MILES_PER_DEGREE
                }
            }
            for i, linestring in enumerate(linestrings)
        ]
    }
    last_location = {
        'type': 'Feature',
        'properties': {
            'distance': linestrings[0].length * MILES_PER_DEGREE
        },
        'geometry': {
            'type': 'Point',
            'coordinates': linestrings[0].coords[-1]
        }
    }

    context = {
        'route_geojson': json.dumps(enhanced_route),
        'last_location': json.dumps(last_location),
        'distance_complete': '%.1f' % (linestrings[0].length * MILES_PER_DEGREE),
        'distance_to_go': '%.1f' % (linestrings[1].length * MILES_PER_DEGREE)
    }
    return render(request, 'dcr.html', context)


def home(request):
    """
    GET /

    Show the home page
    """
    if request.user.is_authenticated():
        return redirect('account_landing')
    context = {
        'hero_image': random.choice(['flood', 'lightning'])
    }
    return render(request, 'index.html', context)


def how_it_works(request):
    """
    GET /how_it_works/

    Show how this whole thing works
    """
    return render(request, 'how_it_works.html')


def premium(request):
    """
    GET /premium/

    Show the premium upsell page
    """
    return render(request, 'premium.html')


def signup(request):
    """
    GET /signup/

    Explain that we'll need access to your Google account and Latitdue oauth stuff
    """
    return render(request, 'signup.html')


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
    try:
        user_location_status = UserLocationStatus.objects.get(user=request.user)
    except UserLocationStatus.DoesNotExist:
        user_location_status = None

    status_message_template = None

    if user_location_status is not None:
        if user_location_status.location_status == UserLocationStatus.LOCATION_STATUS_OK:
            user_location_status_message = 'We\'re successfully tracking your location.'
        elif user_location_status.location_status == UserLocationStatus.LOCATION_STATUS_NOT_OPTED_IN:
            user_location_status_message = 'You have not opted in to Google Latitude.'
            status_message_template = 'account/status_enable_history.html'
        elif user_location_status.location_status == UserLocationStatus.LOCATION_STATUS_INVALID_CREDENTIALS:
            user_location_status_message = 'Invalid credentials.'
        elif user_location_status.location_status == UserLocationStatus.LOCATION_STATUS_NO_HISTORY:
            user_location_status_message = 'You have no Google Latitude history.'
        else:
            user_location_status_message = 'There was an error tracking your location.'

        user_location_status_success_error = 'success' if user_location_status.location_status == UserLocationStatus.LOCATION_STATUS_OK else 'error'
        last_location_check = localize_datetime(request.user, user_location_status.updated)
    else:
        user_location_status_message = 'You must be new here. We haven\'t quite got around to checking your location yet, but refresh to see if we have.'
        user_location_status_success_error = 'error'
        last_location_check = None

    user_profile = request.user.get_profile()

    user_last_location = user_profile.last_location
    user_last_locations = {
        'type': 'FeatureCollection',
        'features': [
            user_location.geojson() for user_location in user_profile.last_locations(minutes=1440)
        ]
    }

    return render(
        request,
        'account/status.html',
        {
            'page': 'landing',
            'user_profile_id': user_profile.id,
            'user_location_status': user_location_status,
            'user_location_status_ok': user_location_status is not None and user_location_status.location_status == UserLocationStatus.LOCATION_STATUS_OK,
            'user_location_status_message': user_location_status_message,
            'user_location_status_success_error': user_location_status_success_error,
            'last_location_check': last_location_check,
            'user_last_location': json.dumps(user_last_location.geojson() if user_last_location is not None else None),
            'user_last_locations': json.dumps(user_last_locations),
            'status_message_template': status_message_template,
            'leaflet': True,
        })


@login_required
def account_settings(request):
    """
    GET /account/settings/

    Account landing page
    """
    user_profile = request.user.get_profile()
    weather_alert_types = WeatherAlertType.objects.all().order_by('name')
    weather_alert_type_exclusions = [wat.weather_alert_type.id for wat in UserWeatherAlertTypeExclusion.objects.filter(user=request.user)]
    return render(
        request,
        'account/settings.html',
        {
            'page': 'settings',
            'user_profile_form': UserProfileForm(instance=user_profile),
            'user_profile_id': user_profile.id,
            'weather_alert_types': weather_alert_types,
            'weather_alert_type_exclusions': weather_alert_type_exclusions,
        })


@login_required
def account_activate_deactivate(request):
    """
    GET /account/activate_deactivate/

    Account landing page
    """
    user_profile = request.user.get_profile()
    return render(
        request,
        'account/activate_deactivate.html',
        {
            'page': 'activate_deactivate',
            'user_profile_id': user_profile.id,
        })


@login_required
def user_weather_alerts(request):
    """
    GET /account/my_weather_alerts/

    Account landing page
    """
    user_weather_alerts = UserWeatherAlert.objects.filter(user=request.user).order_by('-weather_alert__expires')

    active = [uwa for uwa in user_weather_alerts if uwa.weather_alert.active]
    expired = [uwa for uwa in user_weather_alerts if not uwa.weather_alert.active]

    requested_page = request.GET.get('page', 1)

    try:
        requested_page = int(requested_page)
    except ValueError:
        return redirect('user_weather_alerts')

    paginated = Paginator(expired, 12)

    try:
        current_page = paginated.page(requested_page)
    except EmptyPageException:
        if requested_page == 0:
            return redirect('%s?page=%s' % (reverse('user_weather_alerts'), 1))
        else:
            return redirect('%s?page=%s' % (reverse('user_weather_alerts'), paginated.num_pages))

    previous_page_number = current_page.previous_page_number() if current_page.has_previous() else None
    next_page_number = current_page.next_page_number() if current_page.has_next() else None

    active_groups = grouper(3, active)
    expired_groups = grouper(3, current_page.object_list)

    return render(
        request,
        'account/my_weather_alerts.html',
        {
            'page': 'my_weather_alerts',
            'user_profile_id': request.user.get_profile().id,
            'active_groups': active_groups,
            'active_count': len(active),
            'expired_groups': expired_groups,
            'expired_count': len(current_page.object_list),
            'expired_count_total': len(expired),
            'start_index': current_page.start_index(),
            'end_index': current_page.end_index(),
            'previous_page_number': previous_page_number,
            'next_page_number': next_page_number,
        })


def user_weather_alert(request, user_weather_alert_id=None, user_weather_alert_short_url=None):
    if not (user_weather_alert_id or user_weather_alert_short_url):
        return redirect('wxwarn.views.home')
    if user_weather_alert_short_url:
        try:
            user_weather_alert_id = short_url.decode_url(user_weather_alert_short_url)
        except:  # No good exception to catch, library complains of substring error
            raise Http404

    try:
        a_user_weather_alert = UserWeatherAlert.objects.get(id=user_weather_alert_id)
    except UserWeatherAlert.DoesNotExist:
        raise Http404

    user_location_geojson = a_user_weather_alert.user_location.geojson()
    longitude, latitude = user_location_geojson['geometry']['coordinates']

    return render(
        request,
        'user_weather_alert.html',
        {
            'user': a_user_weather_alert.user,
            'user_location': a_user_weather_alert.user_location,
            'user_location_geojson': json.dumps(user_location_geojson),
            'weather_alert_geojson': json.dumps(a_user_weather_alert.weather_alert.geojson()),
            'user_location_latitude': latitude,
            'user_location_longitude': longitude,
            'user_location_last_located': localize_datetime(a_user_weather_alert.user, a_user_weather_alert.user_location.updated),
            'weather_alert': a_user_weather_alert.weather_alert,
            'weather_alert_location_id': a_user_weather_alert.weather_alert_location_id,
            'effective': localize_datetime(a_user_weather_alert.user, a_user_weather_alert.weather_alert.effective),
            'expires': localize_datetime(a_user_weather_alert.user, a_user_weather_alert.weather_alert.expires),
            'leaflet': True,
        })


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
        if weather_alert_settings_dict[key]['value']:  # A weather alert type is checked
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
        else:  # A weather alert type is unchecked
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


@login_required
@require_POST
def user_activate(request):
    if request.user.id != int(request.POST['id']):
        return HttpResponseForbidden()

    a_user_profile = UserProfile.objects.get(id=request.POST['id'])

    form = UserActivateForm(request.POST, instance=a_user_profile)

    if form.is_valid():
        form.save()
        return redirect('account_landing')
    else:
        message = ''
        for field, errors in form.errors.items():
            for error in errors:
                message += 'Field %s: %s' % (field, error)
        return HttpResponseBadRequest(json.dumps({'status': 'error', 'message': message}), mimetype='application/json')


def weather_alerts(request):
    states = State.objects.all().order_by('name')
    marine_zones = MarineZone.objects.all().order_by('name')
    return render(
        request,
        'weather_alerts.html',
        {
            'state_groups': grouper(10, states),
            'marine_zone_groups': grouper(10, marine_zones)
        })


def weather_alerts_state(request, state_code):
    """
    GET /weather_alerts/state/<state_code>/

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
        for location_id in current_weather_alert.location_ids.split(' '):
            location_id_code = location_id[:2]
            if location_id_code == state_code and current_weather_alert.id not in current_weather_alerts_ids:
                current_weather_alerts_for_state.append(current_weather_alert)
                current_weather_alerts_json[current_weather_alert.id] = {
                    'geojson': current_weather_alert.geojson(),
                    'location_ids': current_weather_alert.location_ids,
                }
                current_weather_alerts_ids.append(current_weather_alert.id)

    return render(
        request,
        'weather_alerts_state.html',
        {
            'weather_alerts': current_weather_alerts_for_state,
            'weather_alerts_json': json.dumps(current_weather_alerts_json),
            'state': {
                'code': state.code,
                'name': state.name
            },
            'leaflet': True
        })


def weather_alerts_marine(request, zone_slug):
    """
    GET /weather_alerts/marine/<zone_slug>/

    View list of weather alerts for a marine zone
    """
    try:
        marine_zone = MarineZone.objects.get(slug=zone_slug)
    except MarineZone.DoesNotExist:
        raise Http404

    now = d_now()
    marine_zone_codes = marine_zone.codes.split(' ')
    current_weather_alerts = WeatherAlert.objects.filter(effective__lte=now, expires__gte=now)
    current_weather_alerts_for_marine_zone = []
    current_weather_alerts_json = {}
    current_weather_alerts_ids = []
    for current_weather_alert in current_weather_alerts:
        for location_id in current_weather_alert.location_ids.split(' '):
            location_id_code = location_id[:2]
            if location_id_code in marine_zone_codes and current_weather_alert.id not in current_weather_alerts_ids:
                current_weather_alerts_for_marine_zone.append(current_weather_alert)
                current_weather_alerts_json[current_weather_alert.id] = {
                    'geojson': current_weather_alert.geojson(),
                    'location_ids': current_weather_alert.location_ids,
                }
                current_weather_alerts_ids.append(current_weather_alert.id)

    return render(
        request,
        'weather_alerts_marine.html',
        {
            'weather_alerts': current_weather_alerts_for_marine_zone,
            'weather_alerts_json': json.dumps(current_weather_alerts_json),
            'marine_zone': marine_zone,
            'leaflet': True
        })


def weather_alert(request, weather_alert_id):
    """
    GET /weather_alerts/<id>/

    View weather alert details
    """
    try:
        a_weather_alert = WeatherAlert.objects.get(id=weather_alert_id)
    except WeatherAlert.DoesNotExist:
        raise Http404
    return render(
        request,
        'weather_alert.html',
        {
            'weather_alert': a_weather_alert,
            'weather_alert_geojson': json.dumps(a_weather_alert.geojson()),
            'effective': localize_datetime(request.user, a_weather_alert.effective),
            'expires': localize_datetime(request.user, a_weather_alert.expires),
            'leaflet': True,
        })


def weather_alert_geojson(request, weather_alert_id):
    """
    GET /weather_alerts/<id>.geojson

    View weather alert GeoJSON
    """
    try:
        a_weather_alert = WeatherAlert.objects.get(id=weather_alert_id)
    except WeatherAlert.DoesNotExist:
        raise Http404
    return HttpResponse(json.dumps(a_weather_alert.geojson()), mimetype='application/json')
