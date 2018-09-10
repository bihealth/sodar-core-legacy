from django.conf.urls import url

from . import views

app_name = 'user_profile'

urlpatterns = [
    url(
        regex=r'^$',
        view=views.UserDetailView.as_view(),
        name='detail'
    ),
]
