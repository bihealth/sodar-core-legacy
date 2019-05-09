from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView

# Projectroles dependency
from projectroles.plugins import ProjectAppPluginPoint
from projectroles.user_settings import get_user_setting, set_user_setting
from projectroles.views import LoggedInPermissionMixin, HTTPRefererMixin

from .forms import UserSettingsForm

#: The user model to use
User = auth.get_user_model()


class UserDetailView(LoginRequiredMixin, LoggedInPermissionMixin, TemplateView):
    """Display the user profile view including the user settings"""

    template_name = 'userprofile/detail.html'
    permission_required = 'userprofile.view_detail'

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['user_settings'] = list(self._get_user_settings())
        return result

    def _get_user_settings(self):
        app_plugins = sorted(
            [p for p in ProjectAppPluginPoint.get_plugins() if p.user_settings],
            key=lambda x: x.name,
        )

        for p in app_plugins:
            for s_key in sorted(p.user_settings):
                s_value = p.user_settings[s_key]
                s = p.user_settings[s_key]

                yield {
                    'label': s_value.get('label')
                    or '{}.{}'.format(p.name, s_key),
                    'value': get_user_setting(self.request.user, p.name, s_key),
                    'description': s.get('description'),
                }


class UserSettingUpdateView(
    LoginRequiredMixin, LoggedInPermissionMixin, HTTPRefererMixin, FormView
):
    """Display and process the settings update view"""

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
                set_user_setting(
                    self.request.user, app_name, setting_name, value
                )
        return result
