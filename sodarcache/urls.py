from django.conf.urls import url

from . import views


app_name = 'sodarcache'

urlpatterns = [
    url(
        regex=r'^api/set/(?P<project>[0-9a-f-]+)$',
        view=views.SodarCacheSetAPIView.as_view(),
        name='cache_set',
    ),
    url(
        regex=r'^api/get/(?P<project>[0-9a-f-]+)$',
        view=views.SodarCacheGetAPIView.as_view(),
        name='cache_get',
    ),
    url(
        regex=r'^api/get/date/(?P<project>[0-9a-f-]+)$',
        view=views.SodarCacheGetDateAPIView.as_view(),
        name='cache_get_date',
    ),
]
