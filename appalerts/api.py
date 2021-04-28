"""Backend API for the appalerts app"""

from djangoplugins.models import Plugin

from appalerts.models import AppAlert, ALERT_LEVELS


class AppAlertAPI:
    """App Alerts backend API"""

    @classmethod
    def get_model(cls):
        """
        Return AppAlert model for direct model access.

        :returns: AppAlert class
        """
        return AppAlert

    @classmethod
    def add_alert(
        cls,
        app_name,
        alert_name,
        user,
        message,
        level='INFO',
        url=None,
        project=None,
    ):
        """
        Create an AppAlert.

        :param app_name: Name of app plugin which creates the alert (string)
        :param alert_name: Internal alert name string
        :param user: User object for user receiving the alert
        :param message: Message string (can contain HTML)
        :param level: Alert level string (INFO, SUCCESS, WARNING or DANGER)
        :param url: URL for following up on alert (string, optional)
        :param project: Project the alert belongs to (Project object, optional)
        :raise: ValueError if the plugin is not found or the level is invalid
        :return: AppAlert object
        """
        app_plugin = None  # None = projectroles
        if app_name != 'projectroles':
            try:
                app_plugin = Plugin.objects.get(name=app_name)
            except Plugin.DoesNotExist:
                raise ValueError(
                    'Plugin not found with name: {}'.format(app_name)
                )

        if level not in ALERT_LEVELS:
            raise ValueError(
                'Invalid level "{}", accepted values: {}'.format(
                    level, ', '.join(ALERT_LEVELS)
                )
            )

        return AppAlert.objects.create(
            app_plugin=app_plugin,
            alert_name=alert_name,
            user=user,
            message=message,
            level=level,
            url=url,
            project=project,
        )
