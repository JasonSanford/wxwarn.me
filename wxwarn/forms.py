from django.forms import ModelForm

from wxwarn.models import UserProfile

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ('send_email_alerts', 'sms_number', 'send_sms_alerts', 'timezone', )