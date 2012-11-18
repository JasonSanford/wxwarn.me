import logging
import json

from djangomako.shortcuts import render_to_response
from django.shortcuts import redirect, render
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template import RequestContext
from social_auth.models import UserSocialAuth

from wxwarn.utils import get_user_location


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
    social_auth_user = UserSocialAuth.objects.get(
            user = request.user,
            provider = 'google-oauth2')
    user_profile = request.user.get_profile()
    all_locations = user_profile.all_locations
    return render_to_response('account_landing.html',
            {
                'leaflet': True,
                'last_location': json.dumps(user_profile.last_location),
                'all_locations': json.dumps(all_locations),
                'location_count': len(all_locations['geometries'])
            }, context_instance=RequestContext(request))

