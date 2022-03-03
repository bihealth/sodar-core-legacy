"""UI views for the userprofile app"""

from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins
from projectroles.views import (
    LoggedInPermissionMixin,
    HTTPRefererMixin,
)

from userprofile.forms import UserSettingsForm


User = auth.get_user_model()
app_settings = AppSettingAPI()


# SODAR Constants
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local Constants
SETTING_UPDATE_MSG = 'User settings updated.'


class UserDetailView(LoginRequiredMixin, LoggedInPermissionMixin, TemplateView):
    """Display the user profile view including the user settings"""

    template_name = 'userprofile/detail.html'
    permission_required = 'userprofile.view_detail'

    def _get_user_settings(self):
        plugins = get_active_plugins(
            plugin_type='project_app'
        ) + get_active_plugins(plugin_type='site_app')
        for plugin in plugins + [None]:
            if plugin:
                name = plugin.name
                p_settings = app_settings.get_setting_defs(
                    APP_SETTING_SCOPE_USER, plugin=plugin, user_modifiable=True
                )
            else:
                name = 'projectroles'
                p_settings = app_settings.get_setting_defs(
                    APP_SETTING_SCOPE_USER, app_name=name, user_modifiable=True
                )
            for s_key, s_val in p_settings.items():
                yield {
                    'label': s_val.get('label') or '{}.{}'.format(name, s_key),
                    'value': app_settings.get_app_setting(
                        name, s_key, user=self.request.user
                    ),
                    'description': s_val.get('description'),
                }

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['user_settings'] = list(self._get_user_settings())
        result['local_user'] = self.request.user.is_local()
        return result


class UserSettingUpdateView(
    LoginRequiredMixin, LoggedInPermissionMixin, HTTPRefererMixin, FormView
):
    """User settings update view"""

    form_class = UserSettingsForm
    permission_required = 'userprofile.view_detail'
    template_name = 'userprofile/settings_form.html'
    success_url = reverse_lazy('userprofile:detail')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        result = super().form_valid(form)
        for key, value in form.cleaned_data.items():
            if key.startswith('settings.'):
                _, app_name, setting_name = key.split('.', 3)
                app_settings.set_app_setting(
                    app_name, setting_name, value, user=self.request.user
                )
        messages.success(self.request, SETTING_UPDATE_MSG)
        return result
