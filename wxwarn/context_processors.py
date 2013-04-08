def extended_user(request):
    is_anonymous = request.user.is_anonymous()
    user_profile = None
    if not is_anonymous:
        user_profile = request.user.get_profile()
    return {
        'extended_user': {
            'display_name': '%s %s' % (request.user.first_name, request.user.last_name) if not is_anonymous else None,
            'active': user_profile.active if not is_anonymous else False
        }
    }
