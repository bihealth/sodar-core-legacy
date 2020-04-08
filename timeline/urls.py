from django.conf.urls import url

from timeline import views, views_taskflow


app_name = 'timeline'

# UI views
urls_ui = [
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
]

# Taskflow API views
urls_taskflow = [
    url(
        regex=r'^taskflow/status/set$',
        view=views_taskflow.TaskflowEventStatusSetAPIView.as_view(),
        name='taskflow_status_set',
    )
]

urlpatterns = urls_ui + urls_taskflow
