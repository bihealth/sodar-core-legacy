import rules

from django.conf import settings

from projectroles.models import RoleAssignment, SODAR_CONSTANTS

# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']


# Predicates -------------------------------------------------------------------


@rules.predicate
def is_project_owner(user, obj):
    """
    Whether or not the user has the role of project owner, or is the owner of
    a parent category of the current project.
    """
    return obj.is_owner(user) if obj else False


@rules.predicate
def is_project_delegate(user, obj):
    """Whether or not the user has the role of project delegate"""
    assignment = RoleAssignment.objects.get_assignment(user, obj)
    if assignment:
        return assignment.role.name == PROJECT_ROLE_DELEGATE
    return False


@rules.predicate
def is_project_contributor(user, obj):
    """Whether or not the user has the role of project contributor"""
    assignment = RoleAssignment.objects.get_assignment(user, obj)
    if assignment:
        return assignment.role.name == PROJECT_ROLE_CONTRIBUTOR
    return False


@rules.predicate
def is_project_guest(user, obj):
    """
    Whether or not the user has the role of project guest. Also returns true if
    project has public guest access.
    """
    if obj.public_guest_access:
        return True
    assignment = RoleAssignment.objects.get_assignment(user, obj)
    if assignment:
        return assignment.role.name == PROJECT_ROLE_GUEST
    return False


@rules.predicate
def has_project_role(user, obj):
    """
    Whether or not the user has any role in the project. Also returns true if
    project has public guest access.
    """
    if obj.public_guest_access:
        return True
    if user.is_authenticated and obj.has_role(user):
        return True
    return False


@rules.predicate
def has_category_child_role(user, obj):
    """
    Whether or not the user has any role in any child project under the
    current one, if the current project is a category. Also returns true if
    user is anonymous and category includes children with public guest access.
    """
    return obj.type == PROJECT_TYPE_CATEGORY and (
        (user.is_authenticated and obj.has_role(user, include_children=True))
        or (
            user.is_anonymous
            and getattr(settings, 'PROJECTROLES_ALLOW_ANONYMOUS', False)
            and obj.has_public_children
        )
    )


@rules.predicate
def has_roles(user):
    """Whether or not the user has any roles set in the system"""
    return RoleAssignment.objects.filter(user=user).count() > 0


@rules.predicate
def is_modifiable_project(user, obj):
    """Whether or not project metadata is modifiable"""
    return False if obj.is_remote() else True


@rules.predicate
def can_create_projects(user, obj):
    """Whether or not new projects can be generated on the site"""
    if settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET and (
        not settings.PROJECTROLES_TARGET_CREATE or (obj and obj.is_remote())
    ):
        return False
    return True


@rules.predicate
def is_allowed_anonymous(user):
    """Return True if user is anonymous and allowed by site"""
    if (
        not user
        or user.is_anonymous
        and getattr(settings, 'PROJECTROLES_ALLOW_ANONYMOUS', False)
    ):
        return True
    return False


# Combined predicates ----------------------------------------------------------


# Allow creating projects under the current category
is_project_create_user = (
    is_project_owner | is_project_delegate | is_project_contributor
)

# Allow updating project
is_project_update_user = is_project_owner | is_project_delegate

# Allow creating/updating roles
is_role_update_user = is_project_owner | is_project_delegate


# Rules ------------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------------


# Allow viewing project/category details
rules.add_perm(
    'projectroles.view_project', has_project_role | has_category_child_role
)

# Allow project updating
rules.add_perm(
    'projectroles.update_project',
    is_project_update_user,
)

# Allow creation of projects
rules.add_perm(
    'projectroles.create_project', is_project_create_user & can_create_projects
)

# Allow updating project settings
rules.add_perm(
    'projectroles.update_project_settings',
    is_role_update_user & is_modifiable_project,
)

# Allow viewing project roles
rules.add_perm(
    'projectroles.view_project_roles',
    is_project_owner
    | is_project_delegate
    | is_project_contributor
    | is_project_guest,
)

# Allow updating project owner
rules.add_perm(
    'projectroles.update_project_owner',
    is_project_owner & is_modifiable_project,
)

# Allow updating project delegate
rules.add_perm(
    'projectroles.update_project_delegate',
    is_project_owner & is_modifiable_project,
)

# Allow updating project members
rules.add_perm(
    'projectroles.update_project_members',
    is_role_update_user & is_modifiable_project,
)

# Allow inviting users to project via email
rules.add_perm(
    'projectroles.invite_users', is_role_update_user & is_modifiable_project
)

# Allow importing roles from another project
rules.add_perm(
    'projectroles.import_roles', is_project_owner & is_modifiable_project
)

# Allow updating remote sites and remote project access
rules.add_perm('projectroles.update_remote', rules.is_superuser)

# Allow viewing hidden target sites
rules.add_perm(
    'projectroles.view_hidden_projects', rules.is_superuser | is_project_owner
)
