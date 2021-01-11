from django.conf.urls import url

from example_project_app import views, views_api

app_name = 'example_project_app'

# NOTE: Name of object in kwarg which is a Project or has "project" as a member
#       is expected to correspond 1:1 to the model in question (lowercase ok)!

urls = [
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ExampleView.as_view(),
        name='example',
    )
]

urls_api = [
    url(
        regex=r'^api/hello/(?P<project>[0-9a-f-]+)$',
        view=views_api.HelloExampleProjectAPIView.as_view(),
        name='example_api_hello',
    )
]

urlpatterns = urls + urls_api
