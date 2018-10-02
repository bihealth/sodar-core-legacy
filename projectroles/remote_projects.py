"""Remote project management utilities for the projectroles app"""

import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import Group

from projectroles.models import Project, Role, RoleAssignment, SODAR_CONSTANTS


User = auth.get_user_model()
logger = logging.getLogger(__name__)


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_CHOICES = SODAR_CONSTANTS['PROJECT_TYPE_CHOICES']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS[
    'SUBMIT_STATUS_PENDING_TASKFLOW']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
REMOTE_LEVEL_NONE = SODAR_CONSTANTS['REMOTE_LEVEL_NONE']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']


def sync_remote_projects(site, remote_data):
    """Synchronize remote project data retrieved from source system"""

    logger.info(
        'Synchronizing user and project data from source site "{}"..'.format(
            site.name))

    update_data = {
        'users': {'new': [], 'update': []},
        'categories': {'new': [], 'update': []},
        'projects': {'new': [], 'update': []}}

    def update_obj(obj, data, fields):
        """Update object"""
        for f in [f for f in fields if hasattr(obj, f)]:
            setattr(obj, f, data[f])
        obj.save()
        return obj

    # Users (NOTE: only sync LDAP/AD users)
    for u in [u for u in remote_data['users'] if '@' in u['username']]:

        # Update existing user
        try:
            user = User.objects.get(username=u['username'])
            updated_fields = []

            for k, v in u.items():
                if (k != 'groups' and hasattr(user, k) and
                        str(getattr(user, k)) != str(v)):
                    updated_fields.append(k)

            if updated_fields:
                user = update_obj(user, u, updated_fields)
                update_data['users']['update'].append(user)
                logger.debug('Updated user: {} ({}): {}'.format(
                    u['username'], u['sodar_uuid'], ', '.join(updated_fields)))

            # Check and update groups
            if sorted([g.name for g in user.groups.all()]) != \
                    sorted(u['groups']):
                for g in user.groups.all():
                    if g.name not in u['groups']:
                        g.user_set.remove(user)
                        logger.debug(
                            'Removed user {} ({}) from group "{}"'.format(
                                user.username, user.sodar_uuid, g.name))

                existing_groups = [g.name for g in user.groups.all()]

                for g in u['groups']:
                    if g not in existing_groups:
                        group, created = Group.objects.get_or_create(
                            name=g)
                        group.user_set.add(user)
                        logger.debug('Added user {} ({}) to group "{}"'.format(
                            user.username, user.sodar_uuid, g))

        # Create new user
        except User.DoesNotExist:
            create_values = {k: v for k, v in u.items() if k != 'groups'}
            user = User.objects.create(**create_values)
            update_data['users']['new'].append(user)
            logger.debug('Created user: {}'.format(user.username))

            for g in u['groups']:
                group, created = Group.objects.get_or_create(name=g)
                group.user_set.add(user)
                logger.debug('Added user {} ({}) to group "{}"'.format(
                    user.username, user.sodar_uuid, g))

    # Project updating/creation helper
    def update_project(p, project_type):
        if project_type == PROJECT_TYPE_CATEGORY and p['parent']:
            update_project(p['parent'], project_type)

        parent = None

        # Get parent and ensure we are able to create/update this project
        if p['parent']:
            try:
                parent = Project.objects.get(sodar_uuid=p['parent'])

            except Project.DoesNotExist:
                logger.error(
                    'Parent {} not found for project "{}" ({}), '
                    'unable to modify!'.format(
                        p['parent'], p['title'], p['sodar_uuid']))
                return

        # Update project
        try:
            project = Project.objects.get(
                type=project_type, sodar_uuid=p['sodar_uuid'])
            updated_fields = []

            for k, v in u.items():
                if (k != 'parent' and hasattr(project, k) and
                        str(getattr(project, k)) != str(v)):
                    updated_fields.append(k)

            project = update_obj(project, p, updated_fields)

            # Manually update parent
            if parent != project.parent:
                project.parent = parent
                project.save()

            # TODO: If READ_ROLES, update roles
            # TODO: Update RemoteProject object

        # Create new project
        except Project.DoesNotExist:
            # Create project
            create_fields = ['title', 'description', 'readme', 'sodar_uuid']
            create_values = {k: v for k, v in p.items() if k in create_fields}
            create_values['type'] = project_type
            create_values['parent'] = parent

            project = Project.objects.create(**create_values)

            update_data['x']['new'].append(project)
            logger.debug('Created {}: {} ({})'.format(
                project_type.lower(), p['title'], p['sodar_uuid']))

            # TODO: If READ_ROLES, create roles
            # TODO: If the owner is not an LDAP user, set local admin as owner
            # TODO: Create RemoteProject object

    # Update categories
    for p in remote_data['categories']:
        update_project(p, PROJECT_TYPE_CATEGORY)

    # Update projects
    for p in [p for p in remote_data['projects'] if
              p['level'] in [REMOTE_LEVEL_READ_INFO, REMOTE_LEVEL_READ_ROLES]]:
        update_project(p, PROJECT_TYPE_PROJECT)

    logger.info('Synchronization OK')

    # TODO: Return None if no updates were found
    return update_data
