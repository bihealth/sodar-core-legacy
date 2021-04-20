"""Context processors for the projectroles app"""

from projectroles.plugins import get_active_plugins, get_backend_api
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


def app_alerts_processor(request):
    """
    Context processor for checking app alert status.
    """
    if request.user and request.user.is_authenticated:
        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            return {
                'app_alerts': app_alerts.get_model()
                .objects.filter(user=request.user, active=True)
                .count()
            }
    return {'app_alerts': 0}
