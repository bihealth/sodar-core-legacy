from django.conf.urls import url

from appalerts import views, views_ajax

app_name = 'appalerts'

urlpatterns = [
    url(
        regex=r'^list$',
        view=views.AppAlertListView.as_view(),
        name='list',
    ),
    url(
        regex=r'^redirect/(?P<appalert>[0-9a-f-]+)$',
        view=views.AppAlertLinkRedirectView.as_view(),
        name='redirect',
    ),
    url(
        regex=r'^ajax/status$',
        view=views_ajax.AppAlertStatusAjaxView.as_view(),
        name='ajax_status',
    ),
    url(
        regex=r'^ajax/dismiss/(?P<appalert>[0-9a-f-]+)$',
        view=views_ajax.AppAlertDismissAjaxView.as_view(),
        name='ajax_dismiss',
    ),
    url(
        regex=r'^ajax/dismiss/all$',
        view=views_ajax.AppAlertDismissAjaxView.as_view(),
        name='ajax_dismiss_all',
    ),
]
