"""Timeline API for adding and updating events"""
import re

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import Truncator

# Projectroles dependency
from projectroles.models import Project, RemoteSite
from projectroles.plugins import ProjectAppPluginPoint
from projectroles.templatetags.projectroles_common_tags import get_user_html
from projectroles.utils import get_app_names

from timeline.models import (
    ProjectEvent,
    ProjectEventObjectRef,
    EVENT_STATUS_TYPES,
)


# Local variables
APP_NAMES = get_app_names()
LABEL_MAX_WIDTH = 32

# Access Django user model
User = get_user_model()


class TimelineAPI:
    """Timeline backend API to be used by Django apps."""

    # Helpers ------------------------------------------------------------------

    @staticmethod
    def _get_label(label):
        """Format label to be displayed"""
        if not {' ', '-'}.intersection(label):
            return Truncator(label).chars(LABEL_MAX_WIDTH)
        return label

    @staticmethod
    def _get_not_found_label(ref_obj, history_link):
        """Get label for object which is not found in db"""
        return '<span class="text-danger">{}</span> {}'.format(
            TimelineAPI._get_label(ref_obj.name), history_link
        )

    @staticmethod
    def _get_project_desc(ref_obj, request=None):
        """Get description HTML for special case: Project model"""
        project = Project.objects.filter(sodar_uuid=ref_obj.object_uuid).first()

        if (
            project
            and request
            and request.user.has_perm('projectroles.view_project', project)
        ):
            return '<a href="{}">{}</a>'.format(
                reverse(
                    'projetroles:detail', kwargs={'project': project.sodar_uuid}
                ),
                TimelineAPI._get_label(project.title),
            )

        elif project:
            return '<span class="text-danger">{}</span>'.format(
                TimelineAPI._get_label(project.title)
            )

        return ref_obj.name

    @staticmethod
    def _get_remote_site_desc(ref_obj, history_link, request=None):
        """Get description HTML for special case: RemoteSite model"""
        site = RemoteSite.objects.filter(sodar_uuid=ref_obj.object_uuid).first()

        if site and request and request.user.is_superuser:
            return '<a href="{}">{}</a> {}'.format(
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': site.sodar_uuid},
                ),
                site.name,
                history_link,
            )

        elif site:
            return site.name

        return TimelineAPI._get_not_found_label(ref_obj, history_link)

    # API functions ------------------------------------------------------------

    @staticmethod
    def add_event(
        project,
        app_name,
        user,
        event_name,
        description,
        classified=False,
        extra_data=None,
        status_type=None,
        status_desc=None,
        status_extra_data=None,
    ):
        """
        Create and save a timeline event.

        :param project: Project object
        :param app_name: ID string of app from which event was invoked (NOTE:
            should correspond to member "name" in app plugin!)
        :param user: User invoking the event
        :param event_name: Event ID string (must match schema)
        :param description: Description of status change (may include {object
            label} references)
        :param classified: Whether event is classified (boolean, optional)
        :param extra_data: Additional event data (dict, optional)
        :param status_type: Initial status type (string, optional)
        :param status_desc: Initial status description (string, optional)
        :param status_extra_data: Extra data for initial status (dict, optional)
        :return: ProjectEvent object
        :raise: ValueError if app_name or status_type is invalid
        """
        if app_name not in APP_NAMES:
            raise ValueError(
                'Unknown app name "{}" (active apps: {})'.format(
                    app_name, ', '.join(x for x in APP_NAMES)
                )
            )

        if status_type and status_type not in EVENT_STATUS_TYPES:
            raise ValueError(
                'Unknown status type "{}" (valid types: {})'.format(
                    status_type, ', '.join(x for x in EVENT_STATUS_TYPES)
                )
            )

        event = ProjectEvent()
        event.project = project
        event.app = app_name
        event.user = user
        event.event_name = event_name
        event.description = description
        event.classified = classified

        if extra_data:
            event.extra_data = extra_data

        event.save()

        # Always add "INIT" status when creating, except for "INFO"
        if status_type != 'INFO':
            event.set_status('INIT')

        # Add additional status if set (use if e.g. event is immediately "OK")
        if status_type:
            event.set_status(status_type, status_desc, status_extra_data)

        return event

    @staticmethod
    def get_project_events(project, classified=False):
        """
        Return timeline events for a project.

        :param project: Project object
        :param classified: Include classified (boolean)
        :return: QuerySet
        """
        events = ProjectEvent.objects.filter(project=project)

        if not classified:
            events = events.filter(classified=False)

        return events

    @staticmethod
    def get_event_description(event, request=None):
        """
        Return the description of a timeline event as HTML.

        :param event: ProjectEvent object
        :param request: Request object (optional)
        :return: String (contains HTML)
        """
        desc = event.description
        unknown_label = '(unknown)'
        refs = {}
        ref_ids = re.findall("{'?(.*?)'?}", desc)

        if len(ref_ids) == 0:
            return event.description

        for r in ref_ids:
            # Get reference object or return an unknown label if not found
            if r.startswith('extra-'):
                app_plugin = ProjectAppPluginPoint.get_plugin(name=event.app)
                refs[r] = app_plugin.get_extra_data_link(event.extra_data, r)
                continue

            try:
                ref_obj = ProjectEventObjectRef.objects.get(
                    event=event, label=r
                )

            except ProjectEventObjectRef.DoesNotExist:
                refs[r] = unknown_label
                continue

            # Get history link
            history_url = reverse(
                'timeline:list_object',
                kwargs={
                    'project': event.project.sodar_uuid,
                    'object_model': ref_obj.object_model,
                    'object_uuid': ref_obj.object_uuid,
                },
            )
            history_link = (
                '<a href="{}" class="sodar-tl-object-link">'
                '<i class="fa fa-clock-o"></i></a>'.format(history_url)
            )

            # Special case: User model
            if ref_obj.object_model == 'User':
                try:
                    user = User.objects.get(sodar_uuid=ref_obj.object_uuid)
                    refs[r] = '{} {}'.format(get_user_html(user), history_link)

                except User.DoesNotExist:
                    refs[r] = unknown_label

            # Special case: Project model
            elif ref_obj.object_model == 'Project':
                refs[r] = TimelineAPI._get_project_desc(ref_obj, request)

            # Special case: RemoteSite model
            elif ref_obj.object_model == 'RemoteSite':
                refs[r] = TimelineAPI._get_remote_site_desc(
                    ref_obj, history_link, request
                )

            # Special case: projectroles app
            elif event.app == 'projectroles':
                refs[r] = TimelineAPI._get_not_found_label(
                    ref_obj, history_link
                )

            # Apps with plugins
            else:
                app_plugin = ProjectAppPluginPoint.get_plugin(name=event.app)

                try:
                    link_data = app_plugin.get_object_link(
                        ref_obj.object_model, ref_obj.object_uuid
                    )

                except Exception:
                    link_data = None

                if link_data:
                    refs[r] = '<a href="{}" {}>{}</a> {}'.format(
                        link_data['url'],
                        (
                            'target="_blank"'
                            if 'blank' in link_data
                            and link_data['blank'] is True
                            else ''
                        ),
                        TimelineAPI._get_label(link_data['label']),
                        history_link,
                    )

                else:
                    refs[r] = TimelineAPI._get_not_found_label(
                        ref_obj, history_link
                    )

        return event.description.format(**refs)

    @staticmethod
    def get_object_url(project_uuid, obj):
        """
        Return the URL for a timeline event object history.

        :param project_uuid: UUID of the related project
        :param obj: Django database object
        :return: String
        """
        return reverse(
            'timeline:list_object',
            kwargs={
                'project': project_uuid,
                'object_model': obj.__class__.__name__,
                'object_uuid': obj.sodar_uuid,
            },
        )

    @staticmethod
    def get_object_link(project_uuid, obj):
        """
        Return an inline HTML icon link for a timeline event object history.

        :param project_uuid: UUID of the related project
        :param obj: Django database object
        :return: String (contains HTML)
        """
        return (
            '<a href="{}" class="sodar-tl-object-link">'
            '<i class="fa fa-clock-o"></i>'
            '</a>'.format(TimelineAPI.get_object_url(project_uuid, obj))
        )

    @staticmethod
    def get_models():
        """
        Return project event model classes for custom/advanced queries.

        :return: ProjectEvent, ProjectEventObjectRef
        """
        return ProjectEvent, ProjectEventObjectRef
