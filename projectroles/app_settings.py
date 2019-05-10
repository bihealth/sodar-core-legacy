"""Project and user settings API"""

from projectroles.models import AppSetting, APP_SETTING_TYPES, SODAR_CONSTANTS
from projectroles.plugins import get_app_plugin, get_active_plugins


# SODAR constants
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local constants
VALID_SCOPES = [APP_SETTING_SCOPE_PROJECT, APP_SETTING_SCOPE_USER]


class AppSettingAPI:
    @classmethod
    def _get_settings_dict(cls, app_plugin):
        """
        TEMPORARY DEPRECATION PROTECTION HELPER, TO BE REMOVED IN THE NEXT
        RELEASE

        :param app_plugin: Project app plugin object
        :return: Dict
        """
        if not app_plugin.app_settings and app_plugin.project_settings:
            return app_plugin.project_settings

        return app_plugin.app_settings

    @classmethod
    def _check_project_and_user(cls, project, user):
        """
        Ensure one of the project and user parameters is set.

        :param project: Project object
        :param user: User object
        :raise: ValueError if none or both objects exist
        """
        if not project and not user:
            raise ValueError('Project and user are both unset')

        if project and user:
            raise ValueError(
                'Scope of project AND user not currently supported'
            )

    @classmethod
    def _check_scope(cls, scope):
        """
        Ensure the validity of a scope definition.

        :param scope: String
        :raise: ValueError if scope is not recognized
        """
        if scope not in VALID_SCOPES:
            raise ValueError('Invalid scope "{}"'.format(scope))

    @classmethod
    def get_default_setting(cls, app_name, setting_name):
        """
        Get default setting value from an app plugin.

        :param app_name: App name (string, must correspond to "name" in app
                         plugin)
        :param setting_name: Setting name (string)
        :return: Setting value (string, integer or boolean)
        :raise: KeyError if nothing is found with setting_name
        """
        app_plugin = get_app_plugin(app_name)

        # NOTE: Deprecation protection, to be removed in the next release
        settings_defs = cls._get_settings_dict(app_plugin)

        if setting_name in settings_defs:
            return settings_defs[setting_name]['default']

        raise KeyError(
            'Setting "{}" not found in app plugin "{}"'.format(
                setting_name, app_name
            )
        )

    @classmethod
    def get_app_setting(cls, app_name, setting_name, project=None, user=None):
        """
        Return app setting value for a project or an user. If not set, return
        default.

        :param app_name: App name (string, must correspond to "name" in app
                         plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (can be None)
        :param user: User object (can be None)
        :return: String or None
        :raise: KeyError if nothing is found with setting_name
        """
        try:
            return AppSetting.objects.get_setting_value(
                app_name, setting_name, project=project, user=user
            )

        except AppSetting.DoesNotExist:
            pass

        return cls.get_default_setting(app_name, setting_name)

    @classmethod
    def get_all_settings(cls, project=None, user=None):
        """
        Return all setting values. If the value is not found, return
        the default.

        :param project: Project object (can be None)
        :param user: User object (can be None)
        :return: Dict
        :raise: ValueError if neither project nor user are set
        """
        cls._check_project_and_user(project, user)

        ret = {}
        app_plugins = get_active_plugins()

        for plugin in app_plugins:
            p_settings = cls.get_setting_defs(plugin, APP_SETTING_SCOPE_PROJECT)

            for s_key in p_settings:
                ret[
                    'settings.{}.{}'.format(plugin.name, s_key)
                ] = cls.get_app_setting(plugin.name, s_key, project, user)

        return ret

    @classmethod
    def get_all_defaults(cls, scope):
        """
        Get all default settings for a scope.

        :param scope:
        :return:
        """
        cls._check_scope(scope)

        ret = {}
        app_plugins = get_active_plugins()

        for plugin in app_plugins:
            p_settings = cls.get_setting_defs(plugin, scope)

            for s_key in p_settings:
                ret[
                    'settings.{}.{}'.format(plugin.name, s_key)
                ] = cls.get_default_setting(plugin.name, s_key)

        return ret

    @classmethod
    def set_app_setting(
        cls,
        app_name,
        setting_name,
        value,
        project=None,
        user=None,
        validate=True,
    ):
        """
        Set value of an existing project or user settings. Creates the object if
        not found.

        :param app_name: App name (string, must correspond to "name" in app
                         plugin)
        :param setting_name: Setting name (string)
        :param value: Value to be set
        :param project: Project object (can be None)
        :param user: User object (can be None)
        :param validate: Validate value (bool, default=True)
        :return: True if changed, False if not changed
        :raise: ValueError if validating and value is not accepted for setting
                type
        :raise: ValueError if neither project nor user are set
        :raise: KeyError if setting name is not found in plugin specification
        """
        cls._check_project_and_user(project, user)

        try:
            setting = AppSetting.objects.get(
                app_plugin__name=app_name,
                name=setting_name,
                project=project,
                user=user,
            )

            if setting.value == value:
                return False

            if validate:
                cls.validate_setting(setting.type, value)

            setting.value = value
            setting.save()
            return True

        except AppSetting.DoesNotExist:
            app_plugin = get_app_plugin(app_name)
            # NOTE: Deprecation protection, to be removed in the next release
            settings_defs = cls._get_settings_dict(app_plugin)

            if setting_name not in settings_defs:
                raise KeyError(
                    'Setting "{}" not found in app plugin "{}"'.format(
                        setting_name, app_name
                    )
                )

            s_type = settings_defs[setting_name]['type']

            if validate:
                cls.validate_setting(s_type, value)

            setting = AppSetting(
                app_plugin=app_plugin.get_model(),
                project=project,
                user=user,
                name=setting_name,
                type=s_type,
                value=value,
            )
            setting.save()
            return True

    @classmethod
    def validate_setting(cls, setting_type, setting_value):
        """
        Validate setting value according to its type.

        :param setting_type: Setting type
        :param setting_value: Setting value
        :raise: ValueError if setting_type or setting_value is invalid
        """
        if setting_type not in APP_SETTING_TYPES:
            raise ValueError('Invalid setting type "{}"'.format(setting_type))

        if setting_type == 'BOOLEAN' and not isinstance(setting_value, bool):
            raise ValueError(
                'Please enter a valid boolean value ({})'.format(setting_value)
            )

        if setting_type == 'INTEGER' and (
            not isinstance(setting_value, int)
            and not str(setting_value).isdigit()
        ):
            raise ValueError(
                'Please enter a valid integer value ({})'.format(setting_value)
            )

        return True

    @classmethod
    def get_setting_defs(cls, plugin, scope):
        """
        Return app setting definitions of a specific scope from a plugin.

        :param plugin: project app plugin object extending ProjectAppPluginPoint
        :param scope: PROJECT or USER
        :return: Dict
        :raise: ValueError if scope is invalid
        """
        cls._check_scope(scope)

        # NOTE: Deprecation protection, to be removed in the next release
        if (
            not plugin.app_settings
            and plugin.project_settings
            and scope == APP_SETTING_SCOPE_PROJECT
        ):
            ret = plugin.project_settings

        elif plugin.app_settings:
            ret = {
                k: v
                for k, v in plugin.app_settings.items()
                if 'scope' in v and v['scope'] == scope
            }

        else:
            ret = {}

        return ret
