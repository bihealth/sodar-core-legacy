import uuid

from django.conf import settings
from django.db import models

# Projectroles dependency
from projectroles.models import Project

# Access Django user model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# Event status types
EVENT_STATUS_TYPES = ['OK', 'INIT', 'SUBMIT', 'FAILED', 'INFO', 'CANCEL']

DEFAULT_MESSAGES = {
    'OK': 'All OK',
    'INIT': 'Event initialized',
    'SUBMIT': 'Job submitted to Taskflow',
    'FAILED': 'Failed (unknown problem)',
    'INFO': 'Info level action',
    'CANCEL': 'Action cancelled',
}


class ProjectEventManager(models.Manager):
    """Manager for custom table-level ProjectEvent queries"""

    def get_object_events(
        self, project, object_model, object_uuid, order_by='-pk'
    ):
        """
        Return events which are linked to an object reference.

        :param project: Project object or None
        :param object_model: Object model (string)
        :param object_uuid: sodar_uuid of the original object
        :param order_by: Ordering (default = pk descending)
        :return: QuerySet
        """
        return ProjectEvent.objects.filter(
            project=project,
            event_objects__object_model=object_model,
            event_objects__object_uuid=object_uuid,
        ).order_by(order_by)


class ProjectEvent(models.Model):
    """
    Class representing a Project event. Can also be a site-wide event not linked
    to a specific project.
    """

    #: Project to which the event belongs
    project = models.ForeignKey(
        Project,
        related_name='events',
        help_text='Project to which the event belongs (null for no project)',
        on_delete=models.CASCADE,
        null=True,
    )

    #: App from which the event was triggered
    app = models.CharField(
        max_length=255, help_text='App from which the event was triggered'
    )

    #: User who initiated the event (optional)
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        null=True,
        # related_name='events',
        help_text='User who initiated the event (optional)',
        on_delete=models.CASCADE,
    )

    #: Event ID string
    event_name = models.CharField(max_length=255, help_text='Event ID string')

    #: Description of status change (may include {object_name} references)
    description = models.TextField(
        help_text='Description of status change '
        '(may include {object label} references)'
    )

    #: Additional event data as JSON
    extra_data = models.JSONField(
        default=dict, help_text='Additional event data as JSON'
    )

    #: Event is classified (only viewable by user levels specified in rules)
    classified = models.BooleanField(
        default=False,
        help_text='Event is classified (only viewable by user levels '
        'specified in rules)',
    )

    #: UUID for the event
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='Event SODAR UUID'
    )

    # Set manager for custom queries
    objects = ProjectEventManager()

    def __str__(self):
        return '{}{}{}'.format(
            (self.project.title + ': ') if self.project else '',
            self.event_name,
            ('/' + self.user.username) if self.user else '',
        )

    def __repr__(self):
        return 'ProjectEvent({})'.format(
            ', '.join(repr(v) for v in self.get_repr_values())
        )

    def get_repr_values(self):
        return [
            self.project.title if self.project else 'N/A',
            self.event_name,
            self.user.username if self.user else 'N/A',
        ]

    def get_current_status(self):
        """Return the current event status"""
        return self.status_changes.order_by('-timestamp').first()

    def get_timestamp(self):
        """Return the timestamp of current status"""
        return self.status_changes.order_by('-timestamp').first().timestamp

    def get_status_changes(self, reverse=False):
        """Return all status changes for the event"""
        return self.status_changes.order_by(
            '{}pk'.format('-' if reverse else '')
        )

    def add_object(self, obj, label, name, extra_data=None):
        """
        Add object reference to an event.

        :param obj: Django object to which we want to refer
        :param label: Label for the object in the event description (string)
        :param name: Name or title of the object (string)
        :param extra_data: Additional data related to object (dict, optional)
        :return: ProjectEventObjectRef object
        """
        ref = ProjectEventObjectRef()
        ref.event = self
        ref.label = label
        ref.name = name
        ref.object_model = obj.__class__.__name__
        ref.object_uuid = obj.sodar_uuid

        if extra_data:
            ref.extra_data = extra_data

        ref.save()
        return ref

    def set_status(self, status_type, status_desc=None, extra_data=None):
        """
        Set event status.

        :param status_type: Status type string (see EVENT_STATUS_TYPES)
        :param status_desc: Description string (optional)
        :param extra_data: Extra data for the status (dict, optional)
        :return: ProjectEventStatus object
        :raise: TypeError if status_type is invalid
        """
        if status_type not in EVENT_STATUS_TYPES:
            raise TypeError(
                'Invalid status type (accepted values: {})'.format(
                    ', '.join(v for v in EVENT_STATUS_TYPES)
                )
            )

        status = ProjectEventStatus()
        status.event = self
        status.status_type = status_type
        status.description = (
            status_desc if status_desc else DEFAULT_MESSAGES[status_type]
        )
        if extra_data:
            status.extra_data = extra_data
        status.save()
        return status


class ProjectEventObjectRef(models.Model):
    """Class representing a reference to an object (existing or removed)
    related to a Timeline event status"""

    #: Event to which the object belongs
    event = models.ForeignKey(
        ProjectEvent,
        related_name='event_objects',
        help_text='Event to which the object belongs',
        on_delete=models.CASCADE,
    )

    #: Label for the object related to the event
    label = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text='Label for the object related to the event',
    )

    #: Name or title of the object
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text='Name or title of the object',
    )

    #: Object model as string
    object_model = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text='Object model as string',
    )

    #: Object SODAR UUID
    object_uuid = models.UUIDField(
        null=True, blank=True, unique=False, help_text='Object SODAR UUID'
    )

    #: Additional data related to the object as JSON
    extra_data = models.JSONField(
        default=dict, help_text='Additional data related to the object as JSON'
    )

    def __str__(self):
        return '{} ({})'.format(
            self.event.__str__(),
            self.name,
        )

    def __repr__(self):
        values = self.event.get_repr_values() + [self.name]
        return 'ProjectEventObjectRef({})'.format(
            ', '.join(repr(v) for v in values)
        )


class ProjectEventStatus(models.Model):
    """Class representing a Timeline event status"""

    #: Event to which the status change belongs
    event = models.ForeignKey(
        ProjectEvent,
        related_name='status_changes',
        help_text='Event to which the status change belongs',
        on_delete=models.CASCADE,
    )

    #: DateTime of the status change
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text='DateTime of the status change'
    )

    #: Type of the status change
    status_type = models.CharField(
        max_length=64,
        null=False,
        blank=False,
        help_text='Type of the status change',
    )

    #: Description of status change (optional)
    description = models.TextField(
        blank=True, help_text='Description of status change (optional)'
    )

    #: Additional status data as JSON
    extra_data = models.JSONField(
        default=dict, help_text='Additional status data as JSON'
    )

    def __str__(self):
        return '{} ({})'.format(
            self.event.__str__(),
            self.status_type,
        )

    def __repr__(self):
        values = self.event.get_repr_values() + [self.status_type]
        return 'ProjectEventStatus({})'.format(
            ', '.join(repr(v) for v in values)
        )
