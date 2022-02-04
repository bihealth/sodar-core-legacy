from django.conf.urls import url

from projectroles import views, views_ajax, views_api, views_taskflow

app_name = 'projectroles'

# UI views
urls_ui = [
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ProjectDetailView.as_view(),
        name='detail',
    ),
    url(
        regex=r'^update/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectUpdateView.as_view(),
        name='update',
    ),
    url(
        regex=r'^create$', view=views.ProjectCreateView.as_view(), name='create'
    ),
    url(
        regex=r'^create/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectCreateView.as_view(),
        name='create',
    ),
    # Search views
    url(
        regex=r'^search/results/$',
        view=views.ProjectSearchResultsView.as_view(),
        name='search',
    ),
    url(
        regex=r'^search/advanced$',
        view=views.ProjectAdvancedSearchView.as_view(),
        name='search_advanced',
    ),
    # Project role views
    url(
        regex=r'^members/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectRoleView.as_view(),
        name='roles',
    ),
    url(
        regex=r'^members/create/(?P<project>[0-9a-f-]+)$',
        view=views.RoleAssignmentCreateView.as_view(),
        name='role_create',
    ),
    url(
        regex=r'^members/update/(?P<roleassignment>[0-9a-f-]+)$',
        view=views.RoleAssignmentUpdateView.as_view(),
        name='role_update',
    ),
    url(
        regex=r'^members/delete/(?P<roleassignment>[0-9a-f-]+)$',
        view=views.RoleAssignmentDeleteView.as_view(),
        name='role_delete',
    ),
    url(
        regex=r'^members/owner/transfer/(?P<project>[0-9a-f-]+)$',
        view=views.RoleAssignmentOwnerTransferView.as_view(),
        name='role_owner_transfer',
    ),
    # Project invite views
    url(
        regex=r'^invites/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectInviteView.as_view(),
        name='invites',
    ),
    url(
        regex=r'^invites/create/(?P<project>[0-9a-f-]+)',
        view=views.ProjectInviteCreateView.as_view(),
        name='invite_create',
    ),
    url(
        regex=r'^invites/accept/(?P<secret>[\w\-]+)$',
        view=views.ProjectInviteAcceptView.as_view(),
        name='invite_accept',
    ),
    url(
        regex=r'^invites/process/ldap/(?P<secret>[\w\-]+)$',
        view=views.ProjectInviteProcessLDAPView.as_view(),
        name='invite_process_ldap',
    ),
    url(
        regex=r'^invites/process/local/(?P<secret>[\w\-]+)$',
        view=views.ProjectInviteProcessLocalView.as_view(),
        name='invite_process_local',
    ),
    url(
        regex=r'^invites/resend/(?P<projectinvite>[0-9a-f-]+)$',
        view=views.ProjectInviteResendView.as_view(),
        name='invite_resend',
    ),
    url(
        regex=r'^invites/revoke/(?P<projectinvite>[0-9a-f-]+)$',
        view=views.ProjectInviteRevokeView.as_view(),
        name='invite_revoke',
    ),
    url(
        regex=r'^user/update$',
        view=views.UserUpdateView.as_view(),
        name='user_update',
    ),
    # Remote site and project views
    url(
        regex=r'^remote/sites$',
        view=views.RemoteSiteListView.as_view(),
        name='remote_sites',
    ),
    url(
        regex=r'^remote/site/add$',
        view=views.RemoteSiteCreateView.as_view(),
        name='remote_site_create',
    ),
    url(
        regex=r'^remote/site/update/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteSiteUpdateView.as_view(),
        name='remote_site_update',
    ),
    url(
        regex=r'^remote/site/delete/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteSiteDeleteView.as_view(),
        name='remote_site_delete',
    ),
    url(
        regex=r'^remote/site/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteProjectListView.as_view(),
        name='remote_projects',
    ),
    url(
        regex=r'^remote/site/access/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteProjectBatchUpdateView.as_view(),
        name='remote_projects_update',
    ),
    url(
        regex=r'^remote/site/sync/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteProjectSyncView.as_view(),
        name='remote_projects_sync',
    ),
]

# Ajax API views
urls_ajax = [
    url(
        regex=r'^ajax/list/columns',
        view=views_ajax.ProjectListColumnAjaxView.as_view(),
        name='ajax_project_list_columns',
    ),
    url(
        regex=r'^ajax/star/(?P<project>[0-9a-f-]+)',
        view=views_ajax.ProjectStarringAjaxView.as_view(),
        name='ajax_star',
    ),
    url(
        r'^ajax/autocomplete/user$',
        view=views_ajax.UserAutocompleteAjaxView.as_view(),
        name='ajax_autocomplete_user',
    ),
    url(
        r'^ajax/autocomplete/user/redirect$',
        view=views_ajax.UserAutocompleteRedirectAjaxView.as_view(
            create_field='user'
        ),
        name='ajax_autocomplete_user_redirect',
    ),
]

