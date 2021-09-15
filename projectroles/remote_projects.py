"""Remote project management utilities for the projectroles app"""

import logging
from copy import deepcopy

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone

from djangoplugins.models import Plugin

from projectroles.app_settings import (
    AppSettingAPI,
    APP_SETTING_LOCAL_DEFAULT,
)
from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    RemoteProject,
    RemoteSite,
    SODAR_CONSTANTS,
    AppSetting,
)
from projectroles.plugins import get_backend_api


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
User = auth.get_user_model()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS[
    'SUBMIT_STATUS_PENDING_TASKFLOW'
]
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']

REMOTE_LEVEL_NONE = SODAR_CONSTANTS['REMOTE_LEVEL_NONE']
REMOTE_LEVEL_REVOKED = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']

# Local constants
APP_NAME = 'projectroles'


class RemoteProjectAPI:
    """Remote project data handling API"""

    def __init__(self):
        #: Remote data retrieved from source site
        self.remote_data = None

        #: Remote source site currently being worked with
        self.source_site = None

        #: Timeline API
        self.timeline = get_backend_api('timeline_backend')

        #: User for storing timeline events
        self.tl_user = None

        #: Default owner for projects
        self.default_owner = None

        #: Updated parent projects in current sync operation
        self.updated_parents = []

    # Internal Source Site Functions -------------------------------------------

    @classmethod
    def _add_parent_categories(cls, sync_data, category, project_level):
        """
        Add parent categories of a category to source site sync data.

        :param sync_data: Sync data to be updated (dict)
        :param category: Project object for category
        :param project_level: Access level for project (string)
        :return: Updated sync_data (dict)
        """
        if category.parent:
            sync_data = cls._add_parent_categories(
                sync_data, category.parent, project_level
            )

        # Add if not added yet OR if a READ_ROLES project is encountered
        if (
            str(category.sodar_uuid) not in sync_data['projects'].keys()
            or sync_data['projects'][str(category.sodar_uuid)]['level']
            != REMOTE_LEVEL_READ_ROLES
            and sync_data[project_level] == REMOTE_LEVEL_READ_ROLES
        ):
            cat_data = {
                'title': category.title,
                'type': PROJECT_TYPE_CATEGORY,
                'parent_uuid': str(category.parent.sodar_uuid)
                if category.parent
                else None,
                'description': category.description,
                'readme': category.readme.raw,
            }

            if project_level == REMOTE_LEVEL_READ_ROLES:
                cat_data['roles'] = {}
                cat_data['level'] = REMOTE_LEVEL_READ_ROLES
                for role_as in category.roles.all():
                    cat_data['roles'][str(role_as.sodar_uuid)] = {
                        'user': role_as.user.username,
                        'role': role_as.role.name,
                    }
                    sync_data = cls._add_user(sync_data, role_as.user)
            else:
                cat_data['level'] = REMOTE_LEVEL_READ_INFO

            sync_data['projects'][str(category.sodar_uuid)] = cat_data

        return sync_data

    @classmethod
    def _add_peer_site(cls, sync_data, site):
        """
        Add peer site to source site sync data.

        :param sync_data: Sync data to be updated (dict)
        :param site: RemoteSite object for peer site
        :return: Updated sync_data (dict)
        """
        # Do not add sites twice
        if not sync_data['peer_sites'].get(str(site.sodar_uuid), None):
            sync_data['peer_sites'][str(site.sodar_uuid)] = {
                'name': site.name,
                'url': site.url,
                'description': site.description,
                'user_display': site.user_display,
            }
        return sync_data

    @classmethod
    def _add_user(cls, sync_data, user):
        """
        Add user to source site sync data.

        :param sync_data: Sync data to be updated (dict)
        :param user: SODARUser object
        :return: Updated sync_data (dict)
        """
        if user.username not in [
            u['username'] for u in sync_data['users'].values()
        ]:
            sync_data['users'][str(user.sodar_uuid)] = {
                'username': user.username,
                'name': user.name,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'groups': [g.name for g in user.groups.all()],
            }
        return sync_data

    @classmethod
    def _add_app_setting(cls, sync_data, app_setting, all_defs):
        """
        Add app setting to sync data on source site.

        :param sync_data: Sync data to be updated (dict)
        :param app_setting: AppSetting object
        :param all_defs: All settings defs
        :return: Updated sync_data (dict)
        """
        if app_setting.app_plugin:
            plugin_name = app_setting.app_plugin.name
        else:
            plugin_name = 'projectroles'
        local = (
            all_defs.get(plugin_name, {})
            .get(app_setting.name, {})
            .get('local', APP_SETTING_LOCAL_DEFAULT)
        )
        sync_data['app_settings'][str(app_setting.sodar_uuid)] = {
            'name': app_setting.name,
            'type': app_setting.type,
            'value': app_setting.value,
            'value_json': app_setting.value_json,
            'app_plugin': app_setting.app_plugin.name
            if app_setting.app_plugin
            else None,
            'project_uuid': app_setting.project.sodar_uuid
            if app_setting.project
            else None,
            'user_uuid': app_setting.user.sodar_uuid
            if app_setting.user
            else None,
            'local': local,
        }
        return sync_data

    # Source Site API functions ------------------------------------------------

    def get_source_data(self, target_site):
        """
        Get user and project data on a source site to be synchronized into a
        target site.

        :param target_site: RemoteSite object for target site
        :return: Dict
        """
        sync_data = {
            'users': {},
            'projects': {},
            'peer_sites': {},
            'app_settings': {},
        }
        all_defs = app_settings.get_all_defs()

        for rp in target_site.projects.all():
            project = rp.get_project()
            # All RemoteSites which also host this project with a sufficient
            # access level
            remote_sites = [
                relation.site
                for relation in RemoteProject.objects.filter(
                    project_uuid=project.sodar_uuid
                )
                if relation.level
                in [REMOTE_LEVEL_READ_INFO, REMOTE_LEVEL_READ_ROLES]
                and relation.site != target_site  # Dont add current target site
            ]

            # Get and add app settings for project
            for a in AppSetting.objects.filter(project=project):
                try:
                    sync_data = self._add_app_setting(sync_data, a, all_defs)
                except Exception as ex:
                    logger.error(
                        'Failed to sync app setting "{}.settings.{}" '
                        '(UUID={}): {} '.format(
                            a.app_plugin.name
                            if a.app_plugin
                            else 'projectroles',
                            a.name,
                            a.sodar_uuid,
                            ex,
                        )
                    )

            # RemoteSite data to create objects on target site
            for site in remote_sites:
                sync_data = self._add_peer_site(sync_data, site)

            project_data = {
                'level': rp.level,
                'title': project.title,
                'type': PROJECT_TYPE_PROJECT,
                'remote_sites': [str(site.sodar_uuid) for site in remote_sites],
            }

            # View available projects
            if rp.level == REMOTE_LEVEL_VIEW_AVAIL:
                project_data['available'] = True if project else False

            # Add info
            elif project and rp.level in [
                REMOTE_LEVEL_READ_INFO,
                REMOTE_LEVEL_READ_ROLES,
                REMOTE_LEVEL_REVOKED,
            ]:
                project_data['description'] = project.description
                project_data['readme'] = project.readme.raw
                # Add categories
                if project.parent:
                    sync_data = self._add_parent_categories(
                        sync_data, project.parent, rp.level
                    )
                    project_data['parent_uuid'] = str(project.parent.sodar_uuid)

            # If level is READ_ROLES or REVOKED, add roles
            if rp.level in [REMOTE_LEVEL_READ_ROLES, REMOTE_LEVEL_REVOKED]:
                project_data['roles'] = {}
                for role_as in project.roles.all():
                    # If REVOKED, only sync owner and delegate
                    if (
                        rp.level == REMOTE_LEVEL_READ_ROLES
                        or role_as.role.name
                        in ['project owner', 'project delegate']
                    ):
                        project_data['roles'][str(role_as.sodar_uuid)] = {
                            'user': role_as.user.username,
                            'role': role_as.role.name,
                        }
                        sync_data = self._add_user(sync_data, role_as.user)

            sync_data['projects'][str(rp.project_uuid)] = project_data

        return sync_data

    # Internal Target Site Functions -------------------------------------------

    @staticmethod
    def _update_obj(obj, obj_data, fields):
        """
        Update object for target site sync.

        :param obj: Django database object
        :param obj_data: Object sync data (dict)
        :param fields: Fields to be updated (list)
        :return: Updated object
        """
        for f in [f for f in fields if hasattr(obj, f)]:
            setattr(obj, f, obj_data[f])
        obj.save()
        return obj

    def _check_local_categories(self, uuid):
        """
        Check for local category name conflicts on a target site.

        :param uuid: Category UUID (string)
        :return: True if conflict was found (bool)
        """
        c_data = self.remote_data['projects'][uuid]
        local_cat = (
            Project.objects.filter(
                type=PROJECT_TYPE_CATEGORY, title=c_data['title']
            )
            .exclude(sodar_uuid=uuid)
            .first()
        )
        if local_cat and not local_cat.parent and not c_data['parent_uuid']:
            return True
        elif (
            local_cat
            and local_cat.parent
            and local_cat.parent.title
            == self.remote_data['projects'][c_data['parent_uuid']]['title']
        ):
            return self._check_local_categories(c_data['parent_uuid'])
        return False

    def _sync_user(self, uuid, user_data):
        """
        Synchronize LDAP user on target site.

        :param uuid: User UUID (string)
        :param user_data: User sync data (dict)
        """
        # Update existing user
        try:
            user = User.objects.get(username=user_data['username'])
            updated_fields = []
            for k, v in user_data.items():
                if (
                    k not in ['groups', 'sodar_uuid']
                    and hasattr(user, k)
                    and str(getattr(user, k)) != str(v)
                ):
                    updated_fields.append(k)

            if updated_fields:
                user = self._update_obj(user, user_data, updated_fields)
                user_data['status'] = 'updated'
                logger.info(
                    'Updated user: {} ({}): {}'.format(
                        user_data['username'], uuid, ', '.join(updated_fields)
                    )
                )

            # Check and update groups
            if sorted([g.name for g in user.groups.all()]) != sorted(
                user_data['groups']
            ):
                for g in user.groups.all():
                    if g.name not in user_data['groups']:
                        g.user_set.remove(user)
                        logger.debug(
                            'Removed user {} ({}) from group "{}"'.format(
                                user.username, user.sodar_uuid, g.name
                            )
                        )
                existing_groups = [g.name for g in user.groups.all()]
                for g in user_data['groups']:
                    if g not in existing_groups:
                        group, created = Group.objects.get_or_create(name=g)
                        group.user_set.add(user)
                        logger.debug(
                            'Added user {} ({}) to group "{}"'.format(
                                user.username, user.sodar_uuid, g
                            )
                        )

        # Create new user
        except User.DoesNotExist:
            create_values = {
                k: v for k, v in user_data.items() if k != 'groups'
            }
            user = User.objects.create(**create_values)
            user_data['status'] = 'created'
            logger.info('Created user: {}'.format(user.username))

            for g in user_data['groups']:
                group, created = Group.objects.get_or_create(name=g)
                group.user_set.add(user)
                logger.debug(
                    'Added user {} ({}) to group "{}"'.format(
                        user.username, user.sodar_uuid, g
                    )
                )

    def _handle_user_error(self, error_msg, project, role_uuid):
        """
        Handle user sync error on target site.

        :param error_msg: Error message (string)
        :param project: Project object
        :param role_uuid: UUID of RoleAssignment object (string)
        """
        logger.error(error_msg)
        self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
            role_uuid
        ]['status'] = 'error'
        self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
            role_uuid
        ]['status_msg'] = error_msg

    def _handle_project_error(self, error_msg, uuid, project_data, action):
        """
        Handle project error on target site.

        :param error_msg: Error message (string)
        :param uuid: Project UUID (string)
        :param project_data: Project sync data (string)
        """
        logger.error(
            '{} {} "{}" ({}): {}'.format(
                action.capitalize(),
                project_data['type'].lower(),
                project_data['title'],
                uuid,
                error_msg,
            )
        )
        self.remote_data['projects'][uuid]['status'] = 'error'
        self.remote_data['projects'][uuid]['status_msg'] = error_msg

    def _update_project(self, project, project_data, parent):
        """
        Update an existing project on target site.

        :param project: Project object
        :param project_data: Project sync data (string)
        :param parent: Project object for parent category
        """
        updated_fields = []
        uuid = str(project.sodar_uuid)

        for k, v in project_data.items():
            if (
                k not in ['parent', 'sodar_uuid', 'roles', 'readme']
                and hasattr(project, k)
                and str(getattr(project, k)) != str(v)
            ):
                updated_fields.append(k)

        # README is a special case
        if project.readme.raw != project_data['readme']:
            updated_fields.append('readme')

        if updated_fields or project.parent != parent:
            project = self._update_obj(project, project_data, updated_fields)
            # Manually update parent
            if parent != project.parent:
                project.parent = parent
                project.save()
                updated_fields.append('parent')
            self.remote_data['projects'][uuid]['status'] = 'updated'

            if self.tl_user:  # Timeline
                tl_desc = (
                    'update project from remote site '
                    '"{{{}}}" ({})'.format('site', ', '.join(updated_fields))
                )
                # TODO: Add extra_data
                tl_event = self.timeline.add_event(
                    project=project,
                    app_name=APP_NAME,
                    user=self.tl_user,
                    event_name='remote_project_update',
                    description=tl_desc,
                    status_type='OK',
                )
                tl_event.add_object(
                    self.source_site, 'site', self.source_site.name
                )

            logger.info(
                'Updated {}: {}'.format(
                    project_data['type'].lower(),
                    ', '.join(sorted(updated_fields)),
                )
            )

        else:
            logger.debug('Nothing to update in project details')

    def _create_project(self, uuid, project_data, parent):
        """
        Create a new project on target site.

        :param uuid: Project UUID (string)
        :param project_data: Project sync data (string)
        :param parent: Project object for parent category
        """
        # Check existing title under the same parent
        old_project = Project.objects.filter(
            parent=parent, title=project_data['title']
        ).first()
        if old_project:
            error_msg = (
                '{} with the title "{}" exists under the same '
                'parent, unable to create'.format(
                    old_project.type.capitalize(), old_project.title
                )
            )
            self._handle_project_error(error_msg, uuid, project_data, 'create')
            return

        create_fields = ['title', 'description', 'readme']
        create_values = {
            k: v for k, v in project_data.items() if k in create_fields
        }
        create_values['type'] = project_data['type']
        create_values['parent'] = parent
        create_values['sodar_uuid'] = uuid
        project = Project.objects.create(**create_values)
        self.remote_data['projects'][uuid]['status'] = 'created'

        if self.tl_user:  # Timeline
            tl_event = self.timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=self.tl_user,
                event_name='remote_project_create',
                description='create project from remote site {site}',
                status_type='OK',
            )
            # TODO: Add extra_data
            tl_event.add_object(self.source_site, 'site', self.source_site.name)

        logger.info('Created {}'.format(project_data['type'].lower()))

    def _create_peer_site(self, uuid, site_data):
        """
        Create remote peer site on target site.

        :param uuid: Remote site UUID (string)
        :param site_data: Site sync data (dict)
        """
        create_fields = ['name', 'url', 'description', 'user_display']
        create_values = {
            k: v for k, v in site_data.items() if k in create_fields
        }
        create_values['mode'] = SITE_MODE_PEER
        create_values['sodar_uuid'] = uuid
        create_values['secret'] = None  # Do not share secret of other sites
        RemoteSite.objects.create(**create_values)
        logger.info('Created Peer Site {}'.format(create_values['name']))

    def _update_peer_site(self, uuid, site_data):
        """
        Update remote peer site on target site.

        :param uuid: Remote site UUID (string)
        :param site_data: Site sync data (dict)
        """
        site = RemoteSite.objects.filter(sodar_uuid=uuid).first()
        updated_fields = []
        for k, v in site_data.items():
            if hasattr(site, k) and str(getattr(site, k)) != str(v):
                updated_fields.append(k)
        if updated_fields:
            site = self._update_obj(site, site_data, updated_fields)
            logger.info(
                'Updated Peer Site {}: {}'.format(
                    str(site.name), ', '.join(sorted(updated_fields))
                )
            )
        else:
            logger.debug('Nothing to update for peer site "{}"'.format(uuid))

    def _update_roles(self, project, project_data):
        """
        Create or update project roles on target site.

        :param project: Project object
        :param project_data: Project sync data (string)
        """
        # TODO: Refactor this
        uuid = str(project.sodar_uuid)
        allow_local = getattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS', False)

        for r_uuid, r in {
            k: v for k, v in project_data['roles'].items()
        }.items():
            # Ensure the Role exists
            try:
                role = Role.objects.get(name=r['role'])
            except Role.DoesNotExist:
                error_msg = 'Role object "{}" not found (assignment {})'.format(
                    r['role'], r_uuid
                )
                self._handle_user_error(error_msg, project, r_uuid)
                continue

            # Ensure the user is valid
            if (
                '@' not in r['user']
                and not allow_local
                and r['role'] != PROJECT_ROLE_OWNER
            ):
                error_msg = (
                    'Local user "{}" set for role "{}" but local '
                    'users are not allowed'.format(r['user'], r['role'])
                )
                self._handle_user_error(error_msg, project, r_uuid)
                continue

            # If local user, ensure they exist
            elif (
                '@' not in r['user']
                and allow_local
                and r['role'] != PROJECT_ROLE_OWNER
                and not User.objects.filter(username=r['user']).first()
            ):
                error_msg = (
                    'Local user "{}" not found, role of "{}" will '
                    'not be assigned'.format(r['user'], r['role'])
                )
                self._handle_user_error(error_msg, project, r_uuid)
                continue

            # Use the default owner, if owner role for a non-LDAP user and local
            # users are not allowed
            if (
                r['role'] == PROJECT_ROLE_OWNER
                and (
                    not allow_local
                    or not User.objects.filter(username=r['user']).first()
                )
                and '@' not in r['user']
            ):
                role_user = self.default_owner
                # Notify of assigning role to default owner
                status_msg = (
                    'Non-LDAP/AD user "{}" set as owner, assigning role '
                    'to user "{}"'.format(
                        r['user'], self.default_owner.username
                    )
                )
                self.remote_data['projects'][uuid]['roles'][r_uuid][
                    'user'
                ] = self.default_owner.username
                self.remote_data['projects'][uuid]['roles'][r_uuid][
                    'status_msg'
                ] = status_msg
                logger.info(status_msg)
            else:
                role_user = User.objects.get(username=r['user'])

            # Update RoleAssignment if it exists and is changed
            old_as = RoleAssignment.objects.filter(
                project=project, user=role_user
            ).first()

            # Delete existing owner role
            if r['role'] == PROJECT_ROLE_OWNER:
                old_owner_as = project.get_owner()
                if old_owner_as and old_owner_as.user != role_user:
                    old_owner_as.delete()
                    logger.debug(
                        'Deleted existing owner role from '
                        'user "{}"'.format(old_owner_as.user.username)
                    )

            if old_as and old_as.role != role:
                old_as.role = role
                old_as.user = role_user
                old_as.save()
                self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
                    r_uuid
                ]['status'] = 'updated'

                if self.tl_user:  # Taskflow
                    tl_desc = (
                        'update role to "{}" for {{{}}} from site '
                        '{{{}}}'.format(role.name, 'user', 'site')
                    )
                    tl_event = self.timeline.add_event(
                        project=project,
                        app_name=APP_NAME,
                        user=self.tl_user,
                        event_name='remote_role_update',
                        description=tl_desc,
                        status_type='OK',
                    )
                    tl_event.add_object(role_user, 'user', role_user.username)
                    tl_event.add_object(
                        self.source_site, 'site', self.source_site.name
                    )

                logger.info(
                    'Updated role {}: {} = {}'.format(
                        r_uuid, role_user.username, role.name
                    )
                )

            # Create a new RoleAssignment
            elif not old_as:
                role_values = {
                    'sodar_uuid': r_uuid,
                    'project': project,
                    'role': role,
                    'user': role_user,
                }
                RoleAssignment.objects.create(**role_values)
                self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
                    r_uuid
                ]['status'] = 'created'

                if self.tl_user:  # Taskflow
                    tl_desc = (
                        'add role "{}" for {{{}}} '
                        'from site {{{}}}'.format(role.name, 'user', 'site')
                    )
                    tl_event = self.timeline.add_event(
                        project=project,
                        app_name=APP_NAME,
                        user=self.tl_user,
                        event_name='remote_role_create',
                        description=tl_desc,
                        status_type='OK',
                    )
                    tl_event.add_object(role_user, 'user', role_user.username)
                    tl_event.add_object(
                        self.source_site, 'site', self.source_site.name
                    )

                logger.info(
                    'Created role {}: {} -> {}'.format(
                        r_uuid, role_user.username, role.name
                    )
                )

    def _remove_deleted_roles(self, project, project_data):
        """
        Remove deleted project roles from target site.

        :param project: Project object
        :param project_data: Project sync data (string)
        """
        timeline = get_backend_api('timeline_backend')
        uuid = str(project.sodar_uuid)
        current_users = [v['user'] for k, v in project_data['roles'].items()]
        deleted_roles = (
            RoleAssignment.objects.filter(project=project)
            .exclude(role__name=PROJECT_ROLE_OWNER)
            .exclude(user__username__in=current_users)
        )
        deleted_count = deleted_roles.count()

        if deleted_count > 0:
            deleted_users = sorted([r.user.username for r in deleted_roles])

            for del_as in deleted_roles:
                del_user = del_as.user
                del_role = del_as.role
                del_uuid = str(del_as.sodar_uuid)
                del_as.delete()
                self.remote_data['projects'][uuid]['roles'][del_uuid] = {
                    'user': del_user.username,
                    'role': del_role.name,
                    'status': 'deleted',
                }
                if self.tl_user:  # Timeline
                    tl_desc = (
                        'remove role "{}" from {{{}}} by site '
                        '{{{}}}'.format(del_role.name, 'user', 'site')
                    )
                    tl_event = timeline.add_event(
                        project=project,
                        app_name=APP_NAME,
                        user=self.tl_user,
                        event_name='remote_role_delete',
                        description=tl_desc,
                        status_type='OK',
                    )
                    tl_event.add_object(del_user, 'user', del_user.username)
                    tl_event.add_object(
                        self.source_site, 'site', self.source_site.name
                    )

            logger.info(
                'Deleted {} removed role{} for: {}'.format(
                    deleted_count,
                    's' if deleted_count != 1 else '',
                    ', '.join(deleted_users),
                )
            )

    def _sync_project(self, uuid, project_data):
        """
        Synchronize a single project on target site. Create/update project, its
        parents and user roles.

        :param uuid: Project UUID (string)
        :param project_data: Project sync data (string)
        """
        # Add/update parents if not yet handled
        if (
            project_data['parent_uuid']
            and project_data['parent_uuid'] not in self.updated_parents
        ):
            c_data = self.remote_data['projects'][project_data['parent_uuid']]
            self._sync_project(project_data['parent_uuid'], c_data)
            self.updated_parents.append(project_data['parent_uuid'])

        project = Project.objects.filter(
            type=project_data['type'], sodar_uuid=uuid
        ).first()
        parent = None
        action = 'create' if not project else 'update'
        logger.info(
            'Processing {} "{}" ({})..'.format(
                project_data['type'].lower(), project_data['title'], uuid
            )
        )

        # Get parent and ensure it exists
        if project_data['parent_uuid']:
            try:
                parent = Project.objects.get(
                    sodar_uuid=project_data['parent_uuid']
                )
            except Project.DoesNotExist:
                # Handle error
                error_msg = 'Parent {} not found'.format(
                    project_data['parent_uuid']
                )
                self._handle_project_error(
                    error_msg, uuid, project_data, action
                )
                return

        # Update/create project
        if project:
            self._update_project(project, project_data, parent)
        else:
            self._create_project(uuid, project_data, parent)
            project = Project.objects.filter(
                type=project_data['type'], sodar_uuid=uuid
            ).first()

        # Create/update a RemoteProject object
        try:
            remote_project = RemoteProject.objects.get(
                site=self.source_site, project=project
            )
            remote_project.level = project_data['level']
            remote_project.project = project
            remote_project.date_access = timezone.now()
            remote_project.save()
            remote_action = 'updated'
        except RemoteProject.DoesNotExist:
            remote_project = RemoteProject.objects.create(
                site=self.source_site,
                project_uuid=project.sodar_uuid,
                project=project,
                level=project_data['level'],
                date_access=timezone.now(),
            )
            remote_action = 'created'

        logger.debug(
            '{} RemoteProject {}'.format(
                remote_action.capitalize(), remote_project.sodar_uuid
            )
        )

        # Skip the rest if not updating roles
        if 'level' in project_data and project_data['level'] not in [
            REMOTE_LEVEL_READ_ROLES,
            REMOTE_LEVEL_REVOKED,
        ]:
            return

        # Create/update roles
        # NOTE: Only update AD/LDAP user roles and local owner roles
        if project_data['level'] == REMOTE_LEVEL_READ_ROLES:
            self._update_roles(project, project_data)
        # Remove deleted user roles (also for REVOKED projects)
        self._remove_deleted_roles(project, project_data)

    def _sync_peer_projects(self, uuid, p_data):
        """
        Create RemoteProject objects on target site to represent local project
        on different peer sites.
        """
        if p_data.get('remote_sites', None):
            for remote_site_uuid in p_data['remote_sites']:
                remote_site = RemoteSite.objects.filter(
                    sodar_uuid=remote_site_uuid
                ).first()

                try:
                    remote_project = RemoteProject.objects.get(
                        site=remote_site, project_uuid=uuid
                    )
                    remote_project.level = p_data['level']
                    remote_project.project = Project.objects.filter(
                        sodar_uuid=uuid
                    ).first()
                    remote_project.date_access = (
                        timezone.now()
                    )  # This might not be needed for Peer Projects
                    remote_action = 'updated'
                except RemoteProject.DoesNotExist:
                    remote_project = RemoteProject.objects.create(
                        site=remote_site,
                        project_uuid=uuid,
                        project=Project.objects.filter(sodar_uuid=uuid).first(),
                        level=p_data['level'],
                        date_access=timezone.now(),  # This might not be needed
                    )
                    remote_action = 'created'

            logger.debug(
                '{} Peer project {} for the following peer sites: {}'.format(
                    remote_action.capitalize(),
                    remote_project.sodar_uuid,
                    ', '.join(p_data['remote_sites']),
                )
            )
        else:
            logger.debug(
                '{} is not a peer project (no remote site field)'.format(
                    str(uuid)
                )
            )

    @classmethod
    def _remove_revoked_peers(cls, uuid, project_data):
        """
        Remove RemoteProject objects for revoked peer projects from target site.

        :param uuid: Project UUID (string)
        :param project_data: Project sync data (string)
        """
        removed_sites = []

        if project_data.get('remote_sites', None):
            local_peers = RemoteProject.objects.filter(
                project_uuid=uuid, site__mode=SITE_MODE_PEER
            )
            if not local_peers:
                return
            for rp in local_peers:
                if str(rp.site.sodar_uuid) not in project_data['remote_sites']:
                    removed_sites.append(rp.site.name)
                    rp.delete()

        else:  # If an empty list, remove all
            removed_sites += [
                rp.site.name
                for rp in RemoteProject.objects.filter(
                    project_uuid=uuid, site__mode=SITE_MODE_PEER
                )
            ]
            RemoteProject.objects.filter(
                project_uuid=uuid, site__mode=SITE_MODE_PEER
            ).delete()

        if len(removed_sites) > 0:
            logger.debug(
                'Removed peer project(s) for the following sites: {}'.format(
                    ', '.join(removed_sites)
                )
            )

    @classmethod
    def _sync_app_setting(cls, uuid, set_data):
        """
        Create or update an AppSetting on a target site.

        :param uuid: App setting UUID (string)
        :param set_data: App setting data (dict)
        """
        ad = deepcopy(set_data)
        app_plugin = None
        project = None
        user = None

        # Get app plugin (skip the rest if not found on target server)
        if ad['app_plugin']:
            app_plugin = Plugin.objects.filter(name=ad['app_plugin']).first()
            if not app_plugin:
                logger.debug(
                    'Skipping setting "{}": App plugin not found with name '
                    '"{}"'.format(ad['name'], ad['app_plugin'])
                )
                return

        if ad['project_uuid']:
            project = Project.objects.get(sodar_uuid=ad['project_uuid'])
        if ad['user_uuid']:
            user = User.objects.get(sodar_uuid=ad['user_uuid'])

        try:
            obj = AppSetting.objects.get(
                app_plugin=app_plugin,
                name=ad['name'],
                project=project,
                user=user,
            )
            # Skip if value is identical
            if obj.value == ad['value'] and obj.value_json == ad['value_json']:
                logger.info(
                    'Skipping setting {}: value unchanged'.format(str(obj))
                )
                set_data['status'] = 'skipped'
                return
            # Keep local app setting if available
            if ad.get('local', APP_SETTING_LOCAL_DEFAULT):
                logger.info('Keeping local setting {}'.format(ad['name']))
                return
            # If setting is global, update existing value by recreating object
            action_str = 'updating'
            obj.delete()
        except ObjectDoesNotExist:
            action_str = 'creating'

        # Remove keys that are not available in the model
        ad.pop('local', None)
        ad.pop('project_uuid', None)
        ad.pop('user_uuid', None)
        # Add keys required for the model
        ad['project'] = project
        ad['user'] = user
        ad['sodar_uuid'] = uuid
        if app_plugin:
            ad['app_plugin'] = app_plugin

        # Create new app setting
        obj = AppSetting(**ad)
        logger.info('{} setting {}'.format(action_str.capitalize(), str(obj)))
        obj.save()
        set_data['status'] = action_str.replace('ing', 'ed')

    # Target Site API functions ------------------------------------------------

    @transaction.atomic
    def sync_remote_data(self, site, remote_data, request=None):
        """
        Synchronize remote user and project data into the local Django database
        on a target site and return information of additions.

        :param site: RemoteSite object for the source site
        :param remote_data: Data returned by get_source_data() on the source
                            site (dict)
        :param request: Request object (optional)
        :return: Dict with updated remote_data
        :raise: ValueError if user from PROJECTROLES_DEFAULT_ADMIN is not found
        """
        self.source_site = site
        self.remote_data = remote_data
        self.updated_parents = []

        # Get default owner if remote projects have a local owner
        try:
            self.default_owner = User.objects.get(
                username=settings.PROJECTROLES_DEFAULT_ADMIN
            )
        except User.DoesNotExist:
            error_msg = (
                'Local user "{}" defined in PROJECTROLES_DEFAULT_ADMIN '
                'not found'.format(settings.PROJECTROLES_DEFAULT_ADMIN)
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Check for name conflicts in local categories
        for k, v in self.remote_data['projects'].items():
            if (
                v['type'] == PROJECT_TYPE_PROJECT
                and v['parent_uuid']
                and self._check_local_categories(v['parent_uuid'])
            ):
                error_msg = (
                    'Remote sync cancelled: Existing local category '
                    'structure on target site'
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        # Set up timeline user
        if self.timeline:
            self.tl_user = request.user if request else self.default_owner

        logger.info('Synchronizing data from "{}"..'.format(site.name))

        # Return unchanged data if no projects with READ_ROLES are included
        if not {
            k: v
            for k, v in self.remote_data['projects'].items()
            if v['type'] == PROJECT_TYPE_PROJECT
            and v['level'] in [REMOTE_LEVEL_READ_ROLES, REMOTE_LEVEL_REVOKED]
        }.values():
            logger.info(
                'No READ_ROLES or REVOKED access set, nothing to synchronize'
            )
            return self.remote_data

        ##############
        # Peer Sites
        ##############

        logger.info('Synchronizing Peer Sites...')

        if self.remote_data.get('peer_sites', None):
            for remote_site_uuid, site_data in self.remote_data[
                'peer_sites'
            ].items():
                # Create RemoteSite Objects if not yet there
                remote_site = RemoteSite.objects.filter(
                    sodar_uuid=remote_site_uuid
                ).first()
                if remote_site:
                    self._update_peer_site(remote_site_uuid, site_data)
                else:
                    self._create_peer_site(remote_site_uuid, site_data)
            logger.info('Peer Site Sync OK')
        else:
            logger.info('No new Peer Sites to sync')

        ########
        # Users
        ########

        logger.info('Synchronizing LDAP/AD users..')
        # NOTE: only sync LDAP/AD users
        for u_uuid, u_data in {
            k: v
            for k, v in self.remote_data['users'].items()
            if '@' in v['username']
        }.items():
            self._sync_user(u_uuid, u_data)
        logger.info('User sync OK')

        ##########################
        # Categories and Projects
        ##########################

        # Update projects
        logger.info('Synchronizing projects..')
        for p_uuid, p_data in {
            k: v
            for k, v in self.remote_data['projects'].items()
            if v['type'] == PROJECT_TYPE_PROJECT
            and v['level'] in [REMOTE_LEVEL_READ_ROLES, REMOTE_LEVEL_REVOKED]
        }.items():
            self._sync_project(p_uuid, p_data)
            self._sync_peer_projects(p_uuid, p_data)
            self._remove_revoked_peers(p_uuid, p_data)

        ###############
        # App Settings
        ###############

        logger.info('Synchronizing app settings..')
        for a_uuid, a_data in self.remote_data['app_settings'].items():
            try:
                self._sync_app_setting(a_uuid, a_data)
            except Exception as ex:
                logger.error(
                    'Failed to set app setting "{}.setting.{}" ({}): {}'.format(
                        a_data['app_plugin']
                        if a_data['app_plugin']
                        else 'projectroles',
                        a_data['name'],
                        a_uuid,
                        ex,
                    )
                )
                if settings.DEBUG:
                    raise ex

        logger.info('Synchronization OK')
        return self.remote_data
