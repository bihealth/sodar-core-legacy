from django import forms

from projectroles.app_settings import AppSettingAPI
from projectroles.models import APP_SETTING_VAL_MAXLENGTH, SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins


# SODAR Constants
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']


# App settings API
app_settings = AppSettingAPI()


# User Settings Form -----------------------------------------------------------


class UserSettingsForm(forms.Form):
    """The form for configuring user settings."""

    def __init__(self, *args, **kwargs):
        #: The user to display the settings for.
        self.user = kwargs.pop('current_user')

        super().__init__(*args, **kwargs)

        # Add settings fields
        self.app_plugins = get_active_plugins()

        for plugin in self.app_plugins:
            p_settings = app_settings.get_setting_defs(
                plugin, APP_SETTING_SCOPE_USER, user_modifiable=True
            )

            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(plugin.name, s_key)
                field_kwarg = {
                    'required': False,
                    'label': s_val.get('label')
                    or '{}.{}'.format(plugin.name, s_key),
                    'help_text': s_val.get('description'),
                }
                widget_attrs = {'placeholder': s_val.get('placeholder') or None}

                if s_val['type'] == 'STRING':
                    self.fields[s_field] = forms.CharField(
                        max_length=APP_SETTING_VAL_MAXLENGTH,
                        widget=forms.TextInput(attrs=widget_attrs),
                        **field_kwarg,
                    )

                elif s_val['type'] == 'INTEGER':
                    self.fields[s_field] = forms.IntegerField(
                        widget=forms.TextInput(attrs=widget_attrs),
                        **field_kwarg,
                    )

                elif s_val['type'] == 'BOOLEAN':
                    self.fields[s_field] = forms.BooleanField(**field_kwarg)

                # Set initial value
                self.initial[s_field] = app_settings.get_app_setting(
                    app_name=plugin.name, setting_name=s_key, user=self.user
                )

    def clean(self):
        """Function for custom form validation and cleanup"""

        for plugin in self.app_plugins:
            p_settings = app_settings.get_setting_defs(
                plugin, APP_SETTING_SCOPE_USER, user_modifiable=True
            )

            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(plugin.name, s_key)

                if not app_settings.validate_setting(
                    setting_type=s_val['type'],
                    setting_value=self.cleaned_data.get(s_field),
                ):
                    self.add_error(s_field, 'Invalid value')

        return self.cleaned_data
