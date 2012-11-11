from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        non_admin_users = User.objects.filter(id__gt=1)
        non_admin_users.delete()