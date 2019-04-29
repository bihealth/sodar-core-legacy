from projectroles.models import ProjectSetting
from projectroles.plugins import ProjectAppPluginPoint
from projectroles.project_settings import (
    get_default_setting,
    validate_project_setting,
)

# TODO: streamline with *_project_setting* and deprecate these


def get_user_setting(user, app_name, setting_name):
    """
    Return setting value for a project and an app. If not set, return default.

    :param user: User object.
    :param app_name: App name (string, must correspond to "name" in app plugin)
    :param setting_name: Setting name (string)
    :return: String or None
    :raise: KeyError if nothing is found with setting_name
    """
    try:
        return ProjectSetting.objects.get_setting_value(
            app_name, setting_name, user=user
        )
    except ProjectSetting.DoesNotExist:
        pass
    return get_default_setting(app_name, setting_name)


def validate_user_setting(setting_type, setting_value):
    """
    Validate setting value according to its type.

    :param setting_type: Setting type
    :param setting_value: Setting value
    :raise: ValueError if setting_type or setting_value is invalid
    """
    return validate_project_setting(setting_type, setting_value)


def set_user_setting(user, app_name, setting_name, value, validate=True):
    """
    Set value of an existing usersettings variable. Creates the object if
    not found.

    :param project: Project object
    :param app_name: App name (string, must correspond to "name" in app plugin)
    :param setting_name: Setting name (string)
    :param value: Value to be set
    :param validate: Validate value (bool, default=True)
    :return: True if changed, False if not changed
    :raise: ValueError if validating and value is not accepted for setting type
    :raise: KeyError if setting name is not found in plugin specification
    """
    try:
        setting = ProjectSetting.objects.get(
            user=user, app_plugin__name=app_name, name=setting_name
        )

        if setting.value == value:
            return False

        if validate:
            validate_project_setting(setting.type, value)

        setting.value = value
        setting.save()
        return True

    except ProjectSetting.DoesNotExist:
        app_plugin = ProjectAppPluginPoint.get_plugin(name=app_name)

        if setting_name not in app_plugin.user_settings:
            raise KeyError(
                'Setting "{}" not found in app plugin "{}"'.format(
                    setting_name, app_name
                )
            )

        s_type = app_plugin.user_settings[setting_name]['type']

        if validate:
            validate_user_setting(s_type, value)

        setting = ProjectSetting(
            app_plugin=app_plugin.get_model(),
            user=user,
            name=setting_name,
            type=s_type,
            value=value,
        )
        setting.save()
        return True
