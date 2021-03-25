"""Context processors for the projectroles app"""

from projectroles.plugins import get_active_plugins
from projectroles.urls import urlpatterns


def urls_processor(request):
    """Context processor for providing projectroles URLs for the sidebar"""
    return {
        'projectroles_urls': urlpatterns,
        'role_urls': [
            'roles',
            'role_create',
            'role_update',
            'role_delete',
            'invites',
            'invite_create',
            'invite_resend',
            'invite_revoke',
        ],
    }


def site_app_processor(request):
    """
    Context processor for providing site apps for the site titlebar dropdown.
    """
    site_apps = get_active_plugins('site_app')
    return {
        'site_apps': [
            a
            for a in site_apps
            if not a.app_permission or request.user.has_perm(a.app_permission)
        ],
    }
