from django.forms import ModelForm

from wxwarn.models import UserProfile


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        if 'sms_number' in self.fields:
            self.fields['sms_number'].required = False

    class Meta:
        model = UserProfile
        fields = ('send_email_alerts', 'sms_number', 'send_sms_alerts', 'timezone', )


class UserActivateForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ('active', )
