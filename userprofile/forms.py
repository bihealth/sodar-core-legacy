from django import forms

from projectroles.models import PROJECT_SETTING_VAL_MAXLENGTH
from projectroles.plugins import ProjectAppPluginPoint
from projectroles.user_settings import get_user_setting, validate_user_setting


# User Settings Form -----------------------------------------------------------


class UserSettingsForm(forms.Form):
    """The form for configuring user settings."""

    def __init__(self, *args, **kwargs):
        #: The user to display the settings for.
        self.user = kwargs.pop('current_user')

        super().__init__(*args, **kwargs)

        # Add settings fields
        self.app_plugins = list(
            sorted(
                [
                    p
                    for p in ProjectAppPluginPoint.get_plugins()
                    if p.user_settings
                ],
                key=lambda x: x.name,
            )
        )

        for p in self.app_plugins:
            for s_key in sorted(p.user_settings):
                s = p.user_settings[s_key]
                s_field = 'settings.{}.{}'.format(p.name, s_key)
                field_kwarg = {
                    'required': False,
                    'label': s.get('label') or '{}.{}'.format(p.name, s_key),
                    'help_text': s.get('description'),
                }
                widget_attrs = {'placeholder': s.get('placeholder') or None}

                if s['type'] == 'STRING':
                    self.fields[s_field] = forms.CharField(
                        max_length=PROJECT_SETTING_VAL_MAXLENGTH,
                        widget=forms.TextInput(attrs=widget_attrs),
                        **field_kwarg,
                    )

                elif s['type'] == 'INTEGER':
                    self.fields[s_field] = forms.IntegerField(
                        widget=forms.TextInput(attrs=widget_attrs),
                        **field_kwarg,
                    )

                elif s['type'] == 'BOOLEAN':
                    self.fields[s_field] = forms.BooleanField(**field_kwarg)

                # Set initial value
                self.initial[s_field] = get_user_setting(
                    user=self.user, app_name=p.name, setting_name=s_key
                )

    def clean(self):
        """Function for custom form validation and cleanup"""

        for p in self.app_plugins:
            for s_key in sorted(p.user_settings):
                s = p.user_settings[s_key]
                s_field = 'settings.{}.{}'.format(p.name, s_key)

                if not validate_user_setting(
                    setting_type=s['type'],
                    setting_value=self.cleaned_data.get(s_field),
                ):
                    self.add_error(s_field, 'Invalid value')

        return self.cleaned_data
