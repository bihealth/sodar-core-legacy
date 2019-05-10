from django import forms
from django.conf import settings
from django.contrib import auth
from django.utils import timezone

from pagedown.widgets import PagedownWidget
from dal import autocomplete

from .models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    SODAR_CONSTANTS,
    APP_SETTING_VAL_MAXLENGTH,
)

from .plugins import get_active_plugins
from .utils import get_display_name, get_user_display_name, build_secret
from .app_settings import AppSettingAPI


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CHOICES = [
    (
        PROJECT_TYPE_CATEGORY,
        get_display_name(PROJECT_TYPE_CATEGORY, title=True),
    ),
    (PROJECT_TYPE_PROJECT, get_display_name(PROJECT_TYPE_PROJECT, title=True)),
]
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']

# Local constants and settings
APP_NAME = 'projectroles'
INVITE_EXPIRY_DAYS = settings.PROJECTROLES_INVITE_EXPIRY_DAYS
DELEGATE_LIMIT = (
    settings.PROJECTROLES_DELEGATE_LIMIT
    if hasattr(settings, 'PROJECTROLES_DELEGATE_LIMIT')
    else 1
)

User = auth.get_user_model()


# General widgets --------------------------------------------------------------


class UserAutocompleteWidget(autocomplete.ModelSelect2):
    """Custom Select widget for user field autocompletion that uses the UUID
    instead of the pk."""

    # override function to use sodar_uuid instead of pk
    def filter_choices_to_render(self, selected_choices):
        """Filter out un-selected choices if choices is a QuerySet."""
        self.choices.queryset = self.choices.queryset.filter(
            sodar_uuid__in=[c for c in selected_choices if c]
        )


class RedirectWidget(UserAutocompleteWidget):
    """Custom Select widget for QuerySet choices and Select2."""

    autocomplete_function = 'autocomplete_redirect'


# Project form -----------------------------------------------------------------


