import logging

from django.conf import settings
from django.contrib import auth
from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.models import Project, RemoteSite, SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins
from projectroles.views import LoggedInPermissionMixin


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']


# Access Django user model
User = auth.get_user_model()


logger = logging.getLogger(__name__)


class SiteInfoView(LoggedInPermissionMixin, TemplateView):
    """Site info view"""

    permission_required = 'siteinfo.view_info'
    template_name = 'siteinfo/site_info.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Project statistics
        context['project_count'] = Project.objects.filter(
            type=PROJECT_TYPE_PROJECT
        ).count()
        context['category_count'] = Project.objects.filter(
            type=PROJECT_TYPE_CATEGORY
        ).count()

        # User statistics
        context['user_total_count'] = User.objects.all().count()
        context['user_ldap_count'] = User.objects.exclude(
            groups__name__in=['', SYSTEM_USER_GROUP]
        ).count()
        context['user_local_count'] = User.objects.filter(
            groups__name__in=['', SYSTEM_USER_GROUP]
        ).count()
        context['user_admin_count'] = User.objects.filter(
            is_superuser=True
        ).count()

        # App plugins
        project_plugins = get_active_plugins('project_app')
        backend_plugins = get_active_plugins('backend')
        context['site_plugins'] = get_active_plugins('site_app')

        # Plugin statistics
        def _get_plugin_stats(p_list):
            p_stats = {}
            for p in p_list:
                try:
                    p_stats[p] = {'stats': p.get_statistics()}
                except Exception as ex:
                    p_stats[p] = {'error': str(ex)}
                    logger.error(
                        'Exception in {}.get_statistics(): {}'.format(
                            p.name, ex
                        )
                    )
            return p_stats

        context['project_plugins'] = _get_plugin_stats(project_plugins)
        context['backend_plugins'] = _get_plugin_stats(backend_plugins)

        # Basic site info
        context['site_title'] = settings.SITE_TITLE
        context['site_subtitle'] = settings.SITE_SUBTITLE
        context['site_instance_title'] = settings.SITE_INSTANCE_TITLE

        # Remote site info
        context['site_mode'] = settings.PROJECTROLES_SITE_MODE

        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            context['site_target_count'] = RemoteSite.objects.filter(
                mode=SITE_MODE_TARGET
            ).count()

        return context
