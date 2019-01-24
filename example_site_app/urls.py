from django.conf.urls import url

from . import views

app_name = 'example_site_app'

urlpatterns = [
    url(regex=r'^example$', view=views.ExampleView.as_view(), name='example')
]
