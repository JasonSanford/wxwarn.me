import celery

from wxwarn.utils import get_users_location

@celery.task(name='tasks.update_locations')
def update_locations(premium=False):
    get_users_location(premium=premium)