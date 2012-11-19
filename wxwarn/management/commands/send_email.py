from django.core.management.base import BaseCommand
from django.core.mail import send_mail


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        _from = kwargs.get('from', 'jason@wxwarn.me')
        to = kwargs.get('to', ['jasonsanford@gmail.com'])
        subject = kwargs.get('subject', 'Weather Alert')
        body = kwargs.get('body', 'There is a tornado warning in your area. Take cover.')

        send_mail(subject, body, _from, to, fail_silently=False)
