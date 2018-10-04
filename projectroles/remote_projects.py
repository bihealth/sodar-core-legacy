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


class RemoteProjectAPI:
    """Remote project data handling API"""

    @classmethod
    def get_target_data(cls, target_site):
        """
        Get user and project data to be synchronized into a target site
        :param target_site: RemoteSite object for the target site
        :return: Dict
        """

        sync_data = {
            'users': [],
            'categories': [],
            'projects': []}

        def add_user(user):
            if user.username not in [u['username'] for u in sync_data['users']]:
                sync_data['users'].append({
                    'sodar_uuid': user.sodar_uuid,
                    'username': user.username,
                    'name': user.name,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'groups': [g.name for g in user.groups.all()]})

        def add_parent_categories(category, project_level):
            if category.parent:
                add_parent_categories(category.parent, project_level)

            if (category.sodar_uuid not in [
                    c['sodar_uuid'] for c in sync_data['categories']]):
                new_cat = {
                    'sodar_uuid': category.sodar_uuid,
                    'title': category.title,
                    'parent': category.parent.sodar_uuid if
                    category.parent else None,
                    'description': category.description,
                    'readme': category.readme.raw}

                if project_level == REMOTE_LEVEL_READ_ROLES:
                    new_cat['owner'] = category.get_owner().user.username
                    add_user(category.get_owner().user)

                sync_data['categories'].append(new_cat)

        for rp in target_site.projects.all():
            project_data = {
                'sodar_uuid': rp.project_uuid,
                'level': rp.level}
            project = rp.get_project()
            project_data['title'] = project.title

            # View available projects
            if rp.level == REMOTE_LEVEL_VIEW_AVAIL:
                project_data['available'] = True if project else False

            # Add info
            elif project and rp.level in [
                    REMOTE_LEVEL_READ_INFO, REMOTE_LEVEL_READ_ROLES]:
                project_data['description'] = project.description
                project_data['readme'] = project.readme.raw

                # Add categories
                if project.parent:
                    add_parent_categories(project.parent, rp.level)
                    project_data['parent'] = project.parent.sodar_uuid

            # If level is READ_ROLES, add categories and roles
            if rp.level in REMOTE_LEVEL_READ_ROLES:
                project_data['roles'] = []

                for role_as in project.roles.all():
                    project_data['roles'].append({
                        'sodar_uuid': role_as.sodar_uuid,
                        'user': role_as.user.username,
                        'role': role_as.role.name})
                    add_user(role_as.user)

            sync_data['projects'].append(project_data)
            # TODO: Log with timeline

        return sync_data

    @classmethod
    def sync_source_data(cls, site, remote_data):
        """
        Synchronize remote user and project data into the local Django database
        and return information of additions
        :param site: RemoteSite object for the source site
        :param remote_data: Data returned by get_target_data() in the source site
        :return: Dict or None if nothing was updated
        """

        logger.info(
            'Synchronizing user and project data from "{}"..'.format(site.name))

        update_data = {
            'users': {'new': [], 'update': []},
            'categories': {'new': [], 'update': []},
            'projects': {'new': [], 'update': []},
            'errors': []}

        def update_obj(obj, data, fields):
            """Update object"""
            for f in [f for f in fields if hasattr(obj, f)]:
                setattr(obj, f, data[f])
            obj.save()
            return obj

        def add_project_error(error_msg, project_data, project_type, action):
            """Add and log project error"""
            update_data['errors'].append({
                'item': project_type.lower(),
                'action': action,
                'name': p['title'],
                'sodar_uuid': p['sodar_uuid'],
                'msg': error_msg})
            logger.error('{} {} "{}" ({}): {}'.format(
                action.capitalize(),
                project_type.lower(),
                project_data['title'],
                project_data['sodar_uuid'],
                error_msg))

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
                    logger.info('Updated user: {} ({}): {}'.format(
                        u['username'], u['sodar_uuid'],
                        ', '.join(updated_fields)))

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
                            logger.debug(
                                'Added user {} ({}) to group "{}"'.format(
                                    user.username, user.sodar_uuid, g))

            # Create new user
            except User.DoesNotExist:
                create_values = {k: v for k, v in u.items() if k != 'groups'}
                user = User.objects.create(**create_values)
                update_data['users']['new'].append(user)
                logger.info('Created user: {}'.format(user.username))

                for g in u['groups']:
                    group, created = Group.objects.get_or_create(name=g)
                    group.user_set.add(user)
                    logger.debug('Added user {} ({}) to group "{}"'.format(
                        user.username, user.sodar_uuid, g))

        # Project updating/creation helper
        def update_project(p, project_type):
            if project_type == PROJECT_TYPE_CATEGORY and p['parent']:
                update_project(p['parent'], project_type)
            project = None
            parent = None
            action = 'create'

            # Get existing project
            try:
                project = Project.objects.get(
                    type=project_type, sodar_uuid=p['sodar_uuid'])
                action = 'update'

            except Project.DoesNotExist:
                pass

            # Get parent and ensure it exists
            if p['parent']:
                try:
                    parent = Project.objects.get(sodar_uuid=p['parent'])

                except Project.DoesNotExist:
                    # Handle error
                    error_msg = 'Parent {} not found'.format(p['parent'])
                    add_project_error(error_msg, p, project_type, action)
                    return

            # Check existing name under the same parent
            try:
                old_project = Project.objects.get(
                    parent=parent, title=p['title'])

                # Handle error
                error_msg = 'A {} with the title "{}" exists under the same ' \
                            'parent, unable to create'.format(
                                old_project.type.lower(), old_project.title)
                add_project_error(error_msg, p, project_type, action)
                return

            except Project.DoesNotExist:
                pass

            # Update project
            if project:
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
            else:
                create_fields = ['title', 'description', 'readme', 'sodar_uuid']
                create_values = {
                    k: v for k, v in p.items() if k in create_fields}
                create_values['type'] = project_type
                create_values['parent'] = parent

                project = Project.objects.create(**create_values)

                update_data['x']['new'].append(project)
                logger.info('Created {}: {} ({})'.format(
                    project_type.lower(), p['title'], p['sodar_uuid']))

                # TODO: If READ_ROLES, create roles
                # TODO: Create RemoteProject object

        # Update categories
        for p in remote_data['categories']:
            update_project(p, PROJECT_TYPE_CATEGORY)

        # Update projects
        for p in [p for p in remote_data['projects'] if p['level'] in [
                REMOTE_LEVEL_READ_INFO, REMOTE_LEVEL_READ_ROLES]]:
            update_project(p, PROJECT_TYPE_PROJECT)

        logger.info('Synchronization OK')

        # TODO: Return None if no updates were found
        return update_data
