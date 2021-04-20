"""Models for the appalerts app"""

import uuid

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from djangoplugins.models import Plugin

# Projectroles dependency
from projectroles.models import Project


# Access Django user model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# Local constants
ALERT_LEVELS = ['INFO', 'SUCCESS', 'WARNING', 'DANGER']
ALERT_LEVEL_CHOICES = [(a, a.capitalize()) for a in ALERT_LEVELS]


class AppAlert(models.Model):
    """Class representing an alert directed to a specific user"""

    #: App to which the alert belongs
    app_plugin = models.ForeignKey(
        Plugin,
        null=True,  # Null for projectroles
        related_name='app_alerts',
        help_text='App to which the alert belongs',
        on_delete=models.CASCADE,
    )

    #: Internal alert name string
    alert_name = models.CharField(
        max_length=255, help_text='Internal alert name string'
    )

    #: User who receives the alert
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        null=False,
        related_name='app_alerts',
        help_text='User who receives the alert',
        on_delete=models.CASCADE,
    )

    #: Alert message (may contain HTML)
    message = models.TextField(help_text='Alert message (may contain HTML)')

    #: Alert level
    level = models.CharField(
        max_length=64,
        blank=False,
        null=False,
        default='INFO',
        choices=ALERT_LEVEL_CHOICES,
        help_text='Alert level',
    )

    #: Active status of the alert
    active = models.BooleanField(
        default=True, help_text='Active status of the alert'
    )

    #: URL for the source of the alert (optional)
    url = models.URLField(
        max_length=2000,
        blank=True,
        null=True,
        help_text='URL for the source of the alert (optional)',
    )

    #: Project to which the alert belongs (optional)
    project = models.ForeignKey(
        Project,
        related_name='app_alerts',
        help_text='Project to which the alert belongs (optional)',
        on_delete=models.CASCADE,
        null=True,
    )

    #: DateTime of the alert creation
    date_created = models.DateTimeField(
        auto_now_add=True, help_text='DateTime of the alert creation'
    )

    #: UUID for the alert
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='Alert SODAR UUID'
    )

    def __str__(self):
        return '{} / {} / {}'.format(
            self.app_plugin.name if self.app_plugin else 'projectroles',
            self.alert_name,
            self.user.username,
        )

    def __repr__(self):
        values = (
            self.app_plugin.name if self.app_plugin else 'projectroles',
            self.alert_name,
            self.user.username,
            self.project.title,
        )
        return 'AppAlert({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Custom validation for AppAlert"""
        self._validate_level()
        super().save(*args, **kwargs)

    def _validate_level(self):
        """Validate level"""
        if self.level not in ALERT_LEVELS:
            raise ValidationError(
                'Invalid level "{}", valid levels: {}'.format(
                    self.level, ', '.join(ALERT_LEVELS)
                )
            )
