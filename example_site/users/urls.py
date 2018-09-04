from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^(?P<username>[\w.@+-]+)$',
        view=views.UserDetailView.as_view(),
        name='user_detail'
    ),
]
