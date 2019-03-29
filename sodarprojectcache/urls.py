from django.conf.urls import url

from . import views


app_name = 'sodarprojectcache'

urlpatterns = [
    url(
        regex=r'^set/(?P<project>[0-9a-f-]+)$',
        view=views.SodarProjectCacheSetAPIView.as_view(),
        name='projectcache_set',
    ),
    url(
        regex=r'^get/(?P<project>[0-9a-f-]+)$',
        view=views.SodarProjectCacheGetAPIView.as_view(),
        name='projectcache_get',
    ),
    url(
        regex=r'^get/date/(?P<project>[0-9a-f-]+)$',
        view=views.SodarProjectCacheGetDateAPIView.as_view(),
        name='projectcache_get_date',
    ),
    url(
        regex=r'^taskflow/update$',
        view=views.TaskflowCacheUpdateAPIView.as_view(),
        name='taskflow_update',
    ),
]
