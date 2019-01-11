from django.conf.urls import url

from . import views


app_name = 'timeline'

urlpatterns = [
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ProjectTimelineView.as_view(),
        name='list_project',
    ),
    url(
        regex=r'^(?P<project>[0-9a-f-]+)/(?P<object_model>[\w-]+)/'
              r'(?P<object_uuid>[0-9a-f-]+)$',
        view=views.ObjectTimelineView.as_view(),
        name='list_object',
    ),
    # Taskflow API views
    url(
        regex=r'^taskflow/status/set$',
        view=views.TaskflowEventStatusSetAPIView.as_view(),
        name='taskflow_status_set',
    ),
]