class ProjectForm(forms.ModelForm):
    """Form for Project creation/updating"""

    owner = forms.ModelChoiceField(
        User.objects.all(),
        required=True,
        to_field_name='sodar_uuid',
        label='Owner',
        help_text='Owner',
        widget=UserAutocompleteWidget(
            url='projectroles:autocomplete_user_exclude', forward=['project']
        ),
    )

    # Hidden project field for user autocomplete
    project = forms.ModelChoiceField(
        Project.objects.all(),
        required=False,
        to_field_name='sodar_uuid',
        initial=None,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Project
        fields = ['title', 'type', 'parent', 'owner', 'description', 'readme']

    def __init__(self, project=None, current_user=None, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)

        # Add settings fields
        self.app_settings = AppSettingAPI()
        self.app_plugins = sorted(get_active_plugins(), key=lambda x: x.name)

        for plugin in self.app_plugins:
            p_settings = self.app_settings.get_setting_defs(
                plugin, APP_SETTING_SCOPE_PROJECT
            )

            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(plugin.name, s_key)
                setting_kwargs = {
                    'required': False,
                    'label': s_val.get('label')
                    or '{}.{}'.format(plugin.name, s_key),
                    'help_text': s_val['description'],
                }

                if s_val['type'] == 'STRING':
                    self.fields[s_field] = forms.CharField(
                        max_length=APP_SETTING_VAL_MAXLENGTH, **setting_kwargs
                    )

                elif s_val['type'] == 'INTEGER':
                    self.fields[s_field] = forms.IntegerField(**setting_kwargs)

                elif s_val['type'] == 'BOOLEAN':
                    self.fields[s_field] = forms.BooleanField(**setting_kwargs)

                # Set initial value
                if self.instance.pk:
                    self.initial[s_field] = self.app_settings.get_app_setting(
                        app_name=plugin.name,
                        setting_name=s_key,
                        project=self.instance,
                    )

                else:
                    self.initial[
                        s_field
                    ] = self.app_settings.get_default_setting(
                        app_name=plugin.name, setting_name=s_key
                    )

        # Access parent project if present
        parent_project = None

        if project:
            parent_project = Project.objects.filter(sodar_uuid=project).first()

        # Get current user for checking permissions for form items
        if current_user:
            self.current_user = current_user

        # Do not allow transfer under another parent
        self.fields['parent'].disabled = True

        # Update help texts to match DISPLAY_NAMES
        self.fields['title'].help_text = 'Title'
        self.fields['type'].help_text = 'Type of container ({} or {})'.format(
            get_display_name(PROJECT_TYPE_CATEGORY),
            get_display_name(PROJECT_TYPE_PROJECT),
        )
        self.fields['type'].choices = PROJECT_TYPE_CHOICES
        self.fields['parent'].help_text = 'Parent {} if nested'.format(
            get_display_name(PROJECT_TYPE_CATEGORY)
        )
        self.fields['description'].help_text = 'Short description'
        self.fields['readme'].help_text = 'README (optional, supports markdown)'

        ####################
        # Form modifications
        ####################

        # Modify ModelChoiceFields to use sodar_uuid
        self.fields['parent'].to_field_name = 'sodar_uuid'

        # Set readme widget with preview
        self.fields['readme'].widget = PagedownWidget(show_preview=True)

        # Hide parent selection
        self.fields['parent'].widget = forms.HiddenInput()

        # Updating an existing project
        if self.instance.pk:
            # Set readme value as raw markdown
            self.initial['readme'] = self.instance.readme.raw

            # Hide project type selection
            self.fields['type'].widget = forms.HiddenInput()

            # Set hidden project field for autocomplete
            self.initial['project'] = self.instance

            # Only owner/superuser has rights to modify owner
            if current_user.has_perm(
                'projectroles.update_project_owner', self.instance
            ):
                # Set current owner as initial value
                owner = self.instance.get_owner().user
                self.initial['owner'] = owner.sodar_uuid

            # Else hide owner selection
            else:
                self.fields['owner'].widget = forms.HiddenInput()

            # Set initial value for parent
            if parent_project:
                self.initial['parent'] = parent_project.sodar_uuid

            else:
                self.initial['parent'] = None

        # Project creation
        else:
            # Set hidden project field for autocomplete
            self.initial['project'] = None

            # Creating a subproject
            if parent_project:
                # Parent must be current parent
                self.initial['parent'] = parent_project.sodar_uuid

                # Set parent owner as initial value
                parent_owner = parent_project.get_owner().user
                self.initial['owner'] = parent_owner.sodar_uuid

            # Creating a top level project
            else:
                # Force project type
                if (
                    hasattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES')
                    and settings.PROJECTROLES_DISABLE_CATEGORIES
                ):
                    self.initial['type'] = PROJECT_TYPE_PROJECT

                else:
                    self.initial['type'] = PROJECT_TYPE_CATEGORY

                # Hide project type selection
                self.fields['type'].widget = forms.HiddenInput()

                # Set up parent field
                self.initial['parent'] = None

    def clean(self):
        """Function for custom form validation and cleanup"""

        # Ensure the title is unique within parent
        try:
            existing_project = Project.objects.get(
                parent=self.cleaned_data.get('parent'),
                title=self.cleaned_data.get('title'),
            )

            if not self.instance or existing_project.pk != self.instance.pk:
                self.add_error('title', 'Title must be unique within parent')

        except Project.DoesNotExist:
            pass

        # Ensure title is not equal to parent
        parent = self.cleaned_data.get('parent')

        if parent and parent.title == self.cleaned_data.get('title'):
            self.add_error(
                'title',
                '{} and parent titles can not be equal'.format(
                    get_display_name(self.cleaned_data.get('type'), title=True)
                ),
            )

        # Ensure owner has been set
        if not self.cleaned_data.get('owner'):
            self.add_error(
                'owner',
                'Owner must be set for {}'.format(
                    get_display_name(self.cleaned_data.get('type'))
                ),
            )

        # Verify settings fields
        for plugin in self.app_plugins:
            p_settings = self.app_settings.get_setting_defs(
                plugin, APP_SETTING_SCOPE_PROJECT
            )

            for s_key in p_settings:
                s = p_settings[s_key]
                s_field = 'settings.{}.{}'.format(plugin.name, s_key)

                if not self.app_settings.validate_setting(
                    setting_type=s['type'],
                    setting_value=self.cleaned_data.get(s_field),
                ):
                    self.add_error(s_field, 'Invalid value')

        return self.cleaned_data


# RoleAssignment form ----------------------------------------------------------


class RoleAssignmentForm(forms.ModelForm):
    """Form for editing Project role assignments"""

    class Meta:
        model = RoleAssignment
        fields = ['project', 'user', 'role']
        widgets = {
            'user': RedirectWidget(
                url='projectroles:autocomplete_user_redirect',
                forward=['project', 'role'],
            )
        }

    def __init__(self, project=None, current_user=None, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)

        # Get current user for checking permissions for form items
        if current_user:
            self.current_user = current_user

        # Get the project for which role is being assigned
        self.project = None

        if self.instance.pk:
            self.project = self.instance.project

        else:
            self.project = Project.objects.filter(sodar_uuid=project).first()

        ####################
        # Form modifications
        ####################

        # Modify ModelChoiceFields to use sodar_uuid
        self.fields['project'].to_field_name = 'sodar_uuid'
        self.fields['user'].to_field_name = 'sodar_uuid'

        # Limit role choices
        self.fields['role'].choices = get_role_choices(
            self.project, self.current_user
        )

        # Updating an existing assignment
        if self.instance.pk:
            # Set values
            self.initial['project'] = self.instance.project.sodar_uuid
            self.initial['user'] = self.instance.user.sodar_uuid

            # Hide project and user switching
            self.fields['project'].widget = forms.HiddenInput()
            self.fields['user'].widget = forms.HiddenInput()

            # Set initial role
            self.initial['role'] = self.instance.role

        # Creating a new assignment
        elif self.project:
            # Limit project choice to self.project, hide widget
            self.initial['project'] = self.project.sodar_uuid
            self.fields['project'].widget = forms.HiddenInput()

            self.fields['role'].initial = Role.objects.get(
                name=PROJECT_ROLE_GUEST
            ).pk

    def clean(self):
        """Function for custom form validation and cleanup"""
        role = self.cleaned_data.get('role')
        existing_as = RoleAssignment.objects.get_assignment(
            self.cleaned_data.get('user'), self.cleaned_data.get('project')
        )

        # Adding a new RoleAssignment
        if not self.instance.pk:
            # Make sure user doesn't already have role in project
            if existing_as:
                self.add_error(
                    'user',
                    'User {} already assigned as {}'.format(
                        existing_as.role.name,
                        get_user_display_name(self.cleaned_data.get('user')),
                    ),
                )

        # Updating a RoleAssignment
        else:
            # Ensure not setting existing role again
            if existing_as and existing_as.role == role:
                self.add_error('role', 'Role already assigned to user')

        # Delegate checks
        if role.name == PROJECT_ROLE_DELEGATE:
            # Ensure current user has permission to set delegate
            if not self.current_user.has_perm(
                'projectroles.update_project_delegate', obj=self.project
            ):
                self.add_error(
                    'role', 'Insufficient permissions for altering delegate'
                )

            # Ensure user can't attempt to add another delegate if limit is
            # reached
            delegates = self.project.get_delegates()

            if DELEGATE_LIMIT != 0:
                if len(delegates) >= DELEGATE_LIMIT:
                    self.add_error(
                        'role',
                        'The limit ({}) of delegates for this project has '
                        'already been reached.'.format(DELEGATE_LIMIT),
                    )

        return self.cleaned_data


# ProjectInvite form -----------------------------------------------------------


class ProjectInviteForm(forms.ModelForm):
    """Form for ProjectInvite modification"""

    class Meta:
        model = ProjectInvite
        fields = ['email', 'role', 'message']

    def __init__(
        self,
        project=None,
        current_user=None,
        mail=None,
        role=None,
        *args,
        **kwargs
    ):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)

        # Get current user for checking permissions and saving issuer
        if current_user:
            self.current_user = current_user

        # in case it has been redirected from the RoleAssignment form
        if mail:
            self.fields['email'].initial = mail

        # Get the project for which invite is being sent
        self.project = Project.objects.filter(sodar_uuid=project).first()

        # Limit Role choices according to user permissions
        self.fields['role'].choices = get_role_choices(
            self.project, self.current_user, allow_delegate=True
        )

        if role:
            self.fields['role'].initial = role
        else:
            self.fields['role'].initial = Role.objects.get(
                name=PROJECT_ROLE_GUEST
            ).pk

        # Limit textarea height
        self.fields['message'].widget.attrs['rows'] = 4

    def clean(self):
        # Check if user email is already in users
        try:
            existing_user = User.objects.get(
                email=self.cleaned_data.get('email')
            )
            self.add_error(
                'email',
                'User "{}" already exists in the system with this email. '
                'Please use "Add Role" instead.'.format(existing_user.username),
            )

        except User.DoesNotExist:
            pass

        # Check if user already has an invite in the project
        try:
            ProjectInvite.objects.get(
                project=self.project,
                email=self.cleaned_data.get('email'),
                active=True,
                date_expire__gt=timezone.now(),
            )

            self.add_error(
                'email',
                'There is already an active invite for email {} in {}'.format(
                    self.cleaned_data.get('email'), self.project.title
                ),
            )

        except ProjectInvite.DoesNotExist:
            pass

        # Delegate checks
        role = self.cleaned_data.get('role')
        if role.name == PROJECT_ROLE_DELEGATE:
            # Ensure current user has permission to invite delegate
            if not self.current_user.has_perm(
                'projectroles.update_project_delegate', obj=self.project
            ):
                self.add_error(
                    'role', 'Insufficient permissions for inviting delegate'
                )

            # Ensure user can't attempt to add another delegate if limit is
            # reached
            delegates = self.project.get_delegates()

            if DELEGATE_LIMIT != 0:
                if len(delegates) >= DELEGATE_LIMIT:
                    self.add_error(
                        'role',
                        'The limit ({}) of delegates for this project has '
                        'already been reached.'.format(DELEGATE_LIMIT),
                    )

        return self.cleaned_data

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)

        obj.project = self.project
        obj.issuer = self.current_user
        obj.date_expire = timezone.now() + timezone.timedelta(
            days=INVITE_EXPIRY_DAYS
        )
        obj.secret = build_secret()

        obj.save()
        return obj


