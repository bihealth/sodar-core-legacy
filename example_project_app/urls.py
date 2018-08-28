from django.conf.urls import url

from . import views

app_name = 'example_project_app'

# NOTE: Name of object in kwarg which is a Project or has "project" as a member
#       is expected to correspond 1:1 to the model in question (lowercase ok)!

urlpatterns = [
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ExampleView.as_view(),
        name='example',
    ),
]
