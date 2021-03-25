"""Ajax API views for the projectroles app"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse

from dal import autocomplete
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rules.contrib.views import PermissionRequiredMixin

from projectroles.models import (
    Project,
    PROJECT_TAG_STARRED,
    SODAR_CONSTANTS,
)
from projectroles.plugins import get_backend_api
from projectroles.project_tags import get_tag_state, set_tag_state
from projectroles.views import (
    ProjectAccessMixin,
    APP_NAME,
    User,
)
from projectroles.views_api import SODARAPIProjectPermission


# Base Classes and Mixins ------------------------------------------------------


class SODARBaseAjaxView(APIView):
    """
    Base Ajax view with Django session authentication.

    No permission classes or mixins used, you will have to supply your own if
    using this class directly.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]


class SODARBasePermissionAjaxView(PermissionRequiredMixin, SODARBaseAjaxView):
    """
    Base Ajax view with permission checks, to be used e.g. in site apps with no
    project context.

    User-based perms such as is_superuser can be used with this class.
    """

    def handle_no_permission(self):
        """Override handle_no_permission() to provide 403"""
        return HttpResponseForbidden()


class SODARBaseProjectAjaxView(ProjectAccessMixin, SODARBaseAjaxView):
    """Base Ajax view with SODAR project permission checks"""

    permission_classes = [SODARAPIProjectPermission]


# Projectroles Ajax Views ------------------------------------------------------


class ProjectStarringAjaxView(SODARBaseProjectAjaxView):
    """View to handle starring and unstarring a project"""

    permission_required = 'projectroles.view_project'

    def post(self, request, *args, **kwargs):
        # HACK: Manually refuse access to anonymous as this view is an exception
        if request.user.is_anonymous:
            return Response({'detail': 'Anonymous access denied'}, status=401)

        project = self.get_project()
        user = request.user
        timeline = get_backend_api('timeline_backend')

        tag_state = get_tag_state(project, user)
        action_str = '{}star'.format('un' if tag_state else '')

        set_tag_state(project, user, PROJECT_TAG_STARRED)

        # Add event in Timeline
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=user,
                event_name='project_{}'.format(action_str),
                description='{} project'.format(action_str),
                classified=True,
                status_type='INFO',
            )

        return Response(0 if tag_state else 1, status=200)


class UserAutocompleteAjaxView(autocomplete.Select2QuerySetView):
    """User autocompletion widget view"""

    def get_queryset(self):
        """
        Get a User queryset for SODARUserAutocompleteWidget.

        Optional values in self.forwarded:
        - "project": project UUID
        - "scope": string for expected scope (all/project/project_exclude)
        - "exclude": list of explicit User.sodar_uuid to exclude from queryset

        """
        current_user = self.request.user
        project_uuid = self.forwarded.get('project', None)
        exclude_uuids = self.forwarded.get('exclude', None)
        scope = self.forwarded.get('scope', 'all')

        # If project UUID is given, only show users that are in the project
        if scope in ['project', 'project_exclude'] and project_uuid not in [
            '',
            None,
        ]:
            project = Project.objects.filter(sodar_uuid=project_uuid).first()

            # If user has no permission for the project, return None
            if not self.request.user.has_perm(
                'projectroles.view_project', project
            ):
                return User.objects.none()

            project_users = [a.user.pk for a in project.get_all_roles()]

            if scope == 'project':  # Limit choices to current project users
                qs = User.objects.filter(pk__in=project_users)

            elif scope == 'project_exclude':  # Exclude project users
                qs = User.objects.exclude(pk__in=project_users)

        # Else include all users
        else:
            qs = User.objects.all()

        # Exclude users in the system group unless local users are allowed
        allow_local = getattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS', False)

        if not allow_local and not current_user.is_superuser:
            qs = qs.exclude(
                groups__name=SODAR_CONSTANTS['SYSTEM_USER_GROUP']
            ).exclude(groups__isnull=True)

        # Exclude UUIDs explicitly given
        if exclude_uuids:
            qs = qs.exclude(sodar_uuid__in=exclude_uuids)

        # Finally, filter by query
        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q)
                | Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
                | Q(name__icontains=self.q)
                | Q(email__icontains=self.q)
            )

        return qs.order_by('name')

    def get_result_label(self, user):
        """Display options with name, username and email address"""
        display = '{}{}{}'.format(
            user.name if user.name else '',
            ' ({})'.format(user.username) if user.name else user.username,
            ' <{}>'.format(user.email) if user.email else '',
        )
        return display

    def get_result_value(self, user):
        """Use sodar_uuid in the User model instead of pk"""
        return str(user.sodar_uuid)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        return super().get(request, *args, **kwargs)


class UserAutocompleteRedirectAjaxView(UserAutocompleteAjaxView):
    """
    SODARUserRedirectWidget view (user autocompletion) redirecting to
    the create invite page.
    """

    def get_create_option(self, context, q):
        """Form the correct email invite option to append to results"""
        create_option = []
        validator = EmailValidator()
        display_create_option = False

        if self.create_field and q:
            page_obj = context.get('page_obj', None)

            if page_obj is None or page_obj.number == 1:

                # Only create invite if the email address is valid
                try:
                    validator(q)
                    display_create_option = True

                except ValidationError:
                    display_create_option = False

                # Prevent sending a duplicate invite
                existing_options = (
                    self.get_result_label(result).lower()
                    for result in context['object_list']
                )

                if q.lower() in existing_options:
                    display_create_option = False

        if display_create_option:
            create_option = [
                {
                    'id': q,
                    'text': ('Send an invite to "%(new_value)s"')
                    % {'new_value': q},
                    'create_id': True,
                }
            ]
        return create_option

    def post(self, request):
        """Send the invite form url to which the forwarded values will be
        send"""
        project_uuid = self.request.POST.get('project', None)
        project = Project.objects.filter(sodar_uuid=project_uuid).first()
        # create JSON with address to redirect to
        redirect_url = reverse(
            'projectroles:invite_create', kwargs={'project': project.sodar_uuid}
        )
        return JsonResponse({'success': True, 'redirect_url': redirect_url})
