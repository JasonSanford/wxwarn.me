import logging

from djangomako.shortcuts import render_to_response
from django.shortcuts import redirect, render
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template import RequestContext


def home(request):
    """
    GET /

    Show the home page
    """
    return render_to_response('index.html', {}, context_instance=RequestContext(request))


def how_it_works(request):
    """
    GET /about/

    Show the home page
    """
    return render_to_response('how-it-works.html', {}, context_instance=RequestContext(request))


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
    return render_to_response('account_landing.html', {}, context_instance=RequestContext(request))