# REST API views
urls_api = [
    url(
        regex=r'^api/list$',
        view=views_api.ProjectListAPIView.as_view(),
        name='api_project_list',
    ),
    url(
        regex=r'^api/retrieve/(?P<project>[0-9a-f-]+)$',
        view=views_api.ProjectRetrieveAPIView.as_view(),
        name='api_project_retrieve',
    ),
    url(
        regex=r'^api/create$',
        view=views_api.ProjectCreateAPIView.as_view(),
        name='api_project_create',
    ),
    url(
        regex=r'^api/update/(?P<project>[0-9a-f-]+)$',
        view=views_api.ProjectUpdateAPIView.as_view(),
        name='api_project_update',
    ),
    url(
        regex=r'^api/roles/create/(?P<project>[0-9a-f-]+)$',
        view=views_api.RoleAssignmentCreateAPIView.as_view(),
        name='api_role_create',
    ),
    url(
        regex=r'^api/roles/update/(?P<roleassignment>[0-9a-f-]+)$',
        view=views_api.RoleAssignmentUpdateAPIView.as_view(),
        name='api_role_update',
    ),
    url(
        regex=r'^api/roles/destroy/(?P<roleassignment>[0-9a-f-]+)$',
        view=views_api.RoleAssignmentDestroyAPIView.as_view(),
        name='api_role_destroy',
    ),
    url(
        regex=r'^api/roles/owner-transfer/(?P<project>[0-9a-f-]+)$',
        view=views_api.RoleAssignmentOwnerTransferAPIView.as_view(),
        name='api_role_owner_transfer',
    ),
    url(
        regex=r'^api/invites/list/(?P<project>[0-9a-f-]+)$',
        view=views_api.ProjectInviteListAPIView.as_view(),
        name='api_invite_list',
    ),
    url(
        regex=r'^api/invites/create/(?P<project>[0-9a-f-]+)$',
        view=views_api.ProjectInviteCreateAPIView.as_view(),
        name='api_invite_create',
    ),
    url(
        regex=r'^api/invites/revoke/(?P<projectinvite>[0-9a-f-]+)$',
        view=views_api.ProjectInviteRevokeAPIView.as_view(),
        name='api_invite_revoke',
    ),
    url(
        regex=r'^api/invites/resend/(?P<projectinvite>[0-9a-f-]+)$',
        view=views_api.ProjectInviteResendAPIView.as_view(),
        name='api_invite_resend',
    ),
    url(
        regex=r'^api/users/list$',
        view=views_api.UserListAPIView.as_view(),
        name='api_user_list',
    ),
    url(
        regex=r'^api/users/current$',
        view=views_api.CurrentUserRetrieveAPIView.as_view(),
        name='api_user_current',
    ),
    url(
        regex=r'^api/remote/get/(?P<secret>[\w\-]+)$',
        view=views_api.RemoteProjectGetAPIView.as_view(),
        name='api_remote_get',
    ),
]

# Taskflow API views
urls_taskflow = [
    url(
        regex=r'^taskflow/get$',
        view=views_taskflow.TaskflowProjectGetAPIView.as_view(),
        name='taskflow_project_get',
    ),
    url(
        regex=r'^taskflow/update$',
        view=views_taskflow.TaskflowProjectUpdateAPIView.as_view(),
        name='taskflow_project_update',
    ),
    url(
        regex=r'^taskflow/role/get$',
        view=views_taskflow.TaskflowRoleAssignmentGetAPIView.as_view(),
        name='taskflow_role_get',
    ),
    url(
        regex=r'^taskflow/role/set$',
        view=views_taskflow.TaskflowRoleAssignmentSetAPIView.as_view(),
        name='taskflow_role_set',
    ),
    url(
        regex=r'^taskflow/role/delete$',
        view=views_taskflow.TaskflowRoleAssignmentDeleteAPIView.as_view(),
        name='taskflow_role_delete',
    ),
    url(
        regex=r'^taskflow/settings/get$',
        view=views_taskflow.TaskflowProjectSettingsGetAPIView.as_view(),
        name='taskflow_settings_get',
    ),
    url(
        regex=r'^taskflow/settings/set$',
        view=views_taskflow.TaskflowProjectSettingsSetAPIView.as_view(),
        name='taskflow_settings_set',
    ),
]

urlpatterns = urls_ui + urls_ajax + urls_api + urls_taskflow
