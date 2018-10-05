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
            'users': {},
            'projects': {}}

        def add_user(user):
            if user.username not in [
                    u['username'] for u in sync_data['users'].values()]:
                sync_data['users'][str(user.sodar_uuid)] = {
                    'username': user.username,
                    'name': user.name,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'groups': [g.name for g in user.groups.all()]}

        def add_parent_categories(category, project_level):
            if category.parent:
                add_parent_categories(category.parent, project_level)

            if str(category.sodar_uuid) not in sync_data['projects'].keys():
                new_cat = {
                    'title': category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'parent_uuid': str(category.parent.sodar_uuid) if
                    category.parent else None,
                    'description': category.description,
                    'readme': category.readme.raw}

                if project_level == REMOTE_LEVEL_READ_ROLES:
                    new_cat['owner'] = category.get_owner().user.username
                    add_user(category.get_owner().user)

                sync_data['projects'][str(category.sodar_uuid)] = new_cat

        for rp in target_site.projects.all():
            project = rp.get_project()
            project_data = {
                'level': rp.level,
                'title': project.title,
                'type': PROJECT_TYPE_PROJECT}

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
                    project_data['parent_uuid'] = str(project.parent.sodar_uuid)

            # If level is READ_ROLES, add categories and roles
            if rp.level in REMOTE_LEVEL_READ_ROLES:
                project_data['roles'] = {}

                for role_as in project.roles.all():
                    project_data['roles'][str(role_as.sodar_uuid)] = {
                        'user': role_as.user.username,
                        'role': role_as.role.name}
                    add_user(role_as.user)

            sync_data['projects'][str(rp.project_uuid)] = project_data
            # TODO: Log with timeline

        return sync_data

    @classmethod
    def sync_source_data(cls, site, remote_data):
        """
        Synchronize remote user and project data into the local Django database
        and return information of additions
        :param site: RemoteSite object for the source site
        :param remote_data: Data returned by get_target_data() in the source
        :return: Dict with updated remote_data or None if nothing was changed
        """

        logger.info(
            'Synchronizing user and project data from "{}"..'.format(site.name))

        # Return None if no projects with READ_ROLES are included
        # TODO: TBD: What if access in source is e.g. removed?
        # TODO: Fix
        '''
        if (not [p for p in remote_data['projects'].values() if
                p['level'] == REMOTE_LEVEL_READ_ROLES]):
            logger.info('No READ_ROLES access set, nothing to synchronize')
            return None
        '''

        def update_obj(obj, data, fields):
            """Update object"""
            for f in [f for f in fields if hasattr(obj, f)]:
                setattr(obj, f, data[f])
            obj.save()
            return obj

        ########
        # Users
        ########

        # NOTE: only sync LDAP/AD users
        for sodar_uuid, u in {
                k: v for k, v in remote_data['users'].items() if
                '@' in v['username']}.items():

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
                    u['status'] = 'updated'
                    logger.info('Updated user: {} ({}): {}'.format(
                        u['username'], sodar_uuid,
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
                u['status'] = 'created'
                logger.info('Created user: {}'.format(user.username))

                for g in u['groups']:
                    group, created = Group.objects.get_or_create(name=g)
                    group.user_set.add(user)
                    logger.debug('Added user {} ({}) to group "{}"'.format(
                        user.username, user.sodar_uuid, g))

        ##########################
        # Categories and Projects
        ##########################

        def update_project(sodar_uuid, p, remote_data):
            """Create or update project and its parents"""

            def handle_project_error(
                    error_msg, sodar_uuid, p, action, remote_data):
                """Add and log project error"""
                logger.error('{} {} "{}" ({}): {}'.format(
                    action.capitalize(), p['type'].lower(), p['title'],
                    sodar_uuid, error_msg))
                remote_data['projects'][sodar_uuid]['status'] = 'error'
                remote_data['projects'][sodar_uuid]['status_msg'] = error_msg
                return remote_data

            if p['parent_uuid']:
                c = remote_data['projects'][p['parent_uuid']]
                remote_data = update_project(
                    p['parent_uuid'], c, remote_data)

            project = None
            parent = None
            action = 'create'

            # Get existing project
            try:
                project = Project.objects.get(
                    type=p['type'], sodar_uuid=sodar_uuid)
                action = 'update'

            except Project.DoesNotExist:
                pass

            # Get parent and ensure it exists
            if p['parent_uuid']:
                try:
                    parent = Project.objects.get(sodar_uuid=p['parent_uuid'])

                except Project.DoesNotExist:
                    # Handle error
                    error_msg = 'Parent {} not found'.format(p['parent_uuid'])
                    remote_data = handle_project_error(
                        error_msg, sodar_uuid, p, action, remote_data)
                    return remote_data

            # Check existing name under the same parent
            try:
                old_project = Project.objects.get(
                    parent=parent, title=p['title'])

                # Handle error
                error_msg = 'A {} with the title "{}" exists under the same ' \
                            'parent, unable to create'.format(
                                old_project.type.lower(), old_project.title)
                remote_data = handle_project_error(
                    error_msg, sodar_uuid, p, action, remote_data)

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

                remote_data['projects'][sodar_uuid]['status'] = 'updated'

                # TODO: Update roles
                # TODO: Update RemoteProject object

            # Create new project
            else:
                create_fields = ['title', 'description', 'readme']
                create_values = {
                    k: v for k, v in p.items() if k in create_fields}
                create_values['type'] = p['type']
                create_values['parent'] = parent
                create_values['sodar_uuid'] = sodar_uuid

                project = Project.objects.create(**create_values)

                logger.info('Created {}: {} ({})'.format(
                    p['type'].lower(), p['title'], sodar_uuid))

                # TODO: Create roles
                # TODO: Create RemoteProject object

                remote_data['projects'][sodar_uuid]['status'] = 'updated'

            return remote_data

        # Update projects
        for sodar_uuid, p in {
                k: v for k, v in remote_data['projects'].items() if
                v['type'] == PROJECT_TYPE_PROJECT and
                v['level'] == REMOTE_LEVEL_READ_ROLES}.items():
            remote_data = update_project(sodar_uuid, p, remote_data)

        logger.info('Synchronization OK')
        return remote_data
