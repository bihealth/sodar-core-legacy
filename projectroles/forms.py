import json

from django import forms
from django.conf import settings
from django.contrib import auth
from django.urls import reverse
from django.utils import timezone

from pagedown.widgets import PagedownWidget
from dal import autocomplete, forward as dal_forward

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
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
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
DELEGATE_LIMIT = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)


User = auth.get_user_model()


# User autocompletion ----------------------------------------------------------


class SODARUserAutocompleteWidget(autocomplete.ModelSelect2):
    """Custom Select widget for user field autocompletion which uses the SODAR
    User class sodar_uuid instead of pk"""

    # Override function to use sodar_uuid instead of pk
    def filter_choices_to_render(self, selected_choices):
        """Filter out un-selected choices if choices is a QuerySet."""
        self.choices.queryset = self.choices.queryset.filter(
            sodar_uuid__in=[c for c in selected_choices if c]
        )


class SODARUserRedirectWidget(SODARUserAutocompleteWidget):
    """Version of SODARUserAutocompleteWidget to allow redirect on selection"""

    autocomplete_function = 'autocomplete_redirect'


# TODO: Refactor into widget?
def get_user_widget(
    scope='all',
    project=None,
    exclude=None,
    forward=None,
    url=None,
    widget_class=None,
):
    """
    Get an user autocomplete widget for your form.

    :param scope: Scope of users to include: "all"/"project"/"project_exclude"
    :param project: Project object or project UUID string (optional)
    :param exclude: List of User objects or User UUIDs to exclude
    :param forward: Parameters to forward to autocomplete view (optional)
    :param url: Autocomplete ajax class override (optional)
    :param widget_class: Widget class override (optional)
    :return: SODARUserAutocompleteWidget or an overridden widget class
    """
    url = url or 'projectroles:autocomplete_user'
    wg = {'url': url, 'forward': [dal_forward.Const(scope, 'scope')]}

    if project:
        p_uuid = (
            str(project.sodar_uuid)
            if isinstance(project, Project)
            else str(project)
        )
        wg['forward'].append(dal_forward.Const(p_uuid, 'project'))

    if forward and isinstance(forward, list):
        wg['forward'] += forward

    if exclude:
        wg['forward'].append(
            dal_forward.Const(
                [
                    str(u.sodar_uuid) if isinstance(u, User) else u
                    for u in exclude
                ],
                'exclude',
            )
        )

    if widget_class:
        return widget_class(**wg)

    return SODARUserAutocompleteWidget(**wg)


class SODARUserChoiceField(forms.ModelChoiceField):
    """User choice field to be used with SODAR User objects and autocomplete"""

    def __init__(
        self,
        scope='all',
        project=None,
        exclude=None,
        forward=None,
        url=None,
        widget_class=None,
        *args,
        **kwargs
    ):
        """
        Override of ModelChoiceField initialization.

        Most arguments given to ModelChoiceField can be set, with the exception
        of queryset, to_field_name, limit_choices_to and widget.

        :param scope: Scope of users to include:
                      "all"/"project"/"project_exclude"
        :param project: Project object or project UUID string (optional)
        :param exclude: List of User objects or User UUIDs to exclude
        :param forward: Parameters to forward to autocomplete view (optional)
        :param url: Autocomplete ajax class override (optional)
        :param widget_class: Widget class override (optional)
        """
        widget = get_user_widget(
            scope, project, exclude, forward, url, widget_class
        )
        super().__init__(
            User.objects.all(),
            to_field_name='sodar_uuid',
            limit_choices_to=None,
            widget=widget,
            *args,
            **kwargs
        )


# Project form -----------------------------------------------------------------


