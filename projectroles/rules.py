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
    """Whether or not the user has the role of project owner"""
    assignment = RoleAssignment.objects.get_assignment(user, obj)

    if assignment:
        return assignment.role.name == PROJECT_ROLE_OWNER

    return False


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
    """Whether or not the user has the role of project guest"""
    assignment = RoleAssignment.objects.get_assignment(user, obj)

    if assignment:
        return assignment.role.name == PROJECT_ROLE_GUEST

    return False


@rules.predicate
def has_project_role(user, obj):
    """Whether or not the user has any role in the project"""
    return RoleAssignment.objects.get_assignment(user, obj) is not None


@rules.predicate
def has_category_child_role(user, obj):
    """Whether or not the user has any role in any child project under the
    current one, if the current project is a category"""
    return obj.type == PROJECT_TYPE_CATEGORY and obj.has_role(
        user, include_children=True)


@rules.predicate
def has_roles(user):
    """Whether or not the user has any roles set in the system"""
    return RoleAssignment.objects.filter(user=user).count() > 0


@rules.predicate
def is_modifiable_project(user, obj):
    """Whether or not project metadata is modifiable"""
    return False if obj.is_remote() else True


@rules.predicate
def can_create_projects():
    """Whether or not new projects can be generated on the site"""
    if (settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET and
            not settings.PROJECTROLES_TARGET_CREATE):
        return False

    return True

# Combined predicates ----------------------------------------------------------


is_update_user = rules.is_superuser | is_project_owner | is_project_delegate


# Rules ------------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------------


# Allow viewing project/category details
rules.add_perm(
    'projectroles.view_project',
    has_project_role | has_category_child_role)

# Allow project updating
rules.add_perm(
    'projectroles.update_project',
    is_update_user & is_modifiable_project)

# Allow creation of projects
rules.add_perm(
    'projectroles.create_project',
    is_project_owner & can_create_projects)

# Allow updating project settings
rules.add_perm(
    'projectroles.update_project_settings',
    is_update_user & is_modifiable_project)

# Allow viewing project roles
rules.add_perm(
    'projectroles.view_project_roles',
    is_project_owner | is_project_delegate |
    is_project_contributor | is_project_guest)

# Allow updating project owner
rules.add_perm(
    'projectroles.update_project_owner',
    is_project_owner & is_modifiable_project)

# Allow updating project delegate
rules.add_perm(
    'projectroles.update_project_delegate',
    is_project_owner & is_modifiable_project)

# Allow updating project members
rules.add_perm(
    'projectroles.update_project_members',
    is_update_user & is_modifiable_project)

# Allow inviting users to project via email
rules.add_perm(
    'projectroles.invite_users',
    is_update_user & is_modifiable_project)

# Allow importing roles from another project
rules.add_perm(
    'projectroles.import_roles',
    is_project_owner & is_modifiable_project)

# Allow updating remtote sites and remote project access
rules.add_perm(
    'projectroles.update_remote',
    rules.is_superuser)
