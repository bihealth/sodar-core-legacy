from django.conf.urls import url

import adminalerts.views_ajax
from . import views

app_name = 'adminalerts'

urls_ui = [
    url(regex=r'^list$', view=views.AdminAlertListView.as_view(), name='list'),
    url(
        regex=r'^detail/(?P<adminalert>[0-9a-f-]+)$',
        view=views.AdminAlertDetailView.as_view(),
        name='detail',
    ),
    url(
        regex=r'^create$',
        view=views.AdminAlertCreateView.as_view(),
        name='create',
    ),
    url(
        regex=r'^update/(?P<adminalert>[0-9a-f-]+)$',
        view=views.AdminAlertUpdateView.as_view(),
        name='update',
    ),
    url(
        regex=r'^delete/(?P<adminalert>[0-9a-f-]+)/delete',
        view=views.AdminAlertDeleteView.as_view(),
        name='delete',
    ),
]

urls_ajax = [
    url(
        regex=r'^ajax/active/toggle/(?P<adminalert>[0-9a-f-]+)',
        view=adminalerts.views_ajax.AdminAlertActiveToggleAjaxView.as_view(),
        name='ajax_active_toggle',
    ),
]

urlpatterns = urls_ui + urls_ajax