class ProjectForm(forms.ModelForm):
    """Form for Project creation/updating"""

    # Set up owner field
    owner = SODARUserChoiceField(label='Owner', help_text='Owner')

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
                APP_SETTING_SCOPE_PROJECT, plugin=plugin, user_modifiable=True
            )

            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(plugin.name, s_key)
                s_widget_attrs = s_val.get('widget_attrs') or {}
                setting_kwargs = {
                    'required': False,
                    'label': s_val.get('label')
                    or '{}.{}'.format(plugin.name, s_key),
                    'help_text': s_val['description'],
                }

                if s_val['type'] == 'JSON':
                    # NOTE: Attrs MUST be supplied here (#404)
                    if 'class' in s_widget_attrs:
                        s_widget_attrs['class'] += ' sodar-json-input'

                    else:
                        s_widget_attrs['class'] = 'sodar-json-input'

                    self.fields[s_field] = forms.CharField(
                        widget=forms.Textarea(attrs=s_widget_attrs),
                        **setting_kwargs
                    )
                    if self.instance.pk:
                        self.initial[s_field] = json.dumps(
                            self.app_settings.get_app_setting(
                                app_name=plugin.name,
                                setting_name=s_key,
                                project=self.instance,
                            )
                        )

                    else:
                        self.initial[s_field] = json.dumps(
                            self.app_settings.get_default_setting(
                                app_name=plugin.name, setting_name=s_key
                            )
                        )
                else:
                    if s_val['type'] == 'STRING':
                        self.fields[s_field] = forms.CharField(
                            max_length=APP_SETTING_VAL_MAXLENGTH,
                            **setting_kwargs
                        )

                    elif s_val['type'] == 'INTEGER':
                        self.fields[s_field] = forms.IntegerField(
                            **setting_kwargs
                        )

                    elif s_val['type'] == 'BOOLEAN':
                        self.fields[s_field] = forms.BooleanField(
                            **setting_kwargs
                        )

                    # Add optional attributes from plugin (#404)
                    # NOTE: Experimental! Use at your own risk!
                    self.fields[s_field].widget.attrs.update(s_widget_attrs)

                    # Set initial value
                    if self.instance.pk:
                        self.initial[
                            s_field
                        ] = self.app_settings.get_app_setting(
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

            # Set owner value
            self.initial['owner'] = self.instance.get_owner().user.sodar_uuid

            # Hide owner widget if a project (changed in member modification UI)
            if self.initial['type'] == PROJECT_TYPE_PROJECT:
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
                if getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False):
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
                APP_SETTING_SCOPE_PROJECT, plugin=plugin, user_modifiable=True
            )

            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(plugin.name, s_key)

                if s_val['type'] == 'JSON':
                    # for some reason, there is a distinct possiblity, that the
                    # initial value has been discarded and we get '' as value.
                    # Seems to only happen in automated tests. Will catch that
                    # here.
                    if not self.cleaned_data.get(s_field):
                        self.cleaned_data[s_field] = '{}'

                    try:
                        self.cleaned_data[s_field] = json.loads(
                            self.cleaned_data.get(s_field)
                        )

                    except json.JSONDecodeError as err:
                        # TODO: Shouldn't we use add_error() instead?
                        raise forms.ValidationError(
                            'Couldn\'t encode JSON\n' + str(err)
                        )

                if not self.app_settings.validate_setting(
                    setting_type=s_val['type'],
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

        # Modify project field to use sodar_uuid
        self.fields['project'].to_field_name = 'sodar_uuid'

        # Set up user field
        self.fields['user'] = SODARUserChoiceField(
            scope='project_exclude',
            project=self.project,
            forward=['role'],
            url=reverse('projectroles:autocomplete_user_redirect'),
            widget_class=SODARUserRedirectWidget,
        )

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


# Owner transfer form ----------------------------------------------------------


class RoleAssignmentOwnerTransferForm(forms.Form):
    """Form for transferring owner role assignment between users"""

    def __init__(self, project, current_user, current_owner, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)

        # Get current user for checking permissions for form items
        self.current_user = current_user

        # Get the project for which role is being assigned
        self.project = project
        self.current_owner = current_owner

        self.fields['new_owner'] = SODARUserChoiceField(
            label='New owner',
            help_text='Select a member of the project to become owner.',
            scope='project',
            project=self.project,
            exclude=[self.current_owner],
        )

        self.selectable_roles = get_role_choices(
            self.project, self.current_user
        )
        self.fields['ex_owner_role'] = forms.ChoiceField(
            label='New role for {}'.format(self.current_owner.username),
            help_text='New role for the current owner. Select "Remove" in the '
            'member list to remove the user\'s membership.',
            choices=self.selectable_roles,
            initial=Role.objects.get(name=PROJECT_ROLE_CONTRIBUTOR).pk,
        )
        self.fields['project'] = forms.Field(
            widget=forms.HiddenInput(), initial=self.project.sodar_uuid
        )

    def clean_ex_owner_role(self):
        try:
            role = int(self.cleaned_data['ex_owner_role'])

        except ValueError:
            raise forms.ValidationError(
                'Selection couldn\'t be converted to an integer'
            )

        role = next(
            (choice for choice in self.selectable_roles if choice[0] == role),
            None,
        )

        if not role:
            raise forms.ValidationError('Unknown role has been choosen')

        try:
            role = Role.objects.get(name=role[1])

        except Role.DoesNotExist:
            raise forms.ValidationError('Selected role does not exist')

        if role.name == PROJECT_ROLE_DELEGATE:
            # Ensure current user has permission to set delegate
            if not self.current_user.has_perm(
                'projectroles.update_project_delegate', obj=self.project
            ):
                raise forms.ValidationError(
                    'Insufficient permissions for assigning a delegate role'
                )

            # Ensure user can't attempt to add another delegate if limit is
            # reached
            delegates = self.project.get_delegates()

            if DELEGATE_LIMIT != 0:
                if len(delegates) >= DELEGATE_LIMIT:
                    raise forms.ValidationError(
                        'The limit ({}) of delegates for this project has '
                        'already been reached.'.format(DELEGATE_LIMIT)
                    )

        return role

    def clean_new_owner(self):
        user = self.cleaned_data['new_owner']

        if user == self.current_owner:
            raise forms.ValidationError(
                'The new owner shouldn\'t be the current owner'
            )
        ra = RoleAssignment.objects.get_assignment(user, self.project)

        if ra.project != self.project:
            raise forms.ValidationError(
                'The new owner should be from this project'
            )

        return user


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
        fields = ['name', 'url', 'description', 'user_display', 'secret']

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
            self.fields['user_display'].widget = forms.CheckboxInput()
        elif settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET:
            self.fields['user_display'].widget = forms.HiddenInput()

        self.fields['user_display'].initial = True

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


def get_role_choices(
    project, current_user, allow_delegate=True, allow_owner=False
):
    """
    Return valid role choices according to permissions of current user
    :param project: Project in which role will be assigned
    :param current_user: User for whom the form is displayed
    :param allow_delegate: Whether delegate setting should be allowed (bool)
    """

    # Owner cannot be changed in role assignment
    role_excludes = []

    if not allow_owner or not current_user.has_perm(
        'projectroles.update_project_owner', obj=project
    ):
        role_excludes.append(PROJECT_ROLE_OWNER)

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
