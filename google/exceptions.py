class LatitudeUnknown(Exception):
    'An unknown Latitude exception occured'
    pass


class LatitudeNotOptedIn(Exception):
    'The user is not opted in to Google Latitude'
    pass


class LatitudeInvalidCredentials(Exception):
    'The user has not authorized this application to access Latitude data'
    pass


class LatitudeNoLocationHistory(Exception):
    'The user has no Latitude location history'
    pass