# RemoteSite form --------------------------------------------------------------


class RemoteSiteForm(forms.ModelForm):
    """Form for RemoteSite creation/updating"""

    class Meta:
        model = RemoteSite
        fields = ['name', 'url', 'description', 'secret']

    def __init__(self, current_user=None, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)

        self.current_user = current_user

        # Default field modifications
        self.fields['description'].required = False
        self.fields['secret'].widget = forms.TextInput(
            attrs={'class': "sodar-code-input"}
        )
        self.fields['description'].widget.attrs['rows'] = 4

        # Special cases for SOURCE
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            self.fields['secret'].widget.attrs['readonly'] = True

        # Creation
        if not self.instance.pk:
            # Generate secret token for target site
            if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
                self.fields['secret'].initial = build_secret()

        # Updating
        else:
            pass

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)

        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            obj.mode = SITE_MODE_TARGET

        else:
            obj.mode = SITE_MODE_SOURCE

        obj.save()
        return obj


# Helper functions -------------------------------------------------------------


def get_role_choices(project, current_user, allow_delegate=True):
    """
    Return valid role choices according to permissions of current user
    :param project: Project in which role will be assigned
    :param current_user: User for whom the form is displayed
    :param allow_delegate: Whether delegate setting should be allowed (bool)
    """

    # Owner cannot be changed in role assignment
    role_excludes = [PROJECT_ROLE_OWNER]

    # Exclude delegate if not allowed or current user lacks perms
    if not allow_delegate or not current_user.has_perm(
        'projectroles.update_project_delegate', obj=project
    ):
        role_excludes.append(PROJECT_ROLE_DELEGATE)

    return [
        (role.pk, role.name)
        for role in Role.objects.exclude(name__in=role_excludes)
    ]


# TODO: TBD: Needed by other apps than projectroles? Move e.g. to utils?
def get_selectable_users(current_user):
    """
    Return selectable users according to current user level: only show
    non-system users for non-superusers
    :param current_user: User object
    :return: QuerySet
    """
    if not current_user.is_superuser:
        return User.objects.exclude(groups__name='system')

    return User.objects.all()
