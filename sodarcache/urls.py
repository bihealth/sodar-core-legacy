from django.conf.urls import url

from . import views_api


app_name = 'sodarcache'

urlpatterns = [
    url(
        regex=r'^api/set/(?P<project>[0-9a-f-]+)$',
        view=views_api.SodarCacheSetAPIView.as_view(),
        name='cache_set',
    ),
    url(
        regex=r'^api/get/(?P<project>[0-9a-f-]+)$',
        view=views_api.SodarCacheGetAPIView.as_view(),
        name='cache_get',
    ),
    url(
        regex=r'^api/get/date/(?P<project>[0-9a-f-]+)$',
        view=views_api.SodarCacheGetDateAPIView.as_view(),
        name='cache_get_date',
    ),
]
