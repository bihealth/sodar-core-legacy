from django.conf.urls import url
from tokens import views

app_name = 'tokens'

urlpatterns = [
    url(regex=r'^$', view=views.UserTokenListView.as_view(), name='list'),
    url(
        regex=r'^create/',
        view=views.UserTokenCreateView.as_view(),
        name='create',
    ),
    url(
        regex=r'^delete/(?P<pk>.+)$',
        view=views.UserTokenDeleteView.as_view(),
        name='delete',
    ),
]
