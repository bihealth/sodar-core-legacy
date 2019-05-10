from django.conf.urls import url

from . import views

app_name = 'userprofile'

urlpatterns = [
    url(regex=r'^profile$', view=views.UserDetailView.as_view(), name='detail'),
    url(
        regex=r'^profile/settings/update$',
        view=views.UserSettingUpdateView.as_view(),
        name='settings_update',
    ),
]
