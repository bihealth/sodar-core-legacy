from django.conf.urls import url

from . import views, views_api

# NOTE: file/folder/hyperlink objects can be referred to as 'item', but only if
#       ObjectPermissionMixin is used in the view


app_name = 'filesfolders'

urls_ui = [
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ProjectFileView.as_view(),
        name='list',
    ),
    url(
        regex=r'^folder/(?P<folder>[0-9a-f-]+)$',
        view=views.ProjectFileView.as_view(),
        name='list',
    ),
    url(
        regex=r'^upload/(?P<project>[0-9a-f-]+)$',
        view=views.FileCreateView.as_view(),
        name='file_create',
    ),
    url(
        regex=r'^upload/in/(?P<folder>[0-9a-f-]+)$',
        view=views.FileCreateView.as_view(),
        name='file_create',
    ),
    url(
        regex=r'^update/(?P<item>[0-9a-f-]+)$',
        view=views.FileUpdateView.as_view(),
        name='file_update',
    ),
    url(
        regex=r'^delete/(?P<item>[0-9a-f-]+)$',
        view=views.FileDeleteView.as_view(),
        name='file_delete',
    ),
    url(
        regex=r'^download/(?P<file>[0-9a-f-]+)/(?P<file_name>[^\0/]+)$',
        view=views.FileServeView.as_view(),
        name='file_serve',
    ),
    url(
        regex=r'^download/(?P<secret>[\w\-]+)/(?P<file_name>[^\0/]+)$',
        view=views.FileServePublicView.as_view(),
        name='file_serve_public',
    ),
    url(
        regex=r'^link/(?P<file>[0-9a-f-]+)$',
        view=views.FilePublicLinkView.as_view(),
        name='file_public_link',
    ),
    url(
        regex=r'^folder/add/(?P<project>[0-9a-f-]+)$',
        view=views.FolderCreateView.as_view(),
        name='folder_create',
    ),
    url(
        regex=r'^folder/add/in/(?P<folder>[0-9a-f-]+)$',
        view=views.FolderCreateView.as_view(),
        name='folder_create',
    ),
    url(
        regex=r'^folder/update/(?P<item>[0-9a-f-]+)$',
        view=views.FolderUpdateView.as_view(),
        name='folder_update',
    ),
    url(
        regex=r'^folder/delete(?P<item>[0-9a-f-]+)$',
        view=views.FolderDeleteView.as_view(),
        name='folder_delete',
    ),
    url(
        regex=r'^link/add/(?P<project>[0-9a-f-]+)$',
        view=views.HyperLinkCreateView.as_view(),
        name='hyperlink_create',
    ),
    url(
        regex=r'^link/add/in/(?P<folder>[0-9a-f-]+)$',
        view=views.HyperLinkCreateView.as_view(),
        name='hyperlink_create',
    ),
    url(
        regex=r'^link/update/(?P<item>[0-9a-f-]+)$',
        view=views.HyperLinkUpdateView.as_view(),
        name='hyperlink_update',
    ),
    url(
        regex=r'^link/delete/(?P<item>[0-9a-f-]+)$',
        view=views.HyperLinkDeleteView.as_view(),
        name='hyperlink_delete',
    ),
    url(
        regex=r'^batch/(?P<project>[0-9a-f-]+)$',
        view=views.BatchEditView.as_view(),
        name='batch_edit',
    ),
    url(
        regex=r'^batch/in/(?P<folder>[0-9a-f-]+)$',
        view=views.BatchEditView.as_view(),
        name='batch_edit',
    ),
]

urls_api = [
    url(
        regex=r'^api/folder/list-create/(?P<project>[0-9a-f-]+)$',
        view=views_api.FolderListCreateAPIView.as_view(),
        name='api_folder_list_create',
    ),
    url(
        regex=r'^api/folder/retrieve-update-destroy/(?P<folder>[0-9a-f-]+)$',
        view=views_api.FolderRetrieveUpdateDestroyAPIView.as_view(),
        name='api_folder_retrieve_update_destroy',
    ),
    url(
        regex=r'^api/file/list-create/(?P<project>[0-9a-f-]+)$',
        view=views_api.FileListCreateAPIView.as_view(),
        name='api_file_list_create',
    ),
    url(
        regex=r'^api/file/retrieve-update-destroy/(?P<file>[0-9a-f-]+)$',
        view=views_api.FileRetrieveUpdateDestroyAPIView.as_view(),
        name='api_file_retrieve_update_destroy',
    ),
    url(
        regex=r'^api/file/serve/(?P<file>[0-9a-f-]+)$',
        view=views_api.FileServeAPIView.as_view(),
        name='api_file_serve',
    ),
    url(
        regex=r'^api/hyperlink/list-create/(?P<project>[0-9a-f-]+)$',
        view=views_api.HyperLinkListCreateAPIView.as_view(),
        name='api_hyperlink_list_create',
    ),
    url(
        regex=r'^api/hyperlink/retrieve-update-destroy/(?P<hyperlink>[0-9a-f-]+)$',
        view=views_api.HyperLinkRetrieveUpdateDestroyAPIView.as_view(),
        name='api_hyperlink_retrieve_update_destroy',
    ),
]

urlpatterns = urls_ui + urls_api
