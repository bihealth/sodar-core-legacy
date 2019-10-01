"""Project and user settings API"""
import json

from projectroles.models import AppSetting, APP_SETTING_TYPES, SODAR_CONSTANTS
from projectroles.plugins import get_app_plugin, get_active_plugins


# SODAR constants
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local constants
VALID_SCOPES = [APP_SETTING_SCOPE_PROJECT, APP_SETTING_SCOPE_USER]


class AppSettingAPI:
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
    def _get_json_value(cls, value):
        """
        Return JSON value as dict regardless of input type

        :param value: Original value (string or dict)
        :raise: json.decoder.JSONDecodeError if string value is not valid JSON
        :raise: ValueError if value type is not recognized
        :return: dict
        """
        if not value:
            return {}

        elif isinstance(value, str):
            return json.loads(value)

        elif isinstance(value, dict):
            return value

        raise ValueError(
            'Invalid type for value: "{}" ({})'.format(value, type(value))
        )

    @classmethod
    def _compare_value(cls, setting_obj, input_value):
        """
        Compare input value to value in an AppSetting object

        :param setting_obj: AppSetting object
        :param input_value: Input value (string, int, bool or dict)
        :return: Bool
        """
        if setting_obj.type == 'JSON':
            return setting_obj.value_json == cls._get_json_value(input_value)

        elif setting_obj.type == 'BOOLEAN':
            # TODO: Also do conversion on input value here if necessary
            return bool(int(setting_obj.value)) == input_value

        return setting_obj.value == str(input_value)

    @classmethod
    def get_default_setting(cls, app_name, setting_name, post_safe=False):
        """
        Get default setting value from an app plugin.

        :param app_name: App name (string, must correspond to "name" in app
                         plugin)
        :param setting_name: Setting name (string)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: Setting value (string, integer or boolean)
        :raise: KeyError if nothing is found with setting_name
        """
        app_plugin = get_app_plugin(app_name)

        if setting_name in app_plugin.app_settings:
            if (
                post_safe
                and app_plugin.app_settings[setting_name]['type'] == 'JSON'
            ):
                return json.dumps(
                    app_plugin.app_settings[setting_name]['default']
                )

            return app_plugin.app_settings[setting_name]['default']

        raise KeyError(
            'Setting "{}" not found in app plugin "{}"'.format(
                setting_name, app_name
            )
        )

    @classmethod
    def get_app_setting(
        cls, app_name, setting_name, project=None, user=None, post_safe=False
    ):
        """
        Return app setting value for a project or an user. If not set, return
        default.

        :param app_name: App name (string, must correspond to "name" in app
                         plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (can be None)
        :param user: User object (can be None)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: String or None
        :raise: KeyError if nothing is found with setting_name
        """
        try:
            val = AppSetting.objects.get_setting_value(
                app_name, setting_name, project=project, user=user
            )

        except AppSetting.DoesNotExist:
            val = cls.get_default_setting(app_name, setting_name, post_safe)

        # Handle post_safe for dict values (JSON)
        if post_safe and isinstance(val, dict):
            return json.dumps(val)

        return val

    @classmethod
    def get_all_settings(cls, project=None, user=None, post_safe=False):
        """
        Return all setting values. If the value is not found, return
        the default.

        :param project: Project object (can be None)
        :param user: User object (can be None)
        :param post_safe: Whether POST safe values should be returned (bool)
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
                ] = cls.get_app_setting(
                    plugin.name, s_key, project, user, post_safe
                )

        return ret

    @classmethod
    def get_all_defaults(cls, scope, post_safe=False):
        """
        Get all default settings for a scope.

        :param scope: Setting scope (PROJECT or USER)
        :param post_safe: Whether POST safe values should be returned (bool)
        :return: Dict
        """
        cls._check_scope(scope)

        ret = {}
        app_plugins = get_active_plugins()

        for plugin in app_plugins:
            p_settings = cls.get_setting_defs(plugin, scope)

            for s_key in p_settings:
                ret[
                    'settings.{}.{}'.format(plugin.name, s_key)
                ] = cls.get_default_setting(plugin.name, s_key, post_safe)

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

            if cls._compare_value(setting, value):
                return False

            if validate:
                cls.validate_setting(setting.type, value)

            if setting.type == 'JSON':
                setting.value_json = cls._get_json_value(value)

            else:
                setting.value = value

            setting.save()
            return True

        except AppSetting.DoesNotExist:
            app_plugin = get_app_plugin(app_name)

            if setting_name not in app_plugin.app_settings:
                raise KeyError(
                    'Setting "{}" not found in app plugin "{}"'.format(
                        setting_name, app_name
                    )
                )

            s_def = app_plugin.app_settings[setting_name]
            s_type = s_def['type']
            s_mod = (
                bool(s_def['user_modifiable'])
                if 'user_modifiable' in s_def
                else True
            )

            if validate:
                cls.validate_setting(s_type, value)

            # TODO: Simplfy by creating with **values instead
            if s_type == 'JSON':
                setting = AppSetting(
                    app_plugin=app_plugin.get_model(),
                    project=project,
                    user=user,
                    name=setting_name,
                    type=s_type,
                    value_json=cls._get_json_value(value),
                    user_modifiable=s_mod,
                )
            else:
                setting = AppSetting(
                    app_plugin=app_plugin.get_model(),
                    project=project,
                    user=user,
                    name=setting_name,
                    type=s_type,
                    value=value,
                    user_modifiable=s_mod,
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

        elif setting_type == 'BOOLEAN':
            if not isinstance(setting_value, bool):
                raise ValueError(
                    'Please enter a valid boolean value ({})'.format(
                        setting_value
                    )
                )

        elif setting_type == 'INTEGER':
            if (
                not isinstance(setting_value, int)
                and not str(setting_value).isdigit()
            ):
                raise ValueError(
                    'Please enter a valid integer value ({})'.format(
                        setting_value
                    )
                )
        elif setting_type == 'JSON':
            try:
                json.dumps(setting_value)
            except TypeError:
                raise ValueError(
                    'Please enter valid JSON ({})'.format(setting_value)
                )
        return True

    @classmethod
    def get_setting_def(cls, name, plugin=None, app_name=None):
        """
        Return definition for a single app setting, either based on an app name
        or the plugin object.

        :param name: Setting name
        :param app_name: Name of the app plugin (string)
        :param name: Plugin object extending ProjectAppPluginPoint
        :return: Dict
        :raise: ValueError if neither app_name or plugin are set or if setting
                is not found in plugin
        """
        if not plugin and not app_name:
            raise ValueError('Plugin and app name both unset')

        elif not plugin:
            plugin = get_app_plugin(app_name)

            if not plugin:
                raise ValueError(
                    'Plugin not found with app name "{}"'.format(app_name)
                )

        if name not in plugin.app_settings:
            raise ValueError(
                'App setting not found in app "{}" with name "{}"'.format(
                    plugin.name, name
                )
            )

        return plugin.app_settings[name]

    # TODO: Refactor to also take app name instead of plugin
    @classmethod
    def get_setting_defs(cls, plugin, scope, user_modifiable=False):
        """
        Return app setting definitions of a specific scope from a plugin.

        :param plugin: project app plugin object extending ProjectAppPluginPoint
        :param scope: PROJECT or USER
        :param user_modifiable: Only return modifiable settings if True
                                (boolean)
        :return: Dict
        :raise: ValueError if scope is invalid
        """
        cls._check_scope(scope)

        return {
            k: v
            for k, v in plugin.app_settings.items()
            if (
                'scope' in v
                and v['scope'] == scope
                and (
                    not user_modifiable
                    or (
                        'user_modifiable' not in v
                        or v['user_modifiable'] is True
                    )
                )
            )
        }
